"""
PubMed 수집기 - 엽산(Folate) 연구 데이터
"""
import requests
import xml.etree.ElementTree as ET
import time

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def collect_folate_papers():
    # 엽산, 임산부 영양, 폴산 보충제 관련 키워드 설정
    queries = ["Folate supplementation pregnancy", "Folic acid fortification", "Folate deficiency health"]
    all_papers, seen = [], set()

    for q in queries:
        try:
            # 1. ID 검색 (최근 30일 이내의 최신 논문 3건씩 검색)
            r = requests.get(f"{BASE}/esearch.fcgi",
                params={
                    "db": "pubmed", 
                    "term": q, 
                    "retmax": 3, 
                    "sort": "date",
                    "retmode": "json", 
                    "datetype": "pdat", 
                    "reldate": 30
                },
                timeout=15)
            
            ids = r.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                continue

            # 2. 상세 정보 가져오기 (eFetch)
            fr = requests.get(f"{BASE}/efetch.fcgi",
                params={"db": "pubmed", "id": ",".join(ids), "retmode": "xml"},
                timeout=15)

            # API 부하 방지를 위한 짧은 대기
            time.sleep(0.5)

            xml_text = fr.content.decode("utf-8-sig").strip()

            # API 오류 응답 처리
            if xml_text.startswith("{"):
                print(f"  PubMed API 오류: {xml_text[:100]}")
                continue

            root = ET.fromstring(xml_text)

            for art in root.findall(".//PubmedArticle"):
                pmid = art.findtext(".//PMID", "")
                if pmid in seen:
                    continue
                seen.add(pmid)

                # 저자 정보 추출 (최대 3명)
                authors = [
                    f"{a.findtext('LastName', '')} {a.findtext('ForeName', '')}".strip()
                    for a in art.findall(".//Author")[:3]
                ]
                
                # 요약문 추출 및 정제
                abstract = art.findtext(".//AbstractText", "No abstract available.")
                
                all_papers.append({
                    "title":    art.findtext(".//ArticleTitle", "제목 없음"),
                    "abstract": abstract[:300] + "..." if len(abstract) > 300 else abstract,
                    "journal":  art.findtext(".//Title", "저널 미상"),
                    "year":     art.findtext(".//PubDate/Year", art.findtext(".//DateCompleted/Year", "2026")),
                    "authors":  ", ".join(authors) if authors else "저자 미상",
                    "pmid":     pmid,
                    "url":      f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                })

        except Exception as e:
            print(f"  PubMed 수집 중 오류 ('{q}'): {e}")

    print(f"  PubMed 엽산 논문 -> {len(all_papers)}건 수집 완료")
    return all_papers[:8] # 최대 8건 반환
