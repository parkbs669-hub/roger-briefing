import requests
import os
import xml.etree.ElementTree as ET

API_KEY = os.environ.get("PUBLIC_DATA_API_KEY", "")
URL = "http://apis.data.go.kr/1471000/DrugNatnShipmntAprvInfoService/getDrugNatnShipmntAprvInfoInq"

def collect_mfds():
    # ✅ 폐렴구균 관련 백신과 임산부 관련 백신(Tdap, RSV)을 명확히 타겟팅
    targets = {
        "백신": ["폐렴구균", "프리베나", "캡박시브", "박스뉴반스", "프로디악스"], 
        "임산부": ["아다셀", "부스트릭스", "아브리스보", "백일해"] 
    }
    all_items = []
    seen = set()
    
    NUM_OF_ROWS = 50
    CUTOFF_YEAR = "2025"  

    for cat, kws in targets.items():
        for kw in kws:
            params = {"serviceKey": API_KEY, "pageNo": 1, "numOfRows": 1, "goods_name": kw}
            try:
                resp = requests.get(URL, params=params, timeout=15)
                root = ET.fromstring(resp.text.strip())
                total_count = int(root.findtext(".//totalCount", "0") or 0)
                
                if total_count == 0:
                    continue
                    
                total_pages = (total_count + NUM_OF_ROWS - 1) // NUM_OF_ROWS
                
                for page in range(total_pages, 0, -1):
                    params_page = {"serviceKey": API_KEY, "pageNo": page, "numOfRows": NUM_OF_ROWS, "goods_name": kw}
                    resp_page = requests.get(URL, params_page, timeout=15)
                    root_page = ET.fromstring(resp_page.text.strip())
                    
                    items_found = root_page.findall(".//item")
                    page_has_recent = False
                    
                    for item in items_found:
                        d = {c.tag: (c.text or "") for c in item}
                        result_time = d.get("RESULT_TIME", "")
                        
                        if result_time and result_time[:4] < CUTOFF_YEAR:
                            continue
                            
                        page_has_recent = True
                        receipt_no = d.get("RECEIPT_NO", "")
                        
                        if receipt_no and receipt_no not in seen:
                            d['category'] = cat # '백신' 또는 '임산부'로 태깅
                            seen.add(receipt_no)
                            all_items.append(d)
                    
                    if not page_has_recent and page < total_pages:
                        break
                        
            except Exception as e: 
                print(f"MFDS '{kw}' 수집 오류: {e}")
                continue
                
    # 최신 날짜순 완벽 정렬
    all_items.sort(key=lambda x: str(x.get("RESULT_TIME", "")), reverse=True)
    return all_items[:20]
