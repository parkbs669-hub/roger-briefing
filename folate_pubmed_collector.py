"""
PubMed 수집기 - 엽산(Folate/Folic Acid) 관련 최신 논문
"""
import requests
import xml.etree.ElementTree as ET

def collect_folate_papers():
    # 엽산 관련 키워드로 검색 (최근 7일)
    query = "(Folate OR Folic Acid) AND 2024[PDAT] : 2026[PDAT]"
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}&retmax=5&retmode=json"
    
    try:
        r = requests.get(search_url, timeout=15)
        id_list = r.json().get("esearchresult", {}).get("idlist", [])
        if not id_list: return []
        
        ids = ",".join(id_list)
        summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={ids}&retmode=xml"
        r_sum = requests.get(summary_url, timeout=15)
        root = ET.fromstring(r_sum.text)
        
        papers = []
        for doc in root.findall(".//DocSum"):
            papers.append({
                "title": doc.find(".//Item[@Name='Title']").text,
                "authors": doc.find(".//Item[@Name='Author']").text if doc.find(".//Item[@Name='Author']") is not None else "Unknown",
                "journal": doc.find(".//Item[@Name='Source']").text,
                "year": doc.find(".//Item[@Name='PubDate']").text[:4],
                "pmid": doc.find("Id").text
            })
        return papers
    except Exception as e:
        print(f"PubMed 오류: {e}")
        return []
