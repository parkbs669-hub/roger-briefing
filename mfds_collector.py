"""
식약처 수집기 - 의약품 국가출하승인정보
End Point: https://apis.data.go.kr/1471000/DrugNatnShipmntAprvInfoService
"""
import requests, os
import xml.etree.ElementTree as ET

API_KEY = os.environ.get("G2B_API_KEY", "")
BASE_URL = "https://apis.data.go.kr/1471000/DrugNatnShipmntAprvInfoService"

OPERATIONS = [
    "/getDrugNatnShipmntAprvInfoInq",
    "/getNatnShipmntAprvList",
    "/getList",
]

KEYWORDS = ["폐렴구균", "프리베나", "캡박시브", "Prevnar", "Capvaxive"]
PARAM_NAMES = ["prdctNm", "PRDT_NM", "productName", "itemName"]

def collect_mfds():
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
                    print(f"  MFDS {op[-20:]} '{kw}' HTTP: {resp.status_code}")

                    if resp.status_code != 200:
                        break

                    text = resp.text.strip()
                    if not text.startswith("<"):
                        break

                    root = ET.fromstring(text)
                    code = root.findtext(".//resultCode", "")
                    msg  = root.findtext(".//resultMsg", "")
                    print(f"  MFDS 결과: {code} / {msg}")

                    if code == "00":
                        for item in root.findall(".//item"):
                            data = {c.tag: (c.text or "") for c in item}
                            key = str(data)[:80]
                            if key not in seen:
                                seen.add(key)
                                all_items.append(data)
                        break  # 성공한 파라미터 사용

                except Exception as e:
                    print(f"  MFDS 오류: {e}")
                    break

            if all_items:
                return all_items

    return all_items
