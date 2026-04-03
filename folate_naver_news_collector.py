import requests
import os

CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")
URL = "https://openapi.naver.com/v1/search/news.json"

def search_naver_news(keyword, cat):
    headers = {"X-Naver-Client-Id": CLIENT_ID, "X-Naver-Client-Secret": CLIENT_SECRET}
    params = {"query": keyword, "display": 3, "sort": "date"}
    try:
        resp = requests.get(URL, headers=headers, params=params, timeout=15)
        if resp.status_code != 200: return []
        items = resp.json().get("items", [])
        return [{
            "title": i.get("title","").replace("<b>","").replace("</b>",""),
            "description": i.get("description","").replace("<b>","").replace("</b>",""),
            "link": i.get("link",""),
            "pubDate": i.get("pubDate","")[:16],
            "category": cat
        } for i in items]
    except Exception as e:
        print(f"Naver News 오류: {e}")
        return []

def collect_naver_news():
    kw_map = {
        "백신": ["폐렴구균 백신", "캡박시브", "PCV20", "프리베나"],
        "영양제": ["임산부 엽산", "임산부 철분제", "보건소 엽산"]
    }
    all_news, seen = [], set()
    for cat, kws in kw_map.items():
        for kw in kws:
            for item in search_naver_news(kw, cat):
                if item['title'] not in seen:
                    seen.add(item['title'])
                    all_news.append(item)
    return all_news[:15]
