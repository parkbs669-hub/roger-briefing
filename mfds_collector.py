"""
식약처 수집기 - 의약품 국가출하승인정보
공식 참고문서 기반 정확한 파라미터 사용
End Point: http://apis.data.go.kr/1471000/DrugNatnShipmntAprvInfoService
오퍼레이션: getDrugNatnShipmntAprvInfoInq
파라미터: goods_name (제품명), manuf_entp_name (제조수입업자)
"""
import requests, os
import xml.etree.ElementTree as ET

API_KEY = os.environ.get("G2B_API_KEY", "")
URL = "http://apis.data.go.kr/1471000/DrugNatnShipmntAprvInfoService/getDrugNatnShipmntAprvInfoInq"

def collect_mfds():
    keywords = ["폐렴구균", "프리베나", "캡박시브", "Prevnar", "Capvaxive"]
    all_items = []
    seen = set()

    for kw in keywords:
        params = {
            "serviceKey": API_KEY,
            "pageNo":     1,
            "numOfRows":  5,
            "type":       "xml",
            "goods_name": kw,       # ← 공식 파라미터명 확인!
        }
        try:
            resp = requests.get(URL, params=params, timeout=15)
            print(f"  MFDS '{kw}' HTTP: {resp.status_code}")

            if not resp.text.strip().startswith("<"):
                print(f"  MFDS 응답: {resp.text[:100]}")
                continue

            root = ET.fromstring(resp.text)
            code = root.findtext(".//resultCode", "")
            msg  = root.findtext(".//resultMsg", "")
            print(f"  MFDS 결과: {code} / {msg}")

            if code == "00":
                for item in root.findall(".//item"):
                    data = {c.tag: (c.text or "") for c in item}
                    key = data.get("RECEIPT_NO", "") or str(data)[:50]
                    if key not in seen:
                        seen.add(key)
                        all_items.append(data)
                print(f"  MFDS '{kw}' → {len(all_items)}건")

        except Exception as e:
            print(f"  MFDS 오류: {e}")

    return all_items
