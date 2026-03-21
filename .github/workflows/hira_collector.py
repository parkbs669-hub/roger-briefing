"""
심평원 수집기 - 약가기준 및 의약품 사용정보
"""
import requests
import xml.etree.ElementTree as ET
import os

API_KEY = os.environ.get("G2B_API_KEY", "")

# 약가기준 URL
URL_PRICE = "https://apis.data.go.kr/B551182/msupUserInfoService1.2/getDrugPrdtPrce"
# 의약품 사용정보 URL
URL_USE   = "https://apis.data.go.kr/B551182/msupUserInfoService1.2/getDrugUseInfo"

def collect_hira_price():
    """폐렴구균 백신 약가 정보 수집"""
    keywords = ["폐렴구균", "프리베나", "캡박시브", "뉴모"]
    all_items = []

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
            print(f"  HIRA 약가 '{kw}' HTTP: {resp.status_code}")
            print(f"  HIRA 응답: {resp.text[:150]}")

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
            print(f"  HIRA 약가 오류: {e}")

    return all_items


def collect_hira():
    """심평원 전체 수집"""
    price_data = collect_hira_price()
    return price_data
