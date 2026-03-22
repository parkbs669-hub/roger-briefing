"""
식약처 수집기 v2 - 의약품 국가출하승인정보
공식 확인된 정확한 URL 사용
"""
import requests
import xml.etree.ElementTree as ET
import os
import datetime

API_KEY = os.environ.get("G2B_API_KEY", "")

# 공식 확인된 정확한 URL
URL = "http://apis.data.go.kr/1471000/DrugNatnShipmntAprvInfoService/getDrugNatnShipmntAprvInfoInq"

def collect_mfds():
    """폐렴구균 백신 국가출하승인 수집"""
    keywords = ["폐렴구균", "프리베나", "캡박시브", "Prevnar", "Capvaxive"]
    all_items = []
    seen = set()

    for kw in keywords:
        params = {
            "ServiceKey":  API_KEY,
            "pageNo":      1,
            "numOfRows":   5,
            "prdctNm":     kw,
            "type":        "xml",
        }
        try:
            resp = requests.get(URL, params=params, timeout=15)
            print(f"  MFDS '{kw}' HTTP: {resp.status_code}")
            print(f"  MFDS 응답: {resp.text[:200]}")

            if not resp.text.strip().startswith("<"):
                continue

            root = ET.fromstring(resp.text)
            code = root.findtext(".//resultCode", "")
            msg  = root.findtext(".//resultMsg", "")
            print(f"  MFDS 결과: {code} / {msg}")

            if code != "00":
                continue

            for item in root.findall(".//item"):
                data = {child.tag: (child.text or "") for child in item}
                key = data.get("rcptNo", "") or data.get("prdctNm", "")
                if key not in seen:
                    seen.add(key)
                    all_items.append(data)

        except Exception as e:
            print(f"  MFDS 오류: {e}")

    return all_items
