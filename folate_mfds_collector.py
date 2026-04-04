import requests
import os
import xml.etree.ElementTree as ET

API_KEY = os.environ.get("PUBLIC_DATA_API_KEY", "")
URL = "http://apis.data.go.kr/1471000/DrugNatnShipmntAprvInfoService/getDrugNatnShipmntAprvInfoInq"

def collect_mfds():
    targets = {"백신": ["폐렴구균", "프리베나", "캡박시브"], "영양제": ["엽산", "철분"]}
    all_items = []
    seen = set()
    
    NUM_OF_ROWS = 50
    CUTOFF_YEAR = "2025"  # 2025년 1월 1일 이후 데이터만 수집

    for cat, kws in targets.items():
        for kw in kws:
            # 1. 전체 데이터 건수(totalCount)부터 확인
            params = {"serviceKey": API_KEY, "pageNo": 1, "numOfRows": 1, "goods_name": kw}
            try:
                resp = requests.get(URL, params=params, timeout=15)
                root = ET.fromstring(resp.text.strip())
                total_count = int(root.findtext(".//totalCount", "0") or 0)
                
                if total_count == 0:
                    continue
                    
                total_pages = (total_count + NUM_OF_ROWS - 1) // NUM_OF_ROWS
                
                # 2. 마지막 페이지(최신)부터 역순으로 거꾸로 탐색!
                for page in range(total_pages, 0, -1):
                    params_page = {"serviceKey": API_KEY, "pageNo": page, "numOfRows": NUM_OF_ROWS, "goods_name": kw}
                    resp_page = requests.get(URL, params=params_page, timeout=15)
                    root_page = ET.fromstring(resp_page.text.strip())
                    
                    items_found = root_page.findall(".//item")
                    page_has_recent = False
                    
                    for item in items_found:
                        d = {c.tag: (c.text or "") for c in item}
                        result_time = d.get("RESULT_TIME", "")
                        
                        # 2025년 미만 옛날 데이터가 나오면 그 페이지 내역은 패스
                        if result_time and result_time[:4] < CUTOFF_YEAR:
                            continue
                            
                        page_has_recent = True
                        receipt_no = d.get("RECEIPT_NO", "")
                        
                        # 중복 제거 및 카테고리(백신/영양제) 태깅
                        if receipt_no and receipt_no not in seen:
                            d['category'] = cat
                            seen.add(receipt_no)
                            all_items.append(d)
                    
                    # 이 페이지에 2025년 이후 최신 데이터가 하나도 없었다면, 그 앞 페이지들은 더 옛날이므로 탐색 즉시 중단
                    if not page_has_recent and page < total_pages:
                        break
                        
            except Exception as e: 
                print(f"MFDS '{kw}' 수집 오류: {e}")
                continue
                
    # 수집된 데이터들을 최신 날짜순으로 완벽하게 정렬 (내림차순)
    all_items.sort(key=lambda x: str(x.get("RESULT_TIME", "")), reverse=True)
    
    # 이메일에 표출할 최대 개수 조절 (너무 길어지지 않도록 최신 15건만)
    return all_items[:15]
