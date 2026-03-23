"""
naver_tennis_collector.py
네이버 블로그/카페 API - 테니스 스트링 정보 수집기
"""

import os
import re
import requests

CLIENT_ID     = os.environ.get("NAVER_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")

KEYWORDS = [
    "테니스 스트링 추천",
    "테니스 스트링 후기",
    "테니스 거트 교체",
    "폴리 스트링 테니스",
    "테니스 스트링 장력",
    "테니스 줄 추천",
]

SEARCH_TYPES = {
    "blog":        "블로그",
    "cafearticle": "카페",
}


def clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def search_naver(query: str, search_type: str, display: int = 5) -> list[dict]:
    url = f"https://openapi.naver.com/v1/search/{search_type}"
    headers = {
        "X-Naver-Client-Id":     CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }
    params = {"query": query, "display": display, "sort": "date"}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get("items", [])
    except requests.RequestException as e:
        print(f"[네이버] '{query}' ({search_type}) 오류: {e}")
        return []


def collect_tennis_posts(display_per_keyword: int = 5) -> list[dict]:
    all_posts: list[dict] = []
    seen_links: set[str] = set()

    for keyword in KEYWORDS:
        for search_type, type_label in SEARCH_TYPES.items():
            items = search_naver(keyword, search_type, display=display_per_keyword)
            print(f"[네이버] '{keyword}' {type_label}: {len(items)}건")
            for item in items:
                link = item.get("link", "")
                if not link or link in seen_links:
                    continue
                seen_links.add(link)
                all_posts.append({
                    "title":       clean_html(item.get("title", "제목 없음")),
                    "link":        link,
                    "description": clean_html(item.get("description", "")),
                    "date":        item.get("postdate", ""),
                    "author":      item.get("bloggername", ""),
                    "cafe_name":   item.get("cafename", ""),
                    "source_type": type_label,
                    "keyword":     keyword,
                })

    print(f"[네이버] 총 수집 (중복 제거): {len(all_posts)}건")
    return all_posts
