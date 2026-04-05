import os
import time
import requests
import datetime
import xml.etree.ElementTree as ET
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
        "대상포진": "(herpes zoster vaccine OR shingrix OR skyzoster) AND 2026[pdat]"
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
            if not xml_text or not xml_text.startswith("<"): continue

            try:
                root = ET.fromstring(xml_text)
            except: continue

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
# 2️⃣ 네이버 뉴스 수집기 - 대상포진 누락 방지 (Slice 제거)
# ==========================================
def collect_naver_news():
    url = "https://openapi.naver.com/v1/search/news.json"
    kw_map = {
        "백신": ["폐렴구균 백신", "캡박시브", "프리베나"],
        "영양제": ["임산부 엽산", "임산부 철분제"],
        "대상포진": ["대상포진 백신", "싱그릭스", "스카이조스터"]
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
    return all_news # 👈 수집된 모든 뉴스 반환 (나중에 표에서 개수 제한)

# ==========================================
# 3️⃣ 나라장터 (G2B) 입찰공고 수집기
# ==========================================
def collect_g2b():
    url = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoThngPPSSrch"
    kw_map = {
        "백신": ["폐렴구균"], "영양제": ["임산부 영양제", "엽산", "철분"],
        "대상포진": ["대상포진", "싱그릭스"]
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
# 4️⃣ 질병관리청 (KDCA) 감염병 통계 - 대상포진 매핑 강화
# ==========================================
def build_kdca_section(title, all_data, icon, color):
    v_data = [i for i in all_data if i.get('category') == '백신']
    z_data = [i for i in all_data if i.get('category') == '대상포진']
    m_data = [i for i in all_data if i.get('category') == '임산부감염병']
    
    def calc_total(items):
        return sum(int(i.get("resultVal", i.get("patntCnt", "0")) or 0) for i in items if str(i.get("resultVal", i.get("patntCnt", ""))).isdigit())

    v_total = calc_total(v_data)
    z_total = calc_total(z_data)
    m_total = calc_total(m_data)
    total_sum = v_total + z_total + m_total

    def make_cards(items):
        if not items: return "<p style='color:#7f8c8d; font-size:13px;'>집계된 데이터가 없습니다.</p>"
        cards = ""
        for i in items:
            disease = i.get("icdNm", i.get("diseaseNm", ""))
            group = i.get("icdGroupNm", "") # ✅ 급수(제2급 등) 복구
            count = i.get("resultVal", i.get("patntCnt", ""))
            url = "https://dportal.kdca.go.kr/pot/is/inftnsdsEDW.do" # ✅ 링크 URL 복구
            
            # ✅ 사진과 100% 동일한 상세 카드 디자인 복구
            cards += f"""
            <div style='display:inline-block;background:#fff5f5;border:1px solid #fcc;
                        border-left:4px solid #e74c3c;border-radius:6px;padding:12px 16px;
                        margin:4px 8px 8px 0;min-width:200px;vertical-align:top;'>
              <div style='font-size:15px;font-weight:bold;color:#c0392b;'>{disease}</div>
              <div style='font-size:12px;color:#888;margin:4px 0;'>{group} &nbsp;|&nbsp; 누계</div>
              <div style='font-size:22px;font-weight:bold;color:#e74c3c;'>{count}<span style='font-size:13px;color:#888;'>건</span></div>
              <div style='margin-top:6px;'>
                <a href='{url}' style='font-size:11px;color:#1a73e8;text-decoration:none;'>질병관리청 상세보기 -&gt;</a>
              </div>
            </div>"""
        return f"<div style='padding:4px;'>{cards}</div>"

    html = f"""
    <div style='margin-bottom:30px; border:1px solid #dcdde1; border-radius:8px; overflow:hidden; background:#ffffff;'>
        <div style='background:{color}; color:#ffffff; padding:12px 15px; font-size:16px; font-weight:bold;'>
            {icon} {title}
            <span style='float:right; background:rgba(255,255,255,0.3); padding:2px 10px; border-radius:12px; font-size:13px;'>{total_sum}건</span>
        </div>
        <div style='padding:15px;'>
            <h4 style='margin:0 0 10px 0; color:#2c3e50; border-left:4px solid {color}; padding-left:8px;'>🦠 폐렴구균 통계 (총 {v_total}건)</h4>
            {make_cards(v_data)}
            
            <h4 style='margin:25px 0 10px 0; color:#8e44ad; border-left:4px solid #8e44ad; padding-left:8px;'>🦠 대상포진 관련 통계 (총 {z_total}건)</h4>
            {make_cards(z_data)}
            
            <h4 style='margin:25px 0 10px 0; color:#27ae60; border-left:4px solid #27ae60; padding-left:8px;'>🤰 임산부 주의 감염병 통계 (총 {m_total}건)</h4>
            {make_cards(m_data)}
            
            <p style='color:#aaa;font-size:11px;margin-top:12px;border-top:1px solid #eee;padding-top:8px;'>
              ※ 출처: 질병관리청 감염병포털
            </p>
        </div>
    </div>"""
    return html

# ==========================================
# 5️⃣ 식약처 (MFDS) 및 6️⃣ 심평원 (HIRA)
# ==========================================
def collect_mfds():
    url = "http://apis.data.go.kr/1471000/DrugNatnShipmntAprvInfoService/getDrugNatnShipmntAprvInfoInq"
    targets = {
        "백신": ["폐렴구균", "프리베나", "캡박시브"], 
        "임산부": ["아다셀", "부스트릭스", "아브리스보"],
        "대상포진": ["대상포진", "싱그릭스", "스카이조스터"]
    }
    all_items, seen = [], set()
    for cat, kws in targets.items():
        for kw in kws:
            try:
                # 역순 탐색 로직 적용
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

def collect_hira():
    url = "https://apis.data.go.kr/B551182/dgamtCrtrInfoService1.2/getDgamtList"
    kws = {"백신": ["프리베나", "캡박시브"], "영양제": ["폴산", "철분"], "대상포진": ["싱그릭스", "스카이조스터"]}
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
# 🎨 UI 생성 (이전 형식 복구 및 대상포진 추가)
# ==========================================
def make_table(items, columns, col_keys):
    # 표시 개수 제한 (뉴스 등 너무 길어짐 방지)
    display_items = items[:10]
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
        </div>
    </div>"""
    return html

def build_kdca_section(title, all_data, icon, color):
    v_data = [i for i in all_data if i.get('category') == '백신']
    z_data = [i for i in all_data if i.get('category') == '대상포진']
    m_data = [i for i in all_data if i.get('category') == '임산부감염병']
    
    def ct(items): return sum(int(i.get("resultVal", i.get("patntCnt", "0")) or 0) for i in items if str(i.get("resultVal", i.get("patntCnt", ""))).isdigit())
    v_t, z_t, m_t = ct(v_data), ct(z_data), ct(m_data)

    def mc(items):
        if not items: return "<p style='color:#7f8c8d; font-size:13px;'>집계된 데이터가 없습니다.</p>"
        cards = ""
        for i in items:
            ds, cnt = i.get("icdNm", i.get("diseaseNm", "")), i.get("resultVal", i.get("patntCnt", ""))
            cards += f"""<div style='display:inline-block;background:#fff5f5;border:1px solid #fcc;border-left:4px solid #e74c3c;border-radius:6px;padding:12px;margin:4px 8px 8px 0;min-width:180px;'>
                <div style='font-size:14px;font-weight:bold;color:#c0392b;'>{ds}</div>
                <div style='font-size:20px;font-weight:bold;color:#e74c3c;'>{cnt}<span style='font-size:12px;color:#888;'>건</span></div>
            </div>"""
        return f"<div style='padding:4px;'>{cards}</div>"

    return f"""
    <div style='margin-bottom:30px; border:1px solid #dcdde1; border-radius:8px; overflow:hidden; background:#ffffff;'>
        <div style='background:{color}; color:#ffffff; padding:12px 15px; font-size:16px; font-weight:bold;'>{icon} {title} <span style='float:right; background:rgba(255,255,255,0.3); padding:2px 10px; border-radius:12px; font-size:13px;'>{v_t+z_t+m_t}건</span></div>
        <div style='padding:15px;'>
            <h4 style='margin:0 0 10px 0; color:#2c3e50; border-left:4px solid {color}; padding-left:8px;'>🦠 폐렴구균 통계 (총 {v_t}건)</h4> {mc(v_data)}
            <h4 style='margin:25px 0 10px 0; color:#8e44ad; border-left:4px solid #8e44ad; padding-left:8px;'>🦠 대상포진 관련 통계 (총 {z_t}건)</h4> {mc(z_data)}
            <h4 style='margin:25px 0 10px 0; color:#27ae60; border-left:4px solid #27ae60; padding-left:8px;'>🤰 임산부 주의 감염병 통계 (총 {m_t}건)</h4> {mc(m_data)}
            <p style='color:#aaa;font-size:11px;margin-top:12px;border-top:1px solid #eee;padding-top:8px;'>※ 출처: 질병관리청 감염병포털</p>
        </div>
    </div>"""

# ==========================================
# 🚀 메인 실행부
# ==========================================
def main():
    today = datetime.date.today().strftime("%Y년 %m월 %d일")
    print(f"🚀 {today} 데이터 수집 시작")
    
    addr, pw = os.environ.get("NAVER_ADDRESS"), os.environ.get("NAVER_PASSWORD")
    if not addr or not pw: return

    data = {"G2B": collect_g2b(), "NEWS": collect_naver_news(), "PUBMED": collect_pubmed(), 
            "KDCA": collect_kdca(), "MFDS": collect_mfds(), "HIRA": collect_hira()}
    
    html_body = f"""<html><body style='font-family:"Malgun Gothic", sans-serif; padding:20px; background:#f0f2f5;'>
        <div style='max-width:800px; margin:0 auto;'>
            <div style='text-align:center; margin-bottom:30px;'><h1 style='color:#2c3e50;'>📊 통합 인텔리전스 브리핑</h1><p style='color:#7f8c8d;'>{today} 기준 자동화 리포트</p></div>
            {build_section("네이버 최신 뉴스", data['NEWS'], ['제목', '날짜', '링크'], ['title', 'pubDate', 'link'], "📰", "#3498db")}
            {build_section("나라장터 입찰공고", data['G2B'], ['공고명', '기관명', '공고일', '링크'], ['bidNtceNm', 'ntceInsttNm', 'bidNtceDt', 'bidNtceUrl'], "🏛️", "#e67e22")}
            {build_section("학술 논문 (PubMed)", data['PUBMED'], ['제목', '저널', '연도', '링크'], ['title', 'journal', 'year', 'link'], "🔬", "#9b59b6")}
            {build_kdca_section("질병관리청 감염병 현황", data['KDCA'], "🏥", "#e74c3c")}
            {build_section("식약처 국가출하승인", data['MFDS'], ['제품명', '제조사', '승인일'], ['SAMPLE_TYPE', 'MANUF_ENTP_NAME', 'RESULT_TIME'], "💊", "#1abc9c")}
            {build_section("심평원 약가 정보", data['HIRA'], ['제품명', '제약사', '상한금액'], ['itmNm', 'entrpsNm', 'mxDpc'], "💰", "#f1c40f")}
        </div></body></html>"""

    msg = MIMEMultipart(); msg["Subject"] = f"📊 [통합 브리핑] 백신 및 영양제 데일리 리포트 - {today}"
    msg["From"] = addr; msg["To"] = addr
    msg.attach(MIMEText(html_body, "html"))
    
    try:
        with smtplib.SMTP_SSL("smtp.naver.com", 465) as s:
            s.login(addr, pw); s.send_message(msg)
        print("✅ 브리핑 이메일 발송 완료!")
    except Exception as e: print(f"❌ 이메일 발송 오류: {e}")

if __name__ == "__main__": main()
