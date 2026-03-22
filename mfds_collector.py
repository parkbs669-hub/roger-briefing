"""
식약처 수집기 v3 - 의약품 국가출하승인정보
공식 확인된 정확한 URL 사용
"""
import requests
import xml.etree.ElementTree as ET
import os

API_KEY = os.environ.get("G2B_API_KEY", "")

# 공식 확인된 정확한 URL
URL = "http://apis.data.go.kr/1471000/DrugNatnShipmntAprvInfoService/getDrugNatnShipmntAprvInfoInq"

def collect_mfds():
    """폐렴구균 백신 국가출하승인 수집"""
    keywords = ["폐렴구균", "프리베나", "캡박시브", "Prevnar", "pneumococcal"]
    all_items = []
    seen = set()

    for kw in keywords:
        # 파라미터명 변경 (prdctNm → prdctName)
        for param_name in ["prdctNm", "prdctName", "PRDT_NM"]:
            params = {
                "serviceKey": API_KEY,
                "pageNo":     1,
                "numOfRows":  5,
                param_name:   kw,
                "type":       "xml",
            }
            try:
                resp = requests.get(URL, params=params, timeout=15)
                print(f"  MFDS '{kw}' HTTP: {resp.status_code}")

                if not resp.text.strip().startswith("<"):
                    continue

                root = ET.fromstring(resp.text)
                code = root.findtext(".//resultCode", "")
                msg  = root.findtext(".//resultMsg", "")
                print(f"  MFDS 결과: {code} / {msg}")

                if code == "00":
                    for item in root.findall(".//item"):
                        data = {child.tag: (child.text or "") for child in item}
                        key = data.get("rcptNo","") or data.get("prdctNm","") or str(data)[:50]
                        if key not in seen:
                            seen.add(key)
                            all_items.append(data)
                    break  # 성공한 파라미터명 사용

            except Exception as e:
                print(f"  MFDS 오류: {e}")
                continue

    return all_items
