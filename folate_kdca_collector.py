import requests
import os
import datetime

API_KEY = os.environ.get("PUBLIC_DATA_API_KEY", "")
URL = "https://apis.data.go.kr/1790387/EIDAPIService/Disease"

def fetch_kdca_by_year(year):
    """특정 연도의 질병관리청 데이터를 호출하는 내부 함수"""
    params = {
        "serviceKey": API_KEY, "resType": "2", "searchType": "1", 
        "searchYear": year, "patntType": "1", "numOfRows": 100
    }
    try:
        resp = requests.get(URL, params=params, timeout=30)
        data = resp.json()
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(items, dict): items = [items]
        return items if items else []
    except:
        return []

def collect_kdca():
    # 1. 올해 데이터 먼저 조회
    current_year = datetime.date.today().strftime("%Y")
    items = fetch_kdca_by_year(current_year)
    
    # 2. 만약 올해 데이터가 아직 0건이라면 전년도 데이터로 폴백(Fallback) 조회!
    if not items:
        prev_year = str(int(current_year) - 1)
        items = fetch_kdca_by_year(prev_year)

    res = []
    # 임산부 주의 감염병 키워드
    maternal_infections = ["백일해", "풍진", "매독", "지카"]
    
    for i in items:
        disease_name = i.get("icdNm", i.get("diseaseNm", ""))
        
        if "폐렴구균" in disease_name: 
            i['category'] = "백신"
            res.append(i)
        elif any(kw in disease_name for kw in maternal_infections): 
            i['category'] = "임산부감염병" # 영양제가 아닌 명확한 카테고리 부여
            res.append(i)
            
    return res
