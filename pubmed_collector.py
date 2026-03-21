"""
PubMed 논문 수집기 - 폐렴구균 최신 논문
"""
import requests
import xml.etree.ElementTree as ET
import datetime

PUBMED_API_KEY = ""  # 없어도 작동, 있으면 더 빠름
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def search_pubmed(query, max_results=5):
    """PubMed 논문 검색"""
    # 1단계: ID 검색
    search_url = f"{BASE_URL}/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "sort": "date",
        "retmode": "json",
        "datetype": "pdat",
        "reldate": 30,  # 최근 30일
    }
    if PUBMED_API_KEY:
        params["api_key"] = PUBMED_API_KEY

    try:
        resp = requests.get(search_url, params=params, timeout=15)
        data = resp.json()
        ids = data.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []

        # 2단계: 상세 정보 가져오기
        fetch_url = f"{BASE_URL}/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml",
        }
        fetch_resp = requests.get(fetch_url, params=fetch_params, timeout=15)
        root = ET.fromstring(fetch_resp.text)

        papers = []
        for article in root.findall(".//PubmedArticle"):
            title = article.findtext(".//ArticleTitle", "")
            abstract = article.findtext(".//AbstractText", "")
            journal = article.findtext(".//Title", "")
            year = article.findtext(".//PubDate/Year", "")
            month = article.findtext(".//PubDate/Month", "")

            # 저자
            authors = []
            for author in article.findall(".//Author")[:3]:
                last = author.findtext("LastName", "")
                fore = author.findtext("ForeName", "")
                if last:
                    authors.append(f"{last} {fore}".strip())
            author_str = ", ".join(authors)
            if len(article.findall(".//Author")) > 3:
                author_str += " et al."

            pmid = article.findtext(".//PMID", "")

            papers.append({
                "title": title,
                "abstract": abstract[:300] + "..." if len(abstract) > 300 else abstract,
                "journal": journal,
                "year": year,
                "month": month,
                "authors": author_str,
                "pmid": pmid,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })
        return papers

    except Exception as e:
        print(f"  PubMed 오류: {e}")
        return []


def collect_pneumo_papers():
    """폐렴구균 관련 최신 논문 수집"""
    queries = [
        "pneumococcal vaccine PCV20 PCV21",
        "pneumococcal vaccine adult immunization",
        "Streptococcus pneumoniae Korea",
    ]
    all_papers = []
    for q in queries:
        print(f"  🔍 PubMed 검색: {q}")
        papers = search_pubmed(q, max_results=3)
        all_papers.extend(papers)
        print(f"     → {len(papers)}건 발견")

    # 중복 제거 (PMID 기준)
    seen = set()
    unique = []
    for p in all_papers:
        if p["pmid"] not in seen:
            seen.add(p["pmid"])
            unique.append(p)

    return unique[:10]  # 최대 10건
