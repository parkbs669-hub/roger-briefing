import requests
import os
import datetime

API_KEY = os.environ.get("PUBLIC_DATA_API_KEY", "")
URL = "https://apis.data.go.kr/1790387/EIDAPIService/Disease"

def collect_kdca():
    params = {"serviceKey": API_KEY, "resType": "2", "searchType": "1", 
              "searchYear": datetime.date.today().strftime("%Y"), "patntType": "1", "numOfRows": 100}
    try:
        resp = requests.get(URL, params=params, timeout=30)
        data = resp.json()
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(items, dict): items = [items]
        
        res = []
        for i in items:
            disease_name = i.get("icdNm", i.get("diseaseNm", ""))
            if "폐렴구균" in disease_name: 
                i['category'] = "백신"; res.append(i)
            elif "빈혈" in disease_name: 
                i['category'] = "영양제"; res.append(i)
        return res
    except: return []
