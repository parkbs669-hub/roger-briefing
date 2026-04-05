import os
import time
import requests
import datetime
import xml.etree.ElementTree as ET
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ==========================================
# 🔑 환경 변수 및 설정 로드
# ==========================================
PUBLIC_DATA_API_KEY = os.environ.get("PUBLIC_DATA_API_KEY", "")
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")
NAVER_ADDRESS = os.environ.get("NAVER_ADDRESS", "")
NAVER_PASSWORD = os.environ.get("NAVER_PASSWORD", "")

# 다중 수신자 설정 (쉼표로 구분된 문자열을 리스트로 변환)
RECIPIENTS_STR = os.environ.get("REPORT_RECIPIENTS", NAVER_ADDRESS)
RECIPIENTS = [r.strip() for r in RECIPIENTS_STR.split(",") if r.strip()]

# ==========================================
# 1️⃣ PubMed (글로벌 학술 논문) 수집기
# ==========================================
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
                params={"db": "pubmed", "term": q, "retmax": 4, "sort": "date",
                        "retmode": "json", "datetype": "pdat", "reldate": 60}, timeout=15)
            ids = r.json().get("esearchresult", {}).get("idlist", [])
            if not ids: continue

            fr = requests.get(f"{base_url}/efetch.fcgi",
                params={"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}, timeout=15)
            time.sleep(0.5)
            
            # ✅ XML 검증 로직 적용 완료
            xml_text = fr.content.decode("utf-8-sig").strip()
            if not xml_text or not xml_text.startswith("<"):
                print(f"  [경고] PubMed {cat}: 유효하지 않은 응답 형식 건너뜀")
                continue

            # ✅ 검증된 텍스트로만 파싱 (기존 중복 코드는 삭제됨)
            root = ET.fromstring(xml_text)

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
        except Exception as e:
            print(f"  PubMed {cat} 수집 오류: {e}")
            continue
            
    return all_papers[:15]

# ==========================================
# 2️⃣ 네이버 뉴스 수집기
# ==========================================
def collect_naver_news():
    url = "https://openapi.naver.com/v1/search/news.json"
    kw_map = {
        "백신": ["폐렴구균 백신", "캡박시브", "PCV20", "프리베나"],
        "영양제": ["임산부 엽산", "임산부 철분제", "보건소 엽산"],
        "대상포진": ["대상포진 백신", "싱그릭스", "스카이조스터"]
    }
    all_news, seen = [], set()
    headers = {"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
    
    for cat, kws in kw_map.items():
        for kw in kws:
            try:
                resp = requests.get(url, headers=headers, params={"query": kw, "display": 3, "sort": "date"}, timeout=15)
                items = resp.json().get("items", [])
                for i in items:
                    title = i.get("title","").replace("<b>","").replace("</b>","")
                    if title not in seen:
                        seen.add(title)
                        all_news.append({
                            "title": title,
                            "link": i.get("link",""),
                            "pubDate": i.get("pubDate","")[:16],
                            "category": cat
                        })
            except Exception as e:
                print(f"  뉴스 {kw} 수집 오류: {e}")
    return all_news[:15]

# ==========================================
# 3️⃣ 나라장터 (G2B) 입찰공고 수집기
# ==========================================
def collect_g2b():
    url = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoThngPPSSrch"
    kw_map = {
        "백신": ["폐렴구균", "PCV20"], 
        "영양제": ["엽산", "철분제", "임산부 영양제"],
        "대상포진": ["대상포진", "싱그릭스"]
    }
    all_items, seen = [], set()
    start = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y%m%d0000")
    end = datetime.datetime.now().strftime("%Y%m%d2359")
    
    for cat, kws in kw_map.items():
        for kw in kws:
            params = {"ServiceKey": PUBLIC_DATA_API_KEY, "inqryDiv": "1", "inqryBgnDt": start, 
                      "inqryEndDt": end, "bidNtceNm": kw, "numOfRows": "10", "type": "xml"}
            try:
                resp = requests.get(url, params=params, timeout=15)
                root = ET.fromstring(resp.text.strip())
                for item in root.findall(".//item"):
                    d = {c.tag: (c.text or "") for c in item}
                    bid_no = d.get("bidNtceNo", "")
                    if bid_no and bid_no not in seen:
                        d['category'] = cat
                        seen.add(bid_no)
                        all_items.append(d)
            except Exception as e:
                print(f"  나라장터 {kw} 수집 오류: {e}")
    return all_items

# ==========================================
# 4️⃣ 질병관리청 (KDCA) 감염병 통계
# ==========================================
def collect_kdca():
    url = "https://apis.data.go.kr/1790387/EIDAPIService/Disease"
    
    def fetch_by_year(year):
        params = {"serviceKey": PUBLIC_DATA_API_KEY, "resType": "2", "searchType": "1", 
                  "searchYear": year, "patntType": "1", "pageNo": 1, "numOfRows": 100}
        try:
            resp = requests.get(url, params=params, timeout=30)
            data = resp.json()
            # 다중 get 구조로 안정적 파싱
            items = (data.get("body", {}).get("items", {}) or 
                     data.get("response", {}).get("body", {}).get("items", {}) or 
                     data.get("items", {}) or {})
            if isinstance(items, dict): items = items.get("item", []) or []
            if isinstance(items, dict): items = [items]
            return items or []
        except Exception as e:
            print(f"  KDCA {year} 조회 오류: {e}")
            return []

    current_year = datetime.date.today().strftime("%Y")
    items = fetch_by_year(current_year)
    if not items: # 올해 데이터 없으면 작년 데이터로 폴백
        items = fetch_by_year(str(int(current_year) - 1))

    res = []
    maternal_infections = ["백일해", "풍진", "매독", "지카"]
    for i in items:
        disease_name = i.get("icdNm", i.get("diseaseNm", ""))
        if "폐렴구균" in disease_name: 
            i['category'] = "백신"; res.append(i)
        elif any(kw in disease_name for kw in maternal_infections): 
            i['category'] = "임산부감염병"; res.append(i)
        elif "대상포진" in disease_name:
            i['category'] = "대상포진"; res.append(i)
    return res

# ==========================================
# 5️⃣ 식약처 (MFDS) 국가출하승인 (역순 탐색)
# ==========================================
def collect_mfds():
    url = "http://apis.data.go.kr/1471000/DrugNatnShipmntAprvInfoService/getDrugNatnShipmntAprvInfoInq"
    targets = {
        "백신": ["폐렴구균", "프리베나", "캡박시브", "박스뉴반스"], 
        "임산부": ["아다셀", "부스트릭스", "아브리스보"],
        "대상포진": ["대상포진", "싱그릭스", "스카이조스터"]
    }
    all_items, seen = [], set()
    NUM_OF_ROWS, CUTOFF_YEAR = 50, "2025"

    for cat, kws in targets.items():
        for kw in kws:
            try:
                # 전체 건수 확인
                resp = requests.get(url, params={"serviceKey": PUBLIC_DATA_API_KEY, "pageNo": 1, "numOfRows": 1, "goods_name": kw}, timeout=15)
                root = ET.fromstring(resp.text.strip())
                total_count = int(root.findtext(".//totalCount", "0") or 0)
                if total_count == 0: continue
                total_pages = (total_count + NUM_OF_ROWS - 1) // NUM_OF_ROWS
                
                # 마지막 페이지부터 역순 탐색
                for page in range(total_pages, 0, -1):
                    resp_page = requests.get(url, params={"serviceKey": PUBLIC_DATA_API_KEY, "pageNo": page, "numOfRows": NUM_OF_ROWS, "goods_name": kw}, timeout=15)
                    root_page = ET.fromstring(resp_page.text.strip())
                    items_found = root_page.findall(".//item")
                    page_has_recent = False
                    
                    for item in items_found:
                        d = {c.tag: (c.text or "") for c in item}
                        result_time = d.get("RESULT_TIME", "")
                        if result_time and result_time[:4] < CUTOFF_YEAR: continue
                        
                        page_has_recent = True
                        if d.get("RECEIPT_NO") not in seen:
                            d['category'] = cat; seen.add(d.get("RECEIPT_NO")); all_items.append(d)
                    if not page_has_recent and page < total_pages: break
            except Exception as e:
                print(f"  식약처 {kw} 수집 오류: {e}")
                continue
    all_items.sort(key=lambda x: str(x.get("RESULT_TIME", "")), reverse=True)
    return all_items[:20]

# ==========================================
# 6️⃣ 심평원 (HIRA) 약가 정보
# ==========================================
def collect_hira():
    url = "https://apis.data.go.kr/B551182/dgamtCrtrInfoService1.2/getDgamtList"
    kws = {
        "백신": ["프리베나", "캡박시브"], 
        "영양제": ["폴산", "철분"],
        "대상포진": ["싱그릭스", "스카이조스터"]
    }
    all_items, seen = [], set()
    for cat, words in kws.items():
        for kw in words:
            try:
                params = {"serviceKey": PUBLIC_DATA_API_KEY, "itmNm": kw, "pageNo": 1, "numOfRows": 10}
                resp = requests.get(url, params=params, timeout=15)
                root = ET.fromstring(resp.text.strip())
                for item in root.findall(".//item"):
                    d = {c.tag: (c.text or "") for c in item}
                    if d.get("itmCd") not in seen:
                        d['category'] = cat; seen.add(d.get("itmCd")); all_items.append(d)
            except Exception as e:
                print(f"  심평원 {kw} 수집 오류: {e}")
    return all_items[:15]

# ==========================================
# 🎨 HTML UI 구성 및 메일 발송
# ==========================================
def make_table(items, columns, col_keys):
    if not items: return "<p style='color:#7f8c8d; font-size:13px;'>관련 데이터 없음</p>"
    th_html = "".join([f"<th style='padding:8px; text-align:left; background:#f4f6f7; border-bottom:2px solid #bdc3c7;'>{col}</th>" for col in columns])
    tr_html = ""
    for i in items:
        tds = []
        for key in col_keys:
            val = str(i.get(key, ''))
            if key == 'bidNtceUrl' and val: val = f"<a href='{val}' style='color:#3498db;'>공고보기</a>"
            elif key == 'link' and val:
                lt = "기사" if "naver.com" in val else "PubMed" if "pubmed" in val else "링크"
                val = f"<a href='{val}' style='color:#3498db;'>{lt}</a>"
            tds.append(f"<td style='padding:8px; border-bottom:1px solid #ecf0f1; font-size:13px;'>{val}</td>")
        tr_html += f"<tr>{''.join(tds)}</tr>"
    return f"<table width='100%' style='border-collapse:collapse;'><thead><tr>{th_html}</tr></thead><tbody>{tr_html}</tbody></table>"

def build_section(title, all_data, columns, col_keys, icon, color):
    v_data = [i for i in all_data if i.get('category') == '백신']
    z_data = [i for i in all_data if i.get('category') == '대상포진']
    n_data = [i for i in all_data if i.get('category') in ['영양제', '임산부감염병', '임산부']]
    
    n_title = "🤰 임산부 백신 섹션" if "식약처" in title else "🤰 임산부 영양제 및 관련 섹션"
    
    return f"""
    <div style='margin-bottom:30px; border:1px solid #dcdde1; border-radius:8px; overflow:hidden; background:#ffffff;'>
        <div style='background:{color}; color:#ffffff; padding:12px 15px; font-size:16px; font-weight:bold;'>{icon} {title}</div>
        <div style='padding:15px;'>
            <h4 style='margin:0 0 10px 0; color:#2c3e50; border-left:4px solid {color}; padding-left:8px;'>💉 폐렴구균 백신 섹션</h4>
            {make_table(v_data, columns, col_keys)}
            <h4 style='margin:25px 0 10px 0; color:#8e44ad; border-left:4px solid #8e44ad; padding-left:8px;'>🦠 대상포진 섹션</h4>
            {make_table(z_data, columns, col_keys)}
            <h4 style='margin:25px 0 10px 0; color:#27ae60; border-left:4px solid #27ae60; padding-left:8px;'>{n_title}</h4>
            {make_table(n_data, columns, col_keys)}
        </div>
    </div>"""

def build_kdca_section(title, all_data, icon, color):
    kdca_data = [i for i in all_data if i.get('category') in ['백신', '임산부감염병', '대상포진']]
    ts = sum(int(i.get("resultVal", i.get("patntCnt", "0")) or 0) for i in kdca_data if str(i.get("resultVal", i.get("patntCnt", ""))).isdigit())
    cards = ""
    for i in kdca_data:
        disease, count = i.get("icdNm", i.get("diseaseNm", "")), i.get("resultVal", i.get("patntCnt", ""))
        cards += f"""<div style='display:inline-block;background:#fff5f5;border:1px solid #fcc;border-left:4px solid #e74c3c;border-radius:6px;padding:12px;margin:0 8px 8px 0;min-width:180px;'>
          <div style='font-size:14px;font-weight:bold;color:#c0392b;'>{disease}</div>
          <div style='font-size:20px;font-weight:bold;color:#e74c3c;'>{count}<span style='font-size:12px;color:#888;'>건</span></div>
        </div>"""
    return f"<div style='margin-bottom:30px; border:1px solid #dcdde1; border-radius:8px; overflow:hidden; background:#ffffff;'>" + \
           f"<div style='background:{color}; color:#ffffff; padding:12px 15px; font-size:16px; font-weight:bold;'>{icon} {title} <span style='float:right;background:rgba(255,255,255,0.3);padding:2px 10px;border-radius:12px;'>{ts}건</span></div>" + \
           f"<div style='padding:15px;'>{cards if cards else '데이터 없음'}</div></div>"

# ==========================================
# 🚀 메인 실행부 (데이터 수집 및 메일 발송)
# ==========================================
def main():
    today = datetime.date.today().strftime("%Y년 %m월 %d일")
    print(f"🚀 {today} 데이터 통합 브리핑 시작")
    
    # ✅ 수정 1: 이메일 주소 공백 제거 및 유효성 검사 (빈 값 방지)
    raw_recipients = os.environ.get("REPORT_RECIPIENTS", NAVER_ADDRESS)
    RECIPIENTS = [r.strip() for r in raw_recipients.split(",") if r.strip() and "@" in r]
    if not RECIPIENTS:
        RECIPIENTS = [NAVER_ADDRESS] # 잘못 입력됐을 경우 무조건 본인에게 발송
    
    data = {"G2B": collect_g2b(), "NEWS": collect_naver_news(), "PUBMED": collect_pubmed(), 
            "KDCA": collect_kdca(), "MFDS": collect_mfds(), "HIRA": collect_hira()}
    
    html = f"""<html><body style='font-family:sans-serif; padding:20px; background:#f0f2f5;'>
        <div style='max-width:800px; margin:0 auto;'>
            <h1 style='text-align:center; color:#2c3e50;'>📊 통합 인텔리전스 브리핑</h1>
            {build_section("네이버 최신 뉴스", data['NEWS'], ['제목', '날짜', '링크'], ['title', 'pubDate', 'link'], "📰", "#3498db")}
            {build_section("나라장터 입찰공고", data['G2B'], ['공고명', '기관명', '날짜', '링크'], ['bidNtceNm', 'ntceInsttNm', 'bidNtceDt', 'bidNtceUrl'], "🏛️", "#e67e22")}
            {build_section("학술 논문 (PubMed)", data['PUBMED'], ['제목', '저널', '연도', '링크'], ['title', 'journal', 'year', 'link'], "🔬", "#9b59b6")}
            {build_kdca_section("질병관리청 감염병 현황", data['KDCA'], "🏥", "#e74c3c")}
            {build_section("식약처 국가출하승인", data['MFDS'], ['제품명', '제조사', '승인일'], ['SAMPLE_TYPE', 'MANUF_ENTP_NAME', 'RESULT_TIME'], "💊", "#1abc9c")}
            {build_section("심평원 약가 정보", data['HIRA'], ['제품명', '제약사', '상한금액'], ['itmNm', 'entrpsNm', 'mxDpc'], "💰", "#f1c40f")}
        </div></body></html>"""

    msg = MIMEMultipart()
    msg["Subject"] = f"📊 [통합 브리핑] 백신 및 영양제 데일리 리포트 - {today}"
    msg["From"] = NAVER_ADDRESS
    msg["To"] = ", ".join(RECIPIENTS)
    msg.attach(MIMEText(html, "html"))
    
    try:
        with smtplib.SMTP_SSL("smtp.naver.com", 465) as s:
            s.login(NAVER_ADDRESS, NAVER_PASSWORD)
            # ✅ 수정 2: send_message 대신 sendmail 사용 (다중 발송 에러 원천 차단)
            s.sendmail(NAVER_ADDRESS, RECIPIENTS, msg.as_string())
        print(f"✅ 발송 완료 (수신: {len(RECIPIENTS)}명)")
    except Exception as e: 
        print(f"❌ 발송 실패: {e}")

if __name__ == "__main__": 
    main()
