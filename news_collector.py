# newsapi.org에서 폐렴구균 백신 관련 뉴스를 수집하는 모듈
import os
import requests
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))


def collect_news(keywords: list, api_key: str, days: int = 7, page_size: int = 3) -> list:
    base_url = "https://newsapi.org/v2/everything"
    from_date = (datetime.now(KST) - timedelta(days=days)).strftime("%Y-%m-%d")
    results = []

    for kw in keywords:
        try:
            r = requests.get(base_url, params={
                "q": kw,
                "apiKey": api_key,
                "language": "en",
                "sortBy": "publishedAt",
                "from": from_date,
                "pageSize": page_size,
            }, timeout=10)
            for a in r.json().get("articles", [])[:page_size]:
                results.append({
                    "keyword": kw,
                    "title": a.get("title", ""),
                    "source": a.get("source", {}).get("name", ""),
                    "url": a.get("url", ""),
                    "publishedAt": a.get("publishedAt", "")[:10],
                    "description": a.get("description", "") or "",
                })
        except Exception as e:
            print(f"  ⚠️  뉴스 수집 실패 ({kw}): {e}")

    return results


def format_news_text(articles: list) -> str:
    if not articles:
        return "(수집된 뉴스 없음)"
    lines = []
    for a in articles:
        lines.append(
            f"- [{a['publishedAt']}] {a['title']} ({a['source']})\n"
            f"  {a['description'][:120] if a['description'] else ''}\n"
            f"  URL: {a['url']}"
        )
    return "\n".join(lines)
