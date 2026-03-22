"""
심평원 수집기 - 약가기준정보조회서비스
End Point: https://apis.data.go.kr/B551182/dgamtCrtrInfoService1.2
"""
import requests, os
import xml.etree.ElementTree as ET

API_KEY = os.environ.get("G2B_API_KEY", "")
BASE_URL = "https://apis.data.go.kr/B551182/dgamtCrtrInfoService1.2"

OPERATIONS = [
    "/getDrugPrdtPrceInq",
    "/getPriceList",
    "/getDrugPriceList",
    "/getList",
]

KEYWORDS = ["폐렴구균", "프리베나", "캡박시브", "뉴모"]
PARAM_NAMES = ["itemName", "ITEM_NAME", "drugNm", "prdctNm"]

def collect_hira():
    all_items = []
    seen = set()

    for op in OPERATIONS:
        url = BASE_URL + op
        for kw in KEYWORDS:
            for param in PARAM_NAMES:
                params = {
                    "serviceKey": API_KEY,
                    "pageNo":     1,
                    "numOfRows":  5,
                    param:        kw,
                }
                try:
                    resp = requests.get(url, params=params, timeout=15)
                    print(f"  HIRA {op[-20:]} '{kw}' HTTP: {resp.status_code}")

                    if resp.status_code != 200:
                        break

                    text = resp.text.strip()
                    if not text.startswith("<"):
                        break

                    root = ET.fromstring(text)
                    code = root.findtext(".//resultCode", "")
                    msg  = root.findtext(".//resultMsg", "")
                    print(f"  HIRA 결과: {code} / {msg}")

                    if code == "00":
                        for item in root.findall(".//item"):
                            data = {c.tag: (c.text or "") for c in item}
                            key = str(data)[:80]
                            if key not in seen:
                                seen.add(key)
                                all_items.append(data)
                        break

                except Exception as e:
                    print(f"  HIRA 오류: {e}")
                    break

            if all_items:
                return all_items

    return all_items
