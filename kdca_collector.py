"""
질병관리청 수집기 v3 - 전수신고 감염병 발생현황
공식 확인된 정확한 URL 사용
"""
import requests
import xml.etree.ElementTree as ET
import os
import datetime

API_KEY = os.environ.get("G2B_API_KEY", "")

# 공식 확인된 URL들 (순서대로 시도)
URLS = [
    "https://apis.data.go.kr/1790387/incidntOccrrncInfoInq/getIncidntOccrrncInfoList",
    "https://apis.data.go.kr/B552657/InfectnDissOccrrncInfoInq/getInfectnDissOccrrncInfoList",
]

def collect_kdca():
    """폐렴구균 감염병 발생현황 수집"""
    today = datetime.date.today()
    year  = today.strftime("%Y")

    for url in URLS:
        params = {
            "serviceKey": API_KEY,
            "pageNo":     1,
            "numOfRows":  10,
            "year":       year,
            "diseaseNm":  "폐렴구균",
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            print(f"  KDCA HTTP: {resp.status_code} | URL: {url[-50:]}")

            if resp.status_code != 200:
                continue

            # XML 파싱
            if resp.text.strip().startswith("<"):
                root = ET.fromstring(resp.text)
                code = root.findtext(".//resultCode", "")
                msg  = root.findtext(".//resultMsg", "")
                print(f"  KDCA 결과: {code} / {msg}")

                if code == "00":
                    items = []
                    for item in root.findall(".//item"):
                        data = {child.tag: (child.text or "") for child in item}
                        items.append(data)
                    if items:
                        return items
            # JSON 파싱
            else:
                data = resp.json()
                items = data.get("response", {}).get("body", {}).get("items", [])
                if items:
                    return items if isinstance(items, list) else [items]

        except Exception as e:
            print(f"  KDCA 오류: {e}")
            continue

    print("  KDCA: 모든 URL 실패 → 빈 결과")
    return []
