"""
심평원 수집기 v2 - 약가기준 및 의약품 사용정보
공식 확인된 정확한 URL 사용
"""
import requests
import xml.etree.ElementTree as ET
import os

API_KEY = os.environ.get("G2B_API_KEY", "")

# 공식 확인된 정확한 URL
URL_PRICE = "https://apis.data.go.kr/B551182/msupUserInfoService1.2/getDrugPrdtPrceInq"
URL_USE   = "https://apis.data.go.kr/B551182/msupUserInfoService1.2/getDrugUseInfoInq"

def collect_hira():
    """폐렴구균 백신 약가 및 사용정보 수집"""
    keywords = ["폐렴구균", "프리베나", "캡박시브", "뉴모"]
    all_items = []
    seen = set()

    for kw in keywords:
        params = {
            "ServiceKey":  API_KEY,
            "pageNo":      1,
            "numOfRows":   5,
            "itemName":    kw,
            "type":        "xml",
        }
        try:
            resp = requests.get(URL_PRICE, params=params, timeout=15)
            print(f"  HIRA '{kw}' HTTP: {resp.status_code}")
            print(f"  HIRA 응답: {resp.text[:200]}")

            if not resp.text.strip().startswith("<"):
                continue

            root = ET.fromstring(resp.text)
            code = root.findtext(".//resultCode", "")
            msg  = root.findtext(".//resultMsg", "")
            print(f"  HIRA 결과: {code} / {msg}")

            if code != "00":
                continue

            for item in root.findall(".//item"):
                data = {child.tag: (child.text or "") for child in item}
                key = data.get("itemCode", "") or data.get("itemName", "")
                if key not in seen:
                    seen.add(key)
                    all_items.append(data)

        except Exception as e:
            print(f"  HIRA 오류: {e}")

    return all_items
