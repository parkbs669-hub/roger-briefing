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

CUTOFF_YEAR = str(datetime.date.today().year - 10)  # 최근 10년


def collect_mfds():
    all_items = []
    seen = set()

    for kw in KEYWORDS:
        # ── 파라미터명 후보 3가지 순서대로 시도 ──
        param_candidates = [
            {"serviceKey": API_KEY, "pageNo": 1, "numOfRows": 100, "goods_name": kw},
            {"serviceKey": API_KEY, "pageNo": 1, "numOfRows": 100, "GOODS_NM": kw},
            {"serviceKey": API_KEY, "pageNo": 1, "numOfRows": 100, "item_name": kw},
        ]

        success = False
        for params in param_candidates:
            param_key = [k for k in params if k not in ("serviceKey", "pageNo", "numOfRows")][0]
            try:
                resp = requests.get(URL, params=params, timeout=15)
                print(f"  MFDS '{kw}' [{param_key}] HTTP: {resp.status_code}")
                text = resp.text.strip()

                if not text or not text.startswith("<"):
                    print(f"  MFDS '{kw}' [{param_key}] 비정상 응답: {text[:200]}")
                    continue

                root = ET.fromstring(text)

                code = root.findtext(".//resultCode", "")
                msg  = root.findtext(".//resultMsg", "")
                print(f"  MFDS 결과: {code} / {msg}")

                if code not in ("00", "0000"):
                    continue

                # ── 디버그: totalCount 및 item 태그 수 확인 ──
                total_count = root.findtext(".//totalCount", "N/A")
                items_found = root.findall(".//item")
                print(f"  [DEBUG] '{kw}' [{param_key}] totalCount={total_count}, <item> 수={len(items_found)}")

                if len(items_found) == 0:
                    print(f"  [DEBUG] XML 샘플 (600자):\n{text[:600]}")
                    all_tags = sorted(set(el.tag for el in root.iter()))
                    print(f"  [DEBUG] 모든 태그: {all_tags}")
                    # 파라미터명 문제일 수 있으니 다음 후보 시도
                    continue

                # ── 디버그: 첫 번째 item 필드명 & 값 출력 ──
                first_item_data = {c.tag: (c.text or "") for c in items_found[0]}
                print(f"  [DEBUG] item 필드명: {list(first_item_data.keys())}")
                print(f"  [DEBUG] item 샘플값: {first_item_data}")

                # ── 아이템 수집 ──
                before = len(all_items)
                for item in items_found:
                    data = {c.tag: (c.text or "") for c in item}

                    # 날짜 필터: 최근 10년 이내만 수집
                    result_time = data.get("RESULT_TIME", "")
                    if result_time and len(result_time) >= 4:
                        if result_time[:4] < CUTOFF_YEAR:
                            continue

                    key = data.get("RECEIPT_NO", "") or str(data)[:50]
                    if key not in seen:
                        seen.add(key)
                        all_items.append(data)

                added = len(all_items) - before
                print(f"  MFDS '{kw}' [{param_key}] → 추가 {added}건 / 누적 {len(all_items)}건")
                success = True
                break  # 성공하면 다음 키워드로

            except ET.ParseError as e:
                print(f"  MFDS '{kw}' [{param_key}] XML 파싱 오류: {e}")
                print(f"  응답 원문 (200자): {resp.text[:200]}")
            except Exception as e:
                print(f"  MFDS '{kw}' [{param_key}] 오류: {e}")

        if not success:
            print(f"  ⚠️  MFDS '{kw}' → 모든 파라미터 후보 실패")

    print(f"  → {len(all_items)}건")
    return all_items
