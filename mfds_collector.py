"""
식약처 수집기 - 의약품 국가출하승인정보
"""
import requests
import xml.etree.ElementTree as ET
import os
import datetime

API_KEY = os.environ.get("G2B_API_KEY", "")
URL = "https://apis.data.go.kr/1471000/NationalReleaseSvrc/getNationalReleaseList"

def collect_mfds():
    """폐렴구균 백신 국가출하승인 수집"""
    keywords = ["폐렴구균", "프리베나", "캡박시브"]
    all_items = []

    for kw in keywords:
        params = {
            "ServiceKey":  API_KEY,
            "pageNo":      1,
            "numOfRows":   5,
            "prdctName":   kw,
            "type":        "xml",
        }
        try:
            resp = requests.get(URL, params=params, timeout=15)
            print(f"  MFDS '{kw}' HTTP: {resp.status_code}")
            print(f"  MFDS 응답: {resp.text[:150]}")

            if not resp.text.strip().startswith("<"):
                continue

            root = ET.fromstring(resp.text)
            code = root.findtext(".//resultCode", "")
            if code != "00":
                continue

            for item in root.findall(".//item"):
                data = {child.tag: (child.text or "") for child in item}
                all_items.append(data)

        except Exception as e:
            print(f"  MFDS 오류: {e}")

    return all_items
