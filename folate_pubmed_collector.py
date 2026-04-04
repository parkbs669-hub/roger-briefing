import requests
import xml.etree.ElementTree as ET
import time

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def collect_pneumo_papers():
    queries = {
        "백신": "pneumococcal vaccine PCV20 PCV21",
        "영양제": "(folic acid OR iron supplementation) AND pregnancy AND 2026[pdat]"
    }
    all_papers, seen = [], set()

    for cat, q in queries.items():
        try:
            r = requests.get(f"{BASE}/esearch.fcgi",
                params={"db": "pubmed", "term": q, "retmax": 4, "sort": "date",
                        "retmode": "json", "datetype": "pdat", "reldate": 60}, timeout=15)
            ids = r.json().get("esearchresult", {}).get("idlist", [])
            if not ids: continue

            fr = requests.get(f"{BASE}/efetch.fcgi",
                params={"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}, timeout=15)
            time.sleep(0.5)
            root = ET.fromstring(fr.content.decode("utf-8-sig").strip())

            for art in root.findall(".//PubmedArticle"):
                pmid = art.findtext(".//PMID", "")
                if pmid in seen: continue
                seen.add(pmid)
                authors = [f"{a.findtext('LastName', '')} {a.findtext('ForeName', '')}".strip()
                           for a in art.findall(".//Author")[:3]]
                all_papers.append({
                    "category": cat,
                    "title": art.findtext(".//ArticleTitle", ""),
                    "journal": art.findtext(".//Title", ""),
                    "year": art.findtext(".//PubDate/Year", ""),
                    "authors": ", ".join(authors),
                    "pmid": pmid,
                    "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" # ✅ 링크 데이터 추가
                })
        except Exception as e:
            print(f"PubMed 오류: {e}")
            continue
    return all_papers[:10]
