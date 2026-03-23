"""
식약처 수집기 - 의약품 국가출하승인정보
goods_name 파라미터 = GOODS_NAME(성분명) 기준 검색
→ '폐렴구균'으로만 검색, 날짜 내림차순 정렬 후 최근 20건 수집
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

# goods_name = GOODS_NAME(성분명) 기준 → 폐렴구균만 유효
KEYWORDS = ["폐렴구균"]

# 표시에서 걸러낼 관련 백신 상품명 키워드 (SAMPLE_TYPE 기준)
VACCINE_KEYWORDS = ["폐렴", "프리베나", "신플로릭스", "뉴모박스", "캡박시브",
                    "pneumo", "prevnar", "synflorix", "PCV", "PPSV"]

MAX_ITEMS = 20  # 최근 20건만 표시


def collect_mfds():
    all_items = []
    seen = set()

    for kw in KEYWORDS:
        params = {
            "serviceKey": API_KEY,
            "pageNo":     1,
            "numOfRows":  100,
            "goods_name": kw,
        }
        try:
            resp = requests.get(URL, params=params, timeout=15)
            print(f"  MFDS '{kw}' HTTP: {resp.status_code}")
            text = resp.text.strip()

            if not text or not text.startswith("<"):
                print(f"  MFDS '{kw}' 비정상 응답: {text[:200]}")
                continue

            root = ET.fromstring(text)
            code = root.findtext(".//resultCode", "")
            msg  = root.findtext(".//resultMsg", "")
            print(f"  MFDS 결과: {code} / {msg}")

            if code not in ("00", "0000"):
                continue

            total_count = root.findtext(".//totalCount", "0")
            items_found = root.findall(".//item")
            print(f"  MFDS '{kw}' totalCount={total_count}, 이번 페이지={len(items_found)}건")

            for item in items_found:
                data = {c.tag: (c.text or "") for c in item}

                # SAMPLE_TYPE(상품명) 기준으로 폐렴구균 백신 필터링
                sample_type = data.get("SAMPLE_TYPE", "").lower()
                goods_name  = data.get("GOODS_NAME", "").lower()
                combined    = sample_type + " " + goods_name

                if not any(vk.lower() in combined for vk in VACCINE_KEYWORDS):
                    continue  # 폐렴구균 백신 무관 항목 제외

                key = data.get("RECEIPT_NO", "") or str(data)[:50]
                if key not in seen:
                    seen.add(key)
                    all_items.append(data)

        except ET.ParseError as e:
            print(f"  MFDS '{kw}' XML 파싱 오류: {e}")
        except Exception as e:
            print(f"  MFDS '{kw}' 오류: {e}")

    # RESULT_TIME 내림차순 정렬 → 최근 MAX_ITEMS건만
    all_items.sort(key=lambda x: x.get("RESULT_TIME", ""), reverse=True)
    all_items = all_items[:MAX_ITEMS]

    print(f"  → {len(all_items)}건")
    return all_items
