# Google News RSS + PubMed E-utilities 기반 뉴스/논문 수집 모듈
# (기존 NewsAPI.org 대체 — API 키 불필요, GitHub Actions 서버 사용 허용)
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))


# ──────────────────────────────────────────────
# 1. Google News RSS (영문/한국어 뉴스 수집)
# ──────────────────────────────────────────────
def collect_google_news(keywords: list, days: int = 7, max_per_kw: int = 3) -> list:
    """Google News RSS로 키워드별 최신 뉴스를 수집한다. API 키 불필요."""
    results = []
    try:
        import feedparser
    except ImportError:
        print("  ⚠️  feedparser 미설치 — Google News 수집 생략")
        return results

    for kw in keywords:
        try:
            encoded = urllib.parse.quote(f'{kw} when:{days}d')
            rss_url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:max_per_kw]:
                source = ""
                if hasattr(entry, "source") and hasattr(entry.source, "title"):
                    source = entry.source.title
                results.append({
                    "keyword": kw,
                    "title": entry.get("title", ""),
                    "source": source,
                    "url": entry.get("link", ""),
                    "publishedAt": entry.get("published", "")[:16],
                    "description": entry.get("summary", "")[:200] if entry.get("summary") else "",
                })
        except Exception as e:
            print(f"  ⚠️  Google News 수집 실패 ({kw}): {e}")

    return results


def collect_google_news_kr(keywords_kr: list, days: int = 7, max_per_kw: int = 3) -> list:
    """한국어 Google News RSS 수집."""
    results = []
    try:
        import feedparser
    except ImportError:
        return results

    for kw in keywords_kr:
        try:
            encoded = urllib.parse.quote(f'{kw} when:{days}d')
            rss_url = f"https://news.google.com/rss/search?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:max_per_kw]:
                source = ""
                if hasattr(entry, "source") and hasattr(entry.source, "title"):
                    source = entry.source.title
                results.append({
                    "keyword": kw,
                    "title": entry.get("title", ""),
                    "source": source,
                    "url": entry.get("link", ""),
                    "publishedAt": entry.get("published", "")[:16],
                    "description": entry.get("summary", "")[:200] if entry.get("summary") else "",
                })
        except Exception as e:
            print(f"  ⚠️  한국 뉴스 수집 실패 ({kw}): {e}")

    return results


# ──────────────────────────────────────────────
# 2. PubMed E-utilities (최신 학술 논문 수집)
# ──────────────────────────────────────────────
def collect_pubmed(query: str, days: int = 7, max_results: int = 5) -> list:
    """PubMed ESearch + ESummary로 최근 논문을 수집한다. API 키 불필요."""
    results = []
    try:
        # Step 1: ESearch — 최근 N일 이내 논문 PMID 검색
        search_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pubmed&term={urllib.parse.quote(query)}&retmax={max_results}"
            f"&datetype=edat&reldate={days}&retmode=json"
            f"&tool=roger-briefing&email=parkbs669@naver.com"
        )
        req = urllib.request.Request(search_url, headers={"User-Agent": "roger-briefing/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            ids = data.get("esearchresult", {}).get("idlist", [])

        if not ids:
            return results

        # Step 2: ESummary — 논문 메타데이터 가져오기
        summary_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            f"?db=pubmed&id={','.join(ids)}&retmode=json"
            f"&tool=roger-briefing&email=parkbs669@naver.com"
        )
        req2 = urllib.request.Request(summary_url, headers={"User-Agent": "roger-briefing/1.0"})
        with urllib.request.urlopen(req2, timeout=15) as r:
            summary_data = json.loads(r.read()).get("result", {})

        for pmid in ids:
            article = summary_data.get(pmid, {})
            if not isinstance(article, dict):
                continue
            # 저자 목록 처리
            authors = article.get("authors", [])
            author_str = ", ".join(a.get("name", "") for a in authors[:3]) if authors else ""
            if len(authors) > 3:
                author_str += " et al."

            results.append({
                "pmid": pmid,
                "title": article.get("title", ""),
                "journal": article.get("fulljournalname", "") or article.get("source", ""),
                "pubdate": article.get("pubdate", ""),
                "authors": author_str,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })

    except Exception as e:
        print(f"  ⚠️  PubMed 수집 실패 ({query}): {e}")

    return results


# ──────────────────────────────────────────────
# 3. 포맷팅 함수
# ──────────────────────────────────────────────
def format_news_text(articles: list) -> str:
    """뉴스 기사 목록을 텍스트로 포맷팅 (기존 인터페이스 유지)."""
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


def format_pubmed_text(articles: list) -> str:
    """PubMed 논문 목록을 텍스트로 포맷팅."""
    if not articles:
        return "(최근 7일 이내 관련 PubMed 논문 없음)"
    lines = []
    for a in articles:
        lines.append(
            f"- [{a['pubdate']}] {a['title']}\n"
            f"  저널: {a['journal']} | 저자: {a['authors']}\n"
            f"  URL: {a['url']}"
        )
    return "\n".join(lines)


# ──────────────────────────────────────────────
# 4. 하위 호환용 래퍼 (기존 코드에서 collect_news 호출 시)
# ──────────────────────────────────────────────
def collect_news(keywords: list, api_key: str = "", days: int = 7, page_size: int = 3) -> list:
    """하위 호환 래퍼 — Google News RSS로 대체. api_key 파라미터는 무시됨."""
    return collect_google_news(keywords, days=days, max_per_kw=page_size)
