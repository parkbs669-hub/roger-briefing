"""
질병관리청 수집기 - 전수신고 감염병 발생현황
Base URL: https://apis.data.go.kr/1790387/EIDAPIService
오퍼레이션: /Disease (감염병별 감염병 발생 현황)
"""
import requests
import os
import datetime
import xml.etree.ElementTree as ET

API_KEY = (
    os.environ.get("PUBLIC_DATA_API_KEY") or
    os.environ.get("HIRA_SERVICE_KEY") or
    os.environ.get("G2B_API_KEY", "")
)

BASE_URL = "https://apis.data.go.kr/1790387/EIDAPIService"

# 폐렴구균 질병코드 (ICD-10: A40.3 폐렴구균 패혈증, J13 폐렴구균폐렴)
PNEUMO_KEYWORDS = ["폐렴구균", "Streptococcus pneumoniae"]


def collect_kdca():
    today = datetime.date.today()
    year = today.strftime("%Y")
    prev_year = str(int(year) - 1)

    results = []

    # /Disease 오퍼레이션: 감염병별 발생 현황
    for op in ["/Disease", "/PeriodBasic", "/PeriodRegion"]:
        url = BASE_URL + op
        params = {
            "serviceKey": API_KEY,
            "pageNo": 1,
            "numOfRows": 100,
            "startCreateDt": prev_year + "0101",
            "endCreateDt": year + "1231",
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            print(f"  KDCA {op} HTTP: {resp.status_code}")

            if resp.status_code != 200:
                continue

            text = resp.text.strip()
            if not text:
                continue

            # JSON 파싱 시도
            if text.startswith("{") or text.startswith("["):
                data = resp.json()
                header = data.get("response", {}).get("header", {})
                code = header.get("resultCode", "")
                print(f"  KDCA {op} JSON 결과코드: {code}")
                if code == "00":
                    body = data.get("response", {}).get("body", {})
                    items = body.get("items", {})
                    if isinstance(items, dict):
                        items = items.get("item", [])
                    if isinstance(items, dict):
                        items = [items]
                    items = items or []
                    # 폐렴구균 필터
                    pneumo = [i for i in items if any(
                        kw in str(i.get("diseaseNm", "")) or
                        kw in str(i.get("icdNm", "")) or
                        kw in str(i.get("diseaseCd", ""))
                        for kw in PNEUMO_KEYWORDS
                    )]
                    print(f"  KDCA {op} 전체: {len(items)}건, 폐렴구균: {len(pneumo)}건")
                    if items:
                        results.extend(pneumo if pneumo else items[:5])
                        return results

            # XML 파싱 시도
            elif text.startswith("<"):
                root = ET.fromstring(text)
                code = root.findtext(".//resultCode", "")
                print(f"  KDCA {op} XML 결과코드: {code}")
                if code in ("00", "0000"):
                    items = []
                    for item in root.findall(".//item"):
                        d = {c.tag: (c.text or "") for c in item}
                        items.append(d)
                    pneumo = [i for i in items if any(
                        kw in str(i.get("diseaseNm", "")) or
                        kw in str(i.get("icdNm", ""))
                        for kw in PNEUMO_KEYWORDS
                    )]
                    print(f"  KDCA {op} XML 전체: {len(items)}건, 폐렴구균: {len(pneumo)}건")
                    if items:
                        results.extend(pneumo if pneumo else items[:5])
                        return results

        except Exception as e:
            print(f"  KDCA {op} 오류: {e}")
            continue

    print(f"  KDCA 최종: {len(results)}건")
    return results
