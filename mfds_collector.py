"""
식약처 수집기 - 의약품 국가출하승인정보
goods_name='폐렴구균' 으로 검색 (성분명 기준)
전체 페이지를 역순으로 순회하여 최신 데이터(2025년~) 수집
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

CUTOFF_YEAR   = "2025"   # 2025년 이후만 수집
NUM_OF_ROWS   = 100
MAX_ITEMS     = 20

VACCINE_KEYWORDS = ["폐렴", "프리베나", "신플로릭스", "뉴모박스", "캡박시브",
                    "pneumo", "prevnar", "synflorix", "PCV", "PPSV"]


def collect_mfds():
    all_items = []
    seen = set()

    # ── Step 1: 전체 건수 확인 ──
    params = {
        "serviceKey": API_KEY,
        "pageNo":     1,
        "numOfRows":  NUM_OF_ROWS,
        "goods_name": "폐렴구균",
    }
    try:
        resp = requests.get(URL, params=params, timeout=15)
        print(f"  MFDS '폐렴구균' HTTP: {resp.status_code}")
        text = resp.text.strip()
        if not text or not text.startswith("<"):
            print(f"  MFDS 비정상 응답: {text[:200]}")
            return []

        root = ET.fromstring(text)
        code = root.findtext(".//resultCode", "")
        msg  = root.findtext(".//resultMsg", "")
        print(f"  MFDS 결과: {code} / {msg}")
        if code not in ("00", "0000"):
            return []

        total_count = int(root.findtext(".//totalCount", "0") or 0)
        total_pages = (total_count + NUM_OF_ROWS - 1) // NUM_OF_ROWS
        print(f"  MFDS 전체 {total_count}건 / {total_pages}페이지 → 마지막 페이지부터 역순 탐색")

    except Exception as e:
        print(f"  MFDS 초기 조회 오류: {e}")
        return []

    # ── Step 2: 마지막 페이지부터 역순으로 탐색 (최신 데이터가 뒤에 있음) ──
    for page in range(total_pages, 0, -1):
        params["pageNo"] = page
        try:
            resp = requests.get(URL, params=params, timeout=15)
            text = resp.text.strip()
            if not text or not text.startswith("<"):
                continue

            root = ET.fromstring(text)
            items_found = root.findall(".//item")

            page_has_recent = False
            for item in items_found:
                data = {c.tag: (c.text or "") for c in item}

                result_time = data.get("RESULT_TIME", "")
                # 2025년 미만이면 이 페이지 이후는 더 오래됨 → 탐색 중단
                if result_time and result_time[:4] < CUTOFF_YEAR:
                    continue

                page_has_recent = True

                # 폐렴구균 백신 관련 항목만 수집
                sample_type = data.get("SAMPLE_TYPE", "").lower()
                goods_name  = data.get("GOODS_NAME", "").lower()
                combined    = sample_type + " " + goods_name
                if not any(vk.lower() in combined for vk in VACCINE_KEYWORDS):
                    continue

                key = data.get("RECEIPT_NO", "") or str(data)[:50]
                if key not in seen:
                    seen.add(key)
                    all_items.append(data)

            print(f"  MFDS page={page} → 누적 {len(all_items)}건")

            # 이 페이지에 2025년 이후 데이터가 하나도 없으면 그 앞 페이지도 없음
            if not page_has_recent and page < total_pages:
                print(f"  MFDS 2025년 이전 페이지 도달 → 탐색 중단")
                break

            if len(all_items) >= MAX_ITEMS:
                break

        except Exception as e:
            print(f"  MFDS page={page} 오류: {e}")
            continue

    # 최신순 정렬
    all_items.sort(key=lambda x: x.get("RESULT_TIME", ""), reverse=True)
    all_items = all_items[:MAX_ITEMS]

    print(f"  → {len(all_items)}건")
    return all_items
