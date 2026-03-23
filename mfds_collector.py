"""
식약처 수집기 - 의약품 국가출하승인정보
End Point: http://apis.data.go.kr/1471000/DrugNatnShipmntAprvInfoService
오퍼레이션: getDrugNatnShipmntAprvInfoInq
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

URL = "http://apis.data.go.kr/1471000/DrugNatnShipmntAprvInfoService/getDrugNatnShipmntAprvInfoInq"
KEYWORDS = ["폐렴구균", "프리베나", "캡박시브", "Prevnar", "Capvaxive"]

# 최근 3년치만 수집
CUTOFF_YEAR = str(datetime.date.today().year - 10)  # 최근 10년


def collect_mfds():
    all_items = []
    seen = set()

    for kw in KEYWORDS:
        params = {
            "serviceKey": API_KEY,
            "pageNo": 1,
            "numOfRows": 100,   # 넉넉히 가져와서 날짜 필터링
            "goods_name": kw,
        }
        try:
            resp = requests.get(URL, params=params, timeout=15)
            print(f"  MFDS '{kw}' HTTP: {resp.status_code}")

            text = resp.text.strip()
            if not text or not text.startswith("<"):
                print(f"  MFDS 응답: {text[:150]}")
                continue

            root = ET.fromstring(text)
            code = root.findtext(".//resultCode", "")
            msg  = root.findtext(".//resultMsg", "")
            print(f"  MFDS 결과: {code} / {msg}")

            if code not in ("00", "0000"):
                continue

            for item in root.findall(".//item"):
                data = {c.tag: (c.text or "") for c in item}

                # ── 날짜 필터: 최근 3년 이내만 수집 ──
                result_time = data.get("RESULT_TIME", "")
                if result_time and len(result_time) >= 4:
                    if result_time[:4] < CUTOFF_YEAR:
                        continue  # 오래된 데이터 제외

                key = data.get("RECEIPT_NO", "") or str(data)[:50]
                if key not in seen:
                    seen.add(key)
                    all_items.append(data)

            print(f"  MFDS '{kw}' → 누적 {len(all_items)}건 (최근 10년)")

        except Exception as e:
            print(f"  MFDS '{kw}' 오류: {e}")

    return all_items
