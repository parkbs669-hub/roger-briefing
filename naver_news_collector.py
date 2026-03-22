"""
네이버 뉴스 수집기 - 폐렴구균 백신 최신 뉴스
"""
import requests
import os
import datetime
import urllib.parse

CLIENT_ID     = os.environ.get("NAVER_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")

URL = "https://openapi.naver.com/v1/search/news.json"

def search_naver_news(keyword, display=5):
    """네이버 뉴스 검색"""
    headers = {
        "X-Naver-Client-Id":     CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }
    params = {
        "query":   keyword,
        "display": display,
        "sort":    "date",  # 최신순
    }
    try:
        resp = requests.get(URL, headers=headers, params=params, timeout=15)
        print(f"  네이버 뉴스 '{keyword}' HTTP: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  오류: {resp.text[:200]}")
            return []
        data = resp.json()
        items = data.get("items", [])
        # HTML 태그 제거
        cleaned = []
        for item in items:
            cleaned.append({
                "title":       item.get("title","").replace("<b>","").replace("</b>",""),
                "description": item.get("description","").replace("<b>","").replace("</b>",""),
                "link":        item.get("link",""),
                "pubDate":     item.get("pubDate",""),
                "keyword":     keyword,
            })
        return cleaned
    except Exception as e:
        print(f"  네이버 뉴스 오류: {e}")
        return []


def collect_naver_news():
    """폐렴구균 관련 최신 뉴스 수집"""
    keywords = [
        "폐렴구균 백신",
        "캡박시브",
        "PCV20 PCV21",
        "프리베나 백신",
        "폐렴구균 NIP",
        "폐렴구균 예방접종",
    ]
    all_news = []
    seen = set()

    for kw in keywords:
        print(f"  🔍 네이버 뉴스: '{kw}'")
        items = search_naver_news(kw, display=3)
        for item in items:
            title = item.get("title","")
            if title not in seen:
                seen.add(title)
                all_news.append(item)
        print(f"     → {len(items)}건")

    print(f"  네이버 뉴스 총 {len(all_news)}건 수집")
    return all_news[:15]  # 최대 15건
