import os
import time
import json
import base64
import html as html_lib
import requests
import datetime
import xml.etree.ElementTree as ET
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote

# ==========================================
# 🔑 공통 API 키 설정
# ==========================================
PUBLIC_DATA_API_KEY = os.environ.get("PUBLIC_DATA_API_KEY", "")
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")

# ==========================================
# 1️⃣ PubMed (글로벌 학술 논문) 수집기
# ==========================================
def collect_pubmed():
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    queries = {
        "백신": "pneumococcal vaccine PCV20 PCV21",
        "영양제": "(folic acid OR iron supplementation) AND pregnancy AND 2026[pdat]",
        "대상포진": "(herpes zoster vaccine OR shingrix OR skyzoster) AND 2026[pdat]",
        "타파미디스": "(tafamidis OR transthyretin amyloidosis OR TTR cardiomyopathy OR cardiac amyloidosis) AND 2026[pdat]",
        "RSV": "(respiratory syncytial virus vaccine OR nirsevimab OR palivizumab OR RSV mRNA vaccine) AND 2026[pdat]"
    }
    all_papers, seen = [], set()

    for cat, q in queries.items():
        try:
            r = requests.get(f"{base_url}/esearch.fcgi",
                params={"db": "pubmed", "term": q, "retmax": 5, "sort": "date",
                        "retmode": "json", "datetype": "pdat", "reldate": 60}, timeout=15)
            ids = r.json().get("esearchresult", {}).get("idlist", [])
            if not ids: continue

            fr = requests.get(f"{base_url}/efetch.fcgi",
                params={"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}, timeout=15)
            time.sleep(0.5)
            xml_text = fr.content.decode("utf-8-sig").strip()
            
            if not xml_text or not xml_text.startswith("<"): 
                continue

            try:
                root = ET.fromstring(xml_text)
            except: 
                continue

            for art in root.findall(".//PubmedArticle"):
                pmid = art.findtext(".//PMID", "")
                if pmid in seen: continue
                seen.add(pmid)
                authors = [f"{a.findtext('LastName', '')} {a.findtext('ForeName', '')}".strip()
                           for a in art.findall(".//Author")[:3]]
                all_papers.append({
                    "category": cat,
                    "title": art.findtext(".//ArticleTitle", ""),
                    "journal": art.findtext(".//Title", ""),
                    "year": art.findtext(".//PubDate/Year", ""),
                    "authors": ", ".join(authors),
                    "pmid": pmid,
                    "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                })
        except: continue
    return all_papers

# ==========================================
# 2️⃣ 네이버 뉴스 수집기
# ==========================================
def collect_naver_news():
    url = "https://openapi.naver.com/v1/search/news.json"
    kw_map = {
        "백신": ["폐렴구균 백신", "캡박시브", "프리베나"],
        "영양제": ["임산부 엽산", "임산부 철분제"],
        "대상포진": ["대상포진 백신", "싱그릭스", "스카이조스터"],
        "타파미디스": ["타파미디스", "심장 아밀로이드증", "빈다맥스"],
        "RSV": ["RSV 백신", "호흡기세포융합바이러스", "니르세비맙", "아브리스보"]
    }
    all_news, seen = [], set()
    headers = {"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
    
    for cat, kws in kw_map.items():
        for kw in kws:
            try:
                resp = requests.get(url, headers=headers, params={"query": kw, "display": 5, "sort": "date"}, timeout=15)
                items = resp.json().get("items", [])
                for i in items:
                    title = i.get("title","").replace("<b>","").replace("</b>","")
                    if title not in seen:
                        seen.add(title)
                        all_news.append({
                            "title": title, "link": i.get("link",""),
                            "pubDate": i.get("pubDate","")[:16], "category": cat
                        })
            except: continue
    return all_news

# ==========================================
# 3️⃣ 나라장터 (G2B) 입찰공고 수집기
# ==========================================
def collect_g2b():
    url = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoThngPPSSrch"
    kw_map = {
        "백신": ["폐렴구균"], "영양제": ["임산부 영양제", "엽산", "철분"],
        "대상포진": ["대상포진", "싱그릭스"],
        "타파미디스": ["타파미디스", "빈다맥스"],
        "RSV": ["RSV", "호흡기세포융합바이러스", "아브리스보"]
    }
    all_items, seen = [], set()
    start = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y%m%d0000")
    end = datetime.datetime.now().strftime("%Y%m%d2359")
    
    for cat, kws in kw_map.items():
        for kw in kws:
            params = {"ServiceKey": PUBLIC_DATA_API_KEY, "inqryDiv": "1", "inqryBgnDt": start, 
                      "inqryEndDt": end, "bidNtceNm": kw, "numOfRows": "20", "type": "xml"}
            try:
                resp = requests.get(url, params=params, timeout=15)
                root = ET.fromstring(resp.text.strip())
                for item in root.findall(".//item"):
                    d = {c.tag: (c.text or "") for c in item}
                    bid_no = d.get("bidNtceNo", "")
                    if bid_no and bid_no not in seen:
                        d['category'] = cat; seen.add(bid_no); all_items.append(d)
            except: continue
    return all_items

# ==========================================
# 4️⃣ 질병관리청 (KDCA) 감염병 통계 수집기
# ==========================================
def collect_kdca():
    url = "https://apis.data.go.kr/1790387/EIDAPIService/Disease"
    def fetch_by_year(year):
        params = {"serviceKey": PUBLIC_DATA_API_KEY, "resType": "2", "searchType": "1", 
                  "searchYear": year, "patntType": "1", "pageNo": 1, "numOfRows": 100}
        try:
            resp = requests.get(url, params=params, timeout=30)
            data = resp.json()
            items = (data.get("body", {}).get("items", {}) or 
                     data.get("response", {}).get("body", {}).get("items", {}) or 
                     data.get("items", {}) or {})
            if isinstance(items, dict): items = items.get("item", []) or []
            if isinstance(items, dict): items = [items]
            return items or []
        except: return []

    current_year = datetime.date.today().strftime("%Y")
    items = fetch_by_year(current_year)
    if not items: items = fetch_by_year(str(int(current_year) - 1))

    res = []
    maternal_kws = ["백일해", "풍진", "매독", "지카"]
    for i in items:
        nm = i.get("icdNm", i.get("diseaseNm", ""))
        if "폐렴구균" in nm: i['category'] = "백신"; res.append(i)
        elif any(kw in nm for kw in maternal_kws): i['category'] = "임산부감염병"; res.append(i)
        elif "대상포진" in nm or "수두" in nm: i['category'] = "대상포진"; res.append(i)
        elif "아밀로이드" in nm: i['category'] = "타파미디스"; res.append(i)
        elif "호흡기세포융합" in nm or "RSV" in nm.upper(): i['category'] = "RSV"; res.append(i)
    return res

# ==========================================
# 5️⃣ 식약처 (MFDS) 국가출하승인 수집기
# ==========================================
def collect_mfds():
    url = "http://apis.data.go.kr/1471000/DrugNatnShipmntAprvInfoService/getDrugNatnShipmntAprvInfoInq"
    targets = {
        "백신": ["폐렴구균", "프리베나", "캡박시브"],
        "임산부": ["아다셀", "부스트릭스", "아브리스보"],
        "대상포진": ["대상포진", "싱그릭스", "스카이조스터"],
        "타파미디스": ["타파미디스", "빈다맥스"],
        "RSV": ["아브리스보", "니르세비맙", "RSV"]
    }
    all_items, seen = [], set()
    for cat, kws in targets.items():
        for kw in kws:
            try:
                r = requests.get(url, params={"serviceKey": PUBLIC_DATA_API_KEY, "pageNo": 1, "numOfRows": 1, "goods_name": kw}, timeout=15)
                root = ET.fromstring(r.text.strip()); tc = int(root.findtext(".//totalCount", "0") or 0)
                if tc == 0: continue
                tp = (tc + 49) // 50
                for page in range(tp, 0, -1):
                    rp = requests.get(url, params={"serviceKey": PUBLIC_DATA_API_KEY, "pageNo": page, "numOfRows": 50, "goods_name": kw}, timeout=15)
                    root_p = ET.fromstring(rp.text.strip())
                    page_recent = False
                    for item in root_p.findall(".//item"):
                        d = {c.tag: (c.text or "") for c in item}
                        if d.get("RESULT_TIME", "")[:4] >= "2025":
                            page_recent = True
                            if d.get("RECEIPT_NO") not in seen:
                                d['category'] = cat; seen.add(d.get("RECEIPT_NO")); all_items.append(d)
                    if not page_recent and page < tp: break
            except: continue
    all_items.sort(key=lambda x: str(x.get("RESULT_TIME", "")), reverse=True)
    return all_items

# ==========================================
# 6️⃣ 심평원 (HIRA) 약가 정보 수집기
# ==========================================
def collect_hira():
    url = "https://apis.data.go.kr/B551182/dgamtCrtrInfoService1.2/getDgamtList"
    kws = {"백신": ["프리베나", "캡박시브"], "영양제": ["폴산", "철분"], "대상포진": ["싱그릭스", "스카이조스터"], "타파미디스": ["타파미디스", "빈다맥스"], "RSV": ["아브리스보", "니르세비맙"]}
    all_items, seen = [], set()
    for cat, words in kws.items():
        for kw in words:
            try:
                params = {"serviceKey": PUBLIC_DATA_API_KEY, "itmNm": kw, "pageNo": 1, "numOfRows": 10}
                r = requests.get(url, params=params, timeout=15); root = ET.fromstring(r.text.strip())
                for item in root.findall(".//item"):
                    d = {c.tag: (c.text or "") for c in item}
                    if d.get("itmCd") not in seen:
                        d['category'] = cat; seen.add(d.get("itmCd")); all_items.append(d)
            except: continue
    return all_items

# ==========================================
# 🎨 UI 생성 도구
# ==========================================
def make_table(items, columns, col_keys):
    display_items = items[:10] # 화면에 보여줄 최대 개수 제한
    if not display_items: return "<p style='color:#7f8c8d; font-size:13px;'>관련 데이터가 없습니다.</p>"
    th_html = "".join([f"<th style='padding:8px; text-align:left; background:#f4f6f7; border-bottom:2px solid #bdc3c7;'>{col}</th>" for col in columns])
    tr_html = ""
    for i in display_items:
        tds = []
        for key in col_keys:
            val = str(i.get(key, ''))
            if key == 'bidNtceUrl' and val: val = f"<a href='{val}' style='color:#3498db; text-decoration:none;'>공고보기</a>"
            elif key == 'link' and val:
                lt = "기사보기" if "naver.com" in val else "PubMed" if "pubmed" in val else "확인하기"
                val = f"<a href='{val}' style='color:#3498db; text-decoration:none;'>{lt}</a>"
            tds.append(f"<td style='padding:8px; border-bottom:1px solid #ecf0f1; font-size:13px;'>{val}</td>")
        tr_html += f"<tr>{''.join(tds)}</tr>"
    return f"<table width='100%' style='border-collapse:collapse;'><thead><tr>{th_html}</tr></thead><tbody>{tr_html}</tbody></table>"

def build_section(title, all_data, columns, col_keys, icon, color):
    v_data = [i for i in all_data if i.get('category') == '백신']
    z_data = [i for i in all_data if i.get('category') == '대상포진']
    n_data = [i for i in all_data if i.get('category') in ['영양제', '임산부', '임산부감염병']]
    t_data = [i for i in all_data if i.get('category') == '타파미디스']
    r_data = [i for i in all_data if i.get('category') == 'RSV']

    n_title = "🤰 임산부 백신 섹션" if "식약처" in title else "🤰 임산부 영양제 및 관련 섹션"

    html = f"""
    <div style='margin-bottom:30px; border:1px solid #dcdde1; border-radius:8px; overflow:hidden; background:#ffffff;'>
        <div style='background:{color}; color:#ffffff; padding:12px 15px; font-size:16px; font-weight:bold;'>{icon} {title}</div>
        <div style='padding:15px;'>
            <h4 style='margin:0 0 10px 0; color:#2c3e50; border-left:4px solid {color}; padding-left:8px;'>💉 백신 섹션</h4>
            {make_table(v_data, columns, col_keys)}
            <h4 style='margin:25px 0 10px 0; color:#8e44ad; border-left:4px solid #8e44ad; padding-left:8px;'>🦠 대상포진 (싱그릭스 등) 섹션</h4>
            {make_table(z_data, columns, col_keys)}
            <h4 style='margin:25px 0 10px 0; color:#27ae60; border-left:4px solid #27ae60; padding-left:8px;'>{n_title}</h4>
            {make_table(n_data, columns, col_keys)}
            <h4 style='margin:25px 0 10px 0; color:#c0392b; border-left:4px solid #c0392b; padding-left:8px;'>💊 타파미디스 (Tafamidis / TTR 심장 아밀로이드) 섹션</h4>
            {make_table(t_data, columns, col_keys)}
            <h4 style='margin:25px 0 10px 0; color:#e67e22; border-left:4px solid #e67e22; padding-left:8px;'>🫁 RSV (호흡기세포융합바이러스) 섹션</h4>
            {make_table(r_data, columns, col_keys)}
        </div>
    </div>"""
    return html

# ✅ 질병청 섹션: 요청하신 이미지 스타일로 수정됨 (다른 로직은 유지)
def build_kdca_section(title, all_data, icon, color):
    v_data = [i for i in all_data if i.get('category') == '백신']
    z_data = [i for i in all_data if i.get('category') == '대상포진']
    m_data = [i for i in all_data if i.get('category') == '임산부감염병']
    t_data = [i for i in all_data if i.get('category') == '타파미디스']
    r_data = [i for i in all_data if i.get('category') == 'RSV']

    def ct(items): return sum(int(i.get("resultVal", i.get("patntCnt", "0")) or 0) for i in items if str(i.get("resultVal", i.get("patntCnt", ""))).isdigit())
    v_t, z_t, m_t, t_t, r_t = ct(v_data), ct(z_data), ct(m_data), ct(t_data), ct(r_data)

    def mc(items):
        if not items: return "<p style='color:#7f8c8d; font-size:13px;'>집계된 데이터가 없습니다.</p>"
        cards = ""
        for i in items:
            ds = i.get("icdNm", i.get("diseaseNm", ""))
            group = i.get("icdGroupNm", "")
            cnt = i.get("resultVal", i.get("patntCnt", ""))
            url = "https://dportal.kdca.go.kr/pot/is/inftnsdsEDW.do"
            # 첫 번째 파일(daily) 및 이미지의 붉은색 카드 UI 적용
            cards += f"""
            <div style='display:inline-block;background:#fff5f5;border:1px solid #fcc;
                        border-left:4px solid #e74c3c;border-radius:6px;padding:12px 16px;
                        margin:4px 8px 8px 0;min-width:200px;vertical-align:top;'>
              <div style='font-size:15px;font-weight:bold;color:#c0392b;'>{ds}</div>
              <div style='font-size:12px;color:#888;margin:4px 0;'>{group} &nbsp;|&nbsp; 누계</div>
              <div style='font-size:22px;font-weight:bold;color:#e74c3c;'>{cnt}<span style='font-size:13px;color:#888;'>건</span></div>
              <div style='margin-top:6px;'>
                <a href='{url}' style='font-size:11px;color:#1a73e8;text-decoration:none;'>질병관리청 상세보기 -&gt;</a>
              </div>
            </div>"""
        return f"<div style='padding:4px;'>{cards}</div>"

    return f"""
    <div style='margin-bottom:30px; border:1px solid #dcdde1; border-radius:8px; overflow:hidden; background:#ffffff;'>
        <div style='background:{color}; color:#ffffff; padding:12px 15px; font-size:16px; font-weight:bold;'>{icon} {title} <span style='float:right; background:rgba(255,255,255,0.3); padding:2px 10px; border-radius:12px; font-size:13px;'>{v_t+z_t+m_t+t_t+r_t}건</span></div>
        <div style='padding:15px;'>
            <h4 style='margin:0 0 10px 0; color:#2c3e50; border-left:4px solid {color}; padding-left:8px;'>🦠 폐렴구균 통계 (총 {v_t}건)</h4> {mc(v_data)}
            <h4 style='margin:25px 0 10px 0; color:#8e44ad; border-left:4px solid #8e44ad; padding-left:8px;'>🦠 대상포진 관련 통계 (총 {z_t}건)</h4> {mc(z_data)}
            <h4 style='margin:25px 0 10px 0; color:#27ae60; border-left:4px solid #27ae60; padding-left:8px;'>🤰 임산부 주의 감염병 통계 (총 {m_t}건)</h4> {mc(m_data)}
            <h4 style='margin:25px 0 10px 0; color:#c0392b; border-left:4px solid #c0392b; padding-left:8px;'>💊 타파미디스 관련 통계 (총 {t_t}건)</h4> {mc(t_data)}
            <h4 style='margin:25px 0 10px 0; color:#e67e22; border-left:4px solid #e67e22; padding-left:8px;'>🫁 RSV 관련 통계 (총 {r_t}건)</h4> {mc(r_data)}
            <p style='color:#aaa;font-size:11px;margin-top:12px;border-top:1px solid #eee;padding-top:8px;'>※ 출처: 질병관리청 감염병포털</p>
        </div>
    </div>"""

# ==========================================
# 📝 Vault 직접 커밋
# ==========================================
def _clean(text: str) -> str:
    """HTML 엔티티 제거 및 특수문자 정리."""
    return html_lib.unescape(str(text)).strip()


def build_markdown_report(data: dict, today: str) -> str:
    # 1. KST Time and ISO formatted datetime
    KST = datetime.timezone(datetime.timedelta(hours=9))
    now_kst = datetime.datetime.now(KST)
    date_iso = now_kst.isoformat()
    
    # 2. Setup from / to email addresses for YAML frontmatter
    from_addr = os.environ.get("NAVER_ADDRESS", "parkbs669@naver.com")
    recipients_str = os.environ.get("REPORT_RECIPIENTS", from_addr)
    recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]
    if not recipients:
        recipients = [from_addr]
    
    # Ensure email-to-vault-ssmyy88w0s@wshu.net is in the 'to' list for frontmatter to match format
    frontmatter_recipients = recipients.copy()
    if "email-to-vault-ssmyy88w0s@wshu.net" not in frontmatter_recipients:
        frontmatter_recipients.append("email-to-vault-ssmyy88w0s@wshu.net")
    to_addr = ", ".join(frontmatter_recipients)
    
    # 3. YAML Frontmatter
    lines = [
        "---",
        f'from: "{from_addr}"',
        f'to: "{to_addr}"',
        'cc: ""',
        f'subject: "📊 [통합 브리핑] 데일리 리포트 - {today}"',
        f'date: {date_iso}',
        "---",
        "",
        "# 📊 [통합 브리핑] 데일리 리포트",
        "",
        "> [!NOTE] 보고서 개요",
        f"> {today} 기준 자동화 리포트입니다. (마크다운 표 형식으로 구조화되었습니다)",
        ""
    ]
    
    # 카테고리 이름 매핑
    cat_names_default = {
        "백신": "💉 백신 섹션",
        "대상포진": "🦠 대상포진 (싱그릭스 등) 섹션",
        "영양제": "🤰 임산부 영양제 및 관련 섹션",
        "타파미디스": "💊 타파미디스 (Tafamidis / TTR 심장 아밀로이드) 섹션",
        "RSV": "🫁 RSV (호흡기세포융합바이러스) 섹션"
    }

    cat_names_mfds = {
        "백신": "💉 백신 섹션",
        "대상포진": "🦠 대상포진 (싱그릭스 등) 섹션",
        "임산부": "🤰 임산부 백신 섹션",
        "타파미디스": "💊 타파미디스 (Tafamidis / TTR 심장 아밀로이드) 섹션",
        "RSV": "🫁 RSV (호흡기세포융합바이러스) 섹션"
    }

    # 1. 네이버 최신 뉴스
    lines.append("## 📰 네이버 최신 뉴스")
    news_by_cat = {}
    for item in data["NEWS"][:30]:
        cat = item.get("category", "기타")
        news_by_cat.setdefault(cat, []).append(item)
        
    for cat in ["백신", "대상포진", "영양제", "타파미디스", "RSV"]:
        items = news_by_cat.get(cat, [])
        sec_title = cat_names_default[cat]
        lines.append(f"\n### {sec_title}")
        if items:
            lines.append("| 제목 | 날짜 | 링크 |")
            lines.append("| :--- | :--- | :--- |")
            for item in items[:10]:
                title = _clean(item['title'])
                date  = item.get('pubDate', '')[:16]
                link  = item.get('link', '')
                link_text = "기사보기" if "naver.com" in link else "확인하기"
                lines.append(f"| {title} | {date} | [{link_text}]({link}) |")
        else:
            lines.append("> 관련 데이터가 없습니다.")

    # 2. 나라장터 입찰공고
    lines.append("\n---\n\n## 🏛️ 나라장터 입찰공고")
    g2b_by_cat = {}
    for item in data["G2B"]:
        cat = item.get("category", "기타")
        g2b_by_cat.setdefault(cat, []).append(item)

    for cat in ["백신", "대상포진", "영양제", "타파미디스", "RSV"]:
        items = g2b_by_cat.get(cat, [])
        sec_title = cat_names_default[cat]
        lines.append(f"\n### {sec_title}")
        if items:
            lines.append("| 공고명 | 기관명 | 공고일 | 링크 |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for item in items[:10]:
                name = _clean(item.get('bidNtceNm', ''))
                org  = _clean(item.get('ntceInsttNm', ''))
                date = item.get('bidNtceDt', '')
                url  = item.get('bidNtceUrl', '')
                link_part = f"[공고보기]({url})" if url else "-"
                lines.append(f"| {name} | {org} | {date} | {link_part} |")
        else:
            lines.append("> 관련 데이터가 없습니다.")

    # 3. 학술 논문 (PubMed)
    lines.append("\n---\n\n## 🔬 학술 논문 (PubMed)")
    pubmed_by_cat = {}
    for item in data["PUBMED"]:
        cat = item.get("category", "기타")
        pubmed_by_cat.setdefault(cat, []).append(item)

    for cat in ["백신", "대상포진", "영양제", "타파미디스", "RSV"]:
        items = pubmed_by_cat.get(cat, [])
        sec_title = cat_names_default[cat]
        lines.append(f"\n### {sec_title}")
        if items:
            lines.append("| 제목 | 저널 | 연도 | 링크 |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for item in items[:8]:
                title   = _clean(item.get('title', ''))
                journal = _clean(item.get('journal', ''))
                year    = item.get('year', '')
                link    = item.get('link', '')
                lines.append(f"| {title} | {journal} | {year} | [PubMed]({link}) |")
        else:
            lines.append("> 관련 데이터가 없습니다.")

    # 4. 질병관리청 감염병 현황
    lines.append("\n---\n\n## 🏥 질병관리청 감염병 현황")
    kdca_by_cat = {}
    for item in data["KDCA"]:
        cat = item.get("category", "기타")
        kdca_by_cat.setdefault(cat, []).append(item)

    v_data = kdca_by_cat.get("백신", [])
    z_data = kdca_by_cat.get("대상포진", [])
    m_data = kdca_by_cat.get("임산부감염병", [])
    t_data = kdca_by_cat.get("타파미디스", [])

    def ct(items):
        return sum(int(i.get("resultVal", i.get("patntCnt", "0")) or 0) 
                   for i in items if str(i.get("resultVal", i.get("patntCnt", ""))).isdigit())

    v_t, z_t, m_t, t_t = ct(v_data), ct(z_data), ct(m_data), ct(t_data)

    r_data_md = kdca_by_cat.get("RSV", [])
    r_t = ct(r_data_md)
    kdca_cats = [
        ("백신", v_data, f"🦠 폐렴구균 통계 (총 {v_t}건)"),
        ("대상포진", z_data, f"🦠 대상포진 관련 통계 (총 {z_t}건)"),
        ("임산부감염병", m_data, f"🤰 임산부 주의 감염병 통계 (총 {m_t}건)"),
        ("타파미디스", t_data, f"💊 타파미디스 관련 통계 (총 {t_t}건)"),
        ("RSV", r_data_md, f"🫁 RSV 관련 통계 (총 {r_t}건)")
    ]

    for cat_id, items, sec_title in kdca_cats:
        # 5월 27일자 파일과 동일하게 데이터가 없는 KDCA 섹션은 건너뜀
        if not items:
            continue
        lines.append(f"\n### {sec_title}")
        lines.append("| 질병명 | 등급 | 누계 | 링크 |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for item in items[:8]:
            nm  = _clean(item.get("icdNm", item.get("diseaseNm", "")))
            grp = _clean(item.get("icdGroupNm", ""))
            cnt = item.get("resultVal", item.get("patntCnt", ""))
            url = "https://dportal.kdca.go.kr/pot/is/inftnsdsEDW.do"
            lines.append(f"| {nm} | {grp} | {cnt}건 | [질병관리청 상세보기]({url}) |")

    lines.append("\n*(※ 출처: 질병관리청 감염병포털)*")

    # 5. 식약처 국가출하승인
    lines.append("\n---\n\n## 💊 식약처 국가출하승인")
    mfds_by_cat = {}
    for item in data["MFDS"]:
        cat = item.get("category", "기타")
        mfds_by_cat.setdefault(cat, []).append(item)

    for cat in ["백신", "대상포진", "임산부", "타파미디스", "RSV"]:
        items = mfds_by_cat.get(cat, [])
        sec_title = cat_names_mfds[cat]
        lines.append(f"\n### {sec_title}")
        if items:
            lines.append("| 제품명 | 제조사 | 승인일 |")
            lines.append("| :--- | :--- | :--- |")
            for item in items[:8]:
                name = _clean(item.get('SAMPLE_TYPE', ''))
                mfr  = _clean(item.get('MANUF_ENTP_NAME', ''))
                date = item.get('RESULT_TIME', '')[:10]
                lines.append(f"| {name} | {mfr} | {date} |")
        else:
            lines.append("> 관련 데이터가 없습니다.")

    # 6. 심평원 약가 정보
    lines.append("\n---\n\n## 💰 심평원 약가 정보")
    hira_by_cat = {}
    for item in data["HIRA"]:
        cat = item.get("category", "기타")
        hira_by_cat.setdefault(cat, []).append(item)

    for cat in ["백신", "대상포진", "영양제", "타파미디스", "RSV"]:
        items = hira_by_cat.get(cat, [])
        sec_title = cat_names_default[cat]
        lines.append(f"\n### {sec_title}")
        if items:
            lines.append("| 제품명 | 제약사 | 상한금액 |")
            lines.append("| :--- | :--- | :--- |")
            for item in items[:8]:
                name  = _clean(item.get('itmNm', ''))
                co    = _clean(item.get('entrpsNm', ''))
                price = item.get('mxDpc', '')
                price_str = f"{price}원" if price else "-"
                lines.append(f"| {name} | {co} | {price_str} |")
        else:
            lines.append("> 관련 데이터가 없습니다.")

    return "\n".join(lines)



def commit_to_vault(markdown: str, date_str: str, gh_pat: str):
    owner, repo = "parkbs669-hub", "MyVault_Roger"
    path = f"Emails/{date_str}_통합브리핑.md"
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{quote(path)}"
    headers = {
        "Authorization": f"token {gh_pat}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }

    sha = None
    try:
        r = requests.get(api_url, headers=headers, timeout=15)
        if r.status_code == 200:
            sha = r.json().get("sha")
    except Exception:
        pass

    body = {
        "message": f"chore: 통합브리핑 자동 저장 {date_str}",
        "content": base64.b64encode(markdown.encode("utf-8")).decode("ascii"),
    }
    if sha:
        body["sha"] = sha

    try:
        r = requests.put(api_url, headers=headers, data=json.dumps(body), timeout=30)
        if r.status_code in (200, 201):
            print(f"✅ vault 커밋 완료: {path}")
        else:
            print(f"⚠️  vault 커밋 실패 ({r.status_code}): {r.text[:200]}")
    except Exception as e:
        print(f"⚠️  vault 커밋 오류: {e}")


# ==========================================
# 🚀 메인 실행부
# ==========================================
def main():
    KST = datetime.timezone(datetime.timedelta(hours=9))
    today_kst = datetime.datetime.now(KST).date()
    today = today_kst.strftime("%Y년 %m월 %d일")
    print(f"🚀 {today} 데이터 수집 시작")
    
    addr, pw = os.environ.get("NAVER_ADDRESS"), os.environ.get("NAVER_PASSWORD")
    if not addr or not pw: 
        print("❌ 중단: 이메일 계정 정보가 없습니다.")
        return

    data = {
        "G2B": collect_g2b(), 
        "NEWS": collect_naver_news(), 
        "PUBMED": collect_pubmed(), 
        "KDCA": collect_kdca(), 
        "MFDS": collect_mfds(), 
        "HIRA": collect_hira()
    }
    
    html_body = f"""<html><body style='font-family:"Malgun Gothic", sans-serif; padding:20px; background:#f0f2f5;'>
        <div style='max-width:800px; margin:0 auto;'>
            <div style='text-align:center; margin-bottom:30px;'><h1 style='color:#2c3e50;'>📊 [통합 브리핑] 데일리 리포트</h1><p style='color:#7f8c8d;'>{today} 기준 자동화 리포트</p></div>
            {build_section("네이버 최신 뉴스", data['NEWS'], ['제목', '날짜', '링크'], ['title', 'pubDate', 'link'], "📰", "#3498db")}
            {build_section("나라장터 입찰공고", data['G2B'], ['공고명', '기관명', '공고일', '링크'], ['bidNtceNm', 'ntceInsttNm', 'bidNtceDt', 'bidNtceUrl'], "🏛️", "#e67e22")}
            {build_section("학술 논문 (PubMed)", data['PUBMED'], ['제목', '저널', '연도', '링크'], ['title', 'journal', 'year', 'link'], "🔬", "#9b59b6")}
            {build_kdca_section("질병관리청 감염병 현황", data['KDCA'], "🏥", "#e74c3c")}
            {build_section("식약처 국가출하승인", data['MFDS'], ['제품명', '제조사', '승인일'], ['SAMPLE_TYPE', 'MANUF_ENTP_NAME', 'RESULT_TIME'], "💊", "#1abc9c")}
            {build_section("심평원 약가 정보", data['HIRA'], ['제품명', '제약사', '상한금액'], ['itmNm', 'entrpsNm', 'mxDpc'], "💰", "#f1c40f")}
        </div></body></html>"""

    # 📧 수신자 리스트 설정 (GitHub Secrets에서 쉼표로 구분)
    recipients_str = os.environ.get("REPORT_RECIPIENTS", addr)
    recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]
    if not recipients:
        recipients = [addr]
    
    msg = MIMEMultipart('alternative')
    msg["Subject"] = f"📊 [통합 브리핑]  데일리 리포트 - {today}"
    msg["From"] = addr
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    
    try:
        with smtplib.SMTP_SSL("smtp.naver.com", 465) as s:
            s.login(addr, pw)
            s.send_message(msg)
        print(f"✅ 브리핑 이메일 발송 완료! (수신자: {', '.join(recipients)})")
    except Exception as e:
        print(f"❌ 이메일 발송 오류: {e}")

    # MyVault_Roger에 직접 커밋 (email-to-vault 의존성 제거)
    gh_pat = os.environ.get("GH_PAT", "")
    if gh_pat:
        date_str = today_kst.strftime("%Y-%m-%d")
        markdown = build_markdown_report(data, today)
        commit_to_vault(markdown, date_str, gh_pat)
    else:
        print("⚠️  GH_PAT 없음 — vault 직접 커밋 건너뜀")

if __name__ == "__main__":
    main()
