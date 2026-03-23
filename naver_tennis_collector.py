"""
네이버 블로그/카페 API - 테니스 스트링 정보 수집기
이미 roger-briefing에 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET이 있으므로 추가 키 불필요!
"""

import os
import requests
from datetime import datetime

CLIENT_ID     = os.environ.get("NAVER_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")

# 검색 키워드 목록
KEYWORDS = [
    "테니스 스트링 추천",
    "테니스 스트링 후기",
    "테니스 거트 교체",
    "폴리 스트링 테니스",
    "테니스 스트링 장력",
    "테니스 줄 추천",
]

# 검색 타입
SEARCH_TYPES = {
    "blog":         "블로그",
    "cafearticle":  "카페",
}


def search_naver(query: str, search_type: str, display: int = 5) -> list[dict]:
    """네이버 블로그 or 카페 검색"""
    url = f"https://openapi.naver.com/v1/search/{search_type}"
    headers = {
        "X-Naver-Client-Id":     CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }
    params = {
        "query":   query,
        "display": display,
        "sort":    "date",  # 최신순
    }
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get("items", [])
    except requests.RequestException as e:
        print(f"[네이버] '{query}' ({search_type}) 요청 오류: {e}")
        return []


def clean_html(text: str) -> str:
    """네이버 API 응답의 HTML 태그 제거"""
    import re
    return re.sub(r"<[^>]+>", "", text).strip()


def collect_tennis_posts(display_per_keyword: int = 5) -> list[dict]:
    """
    모든 키워드 × 블로그/카페 검색 후 중복 제거해서 반환
    """
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
                    "date":        item.get("postdate", ""),        # 블로그: YYYYMMDD
                    "author":      item.get("bloggername", ""),     # 블로그만
                    "cafe_name":   item.get("cafename", ""),        # 카페만
                    "source_type": type_label,
                    "keyword":     keyword,
                })

    print(f"[네이버] 총 수집 (중복 제거): {len(all_posts)}건")
    return all_posts


if __name__ == "__main__":
    posts = collect_tennis_posts()
    for p in posts:
        print(f"  [{p['source_type']}] {p['title']} ({p['date']})")
        print(f"    → {p['link']}")
