import requests
import os
import datetime

# 원본 코드처럼 3가지 키 중 하나라도 걸리도록 복원 (안전성 강화)
API_KEY = (
    os.environ.get("PUBLIC_DATA_API_KEY") or
    os.environ.get("HIRA_SERVICE_KEY") or
    os.environ.get("G2B_API_KEY", "")
)

URL = "https://apis.data.go.kr/1790387/EIDAPIService/Disease"

def fetch_kdca_by_year(year):
    """특정 연도의 데이터를 가져오는 내부 함수 (원본 로직 100% 복원)"""
    params = {
        "serviceKey": API_KEY,
        "resType":    "2",
        "searchType": "1",
        "searchYear": year,
        "patntType":  "1",
        "pageNo":     1,     # ✅ 제가 실수로 지웠던 필수 파라미터 복원
        "numOfRows":  100,
    }
    
    try:
        resp = requests.get(URL, params=params, timeout=30)
        if not resp.text.strip(): return []
        
        data = resp.json()
        
        # ✅ 원본 코드의 "방어적 JSON 파싱" 로직 완벽 복원
        items = (
            data.get("body", {}).get("items", {}) or
            data.get("response", {}).get("body", {}).get("items", {}) or
            data.get("items", {}) or {}
        )
        if isinstance(items, dict):
            items = items.get("item", []) or []
        if isinstance(items, dict):
            items = [items]
            
        items = items or []
        return items
        
    except Exception as e:
        print(f"KDCA API 조회 오류 ({year}년): {e}")
        return []

def collect_kdca():
    # 1. 올해 데이터 먼저 조회
    current_year = datetime.date.today().strftime("%Y")
    items = fetch_kdca_by_year(current_year)
    
    # 2. 만약 올해 데이터가 아직 없다면 작년 데이터로 Fallback (원본 로직)
    if not items:
        prev_year = str(int(current_year) - 1)
        items = fetch_kdca_by_year(prev_year)

    res = []
    # 임산부 주요 감염병 필터링 키워드
    maternal_infections = ["백일해", "풍진", "매독", "지카"]
    
    for i in items:
        disease_name = i.get("icdNm", i.get("diseaseNm", ""))
        
        # 내부 분류용 카테고리 태깅
        if "폐렴구균" in disease_name: 
            i['category'] = "백신"
            res.append(i)
        elif any(kw in disease_name for kw in maternal_infections): 
            i['category'] = "임산부감염병"
            res.append(i)
            
    return res
