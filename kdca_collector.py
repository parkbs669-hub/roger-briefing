"""
질병관리청 수집기 - 전수신고 감염병 발생현황
End Point: https://apis.data.go.kr/1790387/EIDAPIService
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

# 가능한 오퍼레이션명 목록 (공식 확인된 순서대로)
OPERATIONS = [
    "/getInfSttsOccrrncInfoList",
    "/getInfectSttsOccrrncInfoList",
    "/getInfDissOccrrncInfoList",
    "/getInfSttsInfo",
    "/getInfectDissOccrrncInfoList",
    "/getInfectDissOccrrncInfo",
    "/getDissOccrrncInfoList",
]


def collect_kdca():
    today = datetime.date.today()
    year = today.strftime("%Y")
    prev_year = str(int(year) - 1)

    for op in OPERATIONS:
        url = BASE_URL + op
        # JSON 시도
        params = {
            "serviceKey": API_KEY,
            "pageNo": 1,
            "numOfRows": 100,
            "resType": "2",
            "searchStartYear": prev_year,
            "searchEndYear": year,
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            print(f"  KDCA {op} HTTP: {resp.status_code}")

            if resp.status_code == 404:
                continue

            text = resp.text.strip()
            if not text:
                continue

            # JSON 파싱 시도
            if text.startswith("{") or text.startswith("["):
                data = resp.json()
                header = data.get("response", {}).get("header", {})
                code = header.get("resultCode", "")
                print(f"  KDCA JSON 결과코드: {code}")
                if code == "00":
                    items = data.get("response", {}).get("body", {}).get("items", {})
                    if isinstance(items, dict):
                        items = items.get("item", [])
                    if isinstance(items, dict):
                        items = [items]
                    pneumo = [i for i in (items or []) if "폐렴구균" in str(i.get("icdNm", ""))]
                    result = pneumo if pneumo else (items or [])[:10]
                    print(f"  KDCA 전체: {len(items or [])}건, 폐렴구균: {len(pneumo)}건")
                    return result

            # XML 파싱 시도
            elif text.startswith("<"):
                root = ET.fromstring(text)
                code = root.findtext(".//resultCode", "")
                print(f"  KDCA XML 결과코드: {code}")
                if code in ("00", "0000"):
                    items = []
                    for item in root.findall(".//item"):
                        d = {c.tag: (c.text or "") for c in item}
                        if "폐렴구균" in d.get("icdNm", ""):
                            items.append(d)
                    print(f"  KDCA 폐렴구균: {len(items)}건")
                    return items

        except Exception as e:
            print(f"  KDCA {op} 오류: {e}")
            continue

    print("  KDCA: 유효한 오퍼레이션 없음")
    return []
