"""
PubMed 수집기 - 엽산(Folate/Folic Acid) 관련 최신 논문
"""
import requests
import xml.etree.ElementTree as ET

def collect_folate_papers():
    """
    PubMed에서 엽산(Folate) 관련 최신 논문 5건을 수집합니다.
    """
    # 엽산 관련 키워드로 검색 (최근 논문 위주)
    query = "(Folate[Title] OR Folic Acid[Title])"
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}&retmax=5&retmode=json"
    
    try:
        # 1. 논문 ID 목록 검색
        r = requests.get(search_url, timeout=15)
        id_list = r.json().get("esearchresult", {}).get("idlist", [])
        
        if not id_list:
            print("  PubMed: 검색 결과가 없습니다.")
            return []
        
        # 2. 검색된 ID들로 논문 상세 정보(Summary) 가져오기
        ids = ",".join(id_list)
        summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={ids}&retmode=xml"
        r_sum = requests.get(summary_url, timeout=15)
        root = ET.fromstring(r_sum.text)
        
        papers = []
        for doc in root.findall(".//DocSum"):
            # 데이터 추출
            title = doc.find(".//Item[@Name='Title']").text if doc.find(".//Item[@Name='Title']") is not None else "제목 없음"
            authors = doc.find(".//Item[@Name='Author']").text if doc.find(".//Item[@Name='Author']") is not None else "저자 미상"
            journal = doc.find(".//Item[@Name='Source']").text if doc.find(".//Item[@Name='Source']") is not None else "저널 미상"
            pub_date = doc.find(".//Item[@Name='PubDate']").text if doc.find(".//Item[@Name='PubDate']") is not None else ""
            pmid = doc.find("Id").text if doc.find("Id") is not None else ""
            
            papers.append({
                "title": title,
                "authors": authors,
                "journal": journal,
                "year": pub_date[:4], # 연도만 추출
                "pmid": pmid
            })
            
        print(f"  PubMed 수집 완료: {len(papers)}건")
        return papers

    except Exception as e:
        print(f"  PubMed 수집 중 오류 발생: {e}")
        return []
