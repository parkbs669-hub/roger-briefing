"""PubMed 수집기"""
import requests
import xml.etree.ElementTree as ET

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def collect_pneumo_papers():
    queries = ["pneumococcal vaccine PCV20 PCV21", "pneumococcal vaccine adult Korea"]
    all_papers, seen = [], set()

    for q in queries:
        try:
            r = requests.get(f"{BASE}/esearch.fcgi",
                params={"db": "pubmed", "term": q, "retmax": 3, "sort": "date",
                        "retmode": "json", "datetype": "pdat", "reldate": 30},
                timeout=15)
            ids = r.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                continue

            fr = requests.get(f"{BASE}/efetch.fcgi",
                params={"db": "pubmed", "id": ",".join(ids), "retmode": "xml"},
                timeout=15)

            import time
            time.sleep(1)

            xml_text = fr.content.decode("utf-8-sig").strip()

            # JSON 오류 응답 확인 (rate limit 등)
            if xml_text.startswith("{"):
                print(f"  PubMed API 오류: {xml_text[:100]}")
                continue

            root = ET.fromstring(xml_text)

            for art in root.findall(".//PubmedArticle"):
                pmid = art.findtext(".//PMID", "")
                if pmid in seen:
                    continue
                seen.add(pmid)
                authors = [
                    f"{a.findtext('LastName', '')} {a.findtext('ForeName', '')}".strip()
                    for a in art.findall(".//Author")[:3]
                ]
                abstract = art.findtext(".//AbstractText", "")
                all_papers.append({
                    "title":    art.findtext(".//ArticleTitle", ""),
                    "abstract": abstract[:300] + "..." if len(abstract) > 300 else abstract,
                    "journal":  art.findtext(".//Title", ""),
                    "year":     art.findtext(".//PubDate/Year", ""),
                    "authors":  ", ".join(authors),
                    "pmid":     pmid,
                    "url":      f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                })

        except Exception as e:
            print(f"  PubMed 오류: {e}")

    print(f"  PubMed -> {len(all_papers)}건")
    return all_papers[:8]
