"""
심평원 수집기 - 약가기준정보조회서비스
파라미터명 후보를 순서대로 시도하여 작동하는 것 확인
"""
import requests
import os
import xml.etree.ElementTree as ET

API_KEY = (
    os.environ.get("HIRA_SERVICE_KEY") or
    os.environ.get("PUBLIC_DATA_API_KEY") or
    os.environ.get("G2B_API_KEY", "")
)

BASE_URL = "https://apis.data.go.kr/B551182/dgamtCrtrInfoService1.2/getDgamtList"

VACCINE_KEYWORDS = ["엽산", "folate"]

# 검색 파라미터명 후보 (심평원 API는 문서와 실제가 다를 수 있음)
SEARCH_PARAM_CANDIDATES = ["itmNm", "itm_nm", "itemName", "item_name", "medNm", "drugNm"]


def collect_hira():
    all_items = []
    seen = set()

    # ── Step 1: 파라미터 없이 전체 조회로 DB 구조 파악 ──
    print("  [DEBUG] HIRA 전체 조회 시도 (파라미터 없이)...")
    try:
        params = {"serviceKey": API_KEY, "pageNo": 1, "numOfRows": 5}
        resp = requests.get(BASE_URL, params=params, timeout=30)
        print(f"  [DEBUG] 전체조회 HTTP: {resp.status_code}")
        text = resp.text.strip()
        root = ET.fromstring(text)
        total = root.findtext(".//totalCount", "0")
        items = root.findall(".//item")
        print(f"  [DEBUG] 전체조회 totalCount={total}, item 수={len(items)}")
        if items:
            sample = {c.tag: (c.text or "") for c in items[0]}
            print(f"  [DEBUG] 전체조회 필드명: {list(sample.keys())}")
            print(f"  [DEBUG] 전체조회 샘플값: {sample}")
    except Exception as e:
        print(f"  [DEBUG] 전체조회 오류: {e}")

    # ── Step 2: 파라미터명 후보 시도 ──
    working_param = None
    print(f"\n  [DEBUG] 파라미터명 후보 테스트 중...")
    for param_name in SEARCH_PARAM_CANDIDATES:
        try:
            params = {
                "serviceKey": API_KEY,
                "pageNo":     1,
                "numOfRows":  5,
                param_name:   "프리베나",
            }
            resp = requests.get(BASE_URL, params=params, timeout=15)
            text = resp.text.strip()
            root = ET.fromstring(text)
            total = int(root.findtext(".//totalCount", "0") or 0)
            print(f"  [DEBUG] '{param_name}'=프리베나 → totalCount={total}")
            if total > 0:
                working_param = param_name
                print(f"  [DEBUG] ✅ 작동하는 파라미터명: {param_name}")
                break
        except Exception as e:
            print(f"  [DEBUG] '{param_name}' 오류: {e}")

    if not working_param:
        print("  ⚠️  작동하는 파라미터명을 찾지 못함 → HIRA 수집 불가")
        return []

    # ── Step 3: 작동하는 파라미터로 실제 수집 ──
    for kw in VACCINE_KEYWORDS:
        try:
            params = {
                "serviceKey": API_KEY,
                "pageNo":     1,
                "numOfRows":  100,
                working_param: kw,
            }
            resp = requests.get(BASE_URL, params=params, timeout=30)
            text = resp.text.strip()
            root = ET.fromstring(text)
            total = int(root.findtext(".//totalCount", "0") or 0)
            items = root.findall(".//item")
            print(f"  HIRA '{kw}' [{working_param}] totalCount={total}, item={len(items)}")

            for item_el in items:
                data = {c.tag: (c.text or "") for c in item_el}
                key = data.get("itmCd") or data.get("itmNm", str(data)[:80])
                if key not in seen:
                    seen.add(key)
                    all_items.append(data)

        except Exception as e:
            print(f"  HIRA '{kw}' 오류: {e}")

    print(f"  HIRA 최종 수집: {len(all_items)}건 (중복제거)")
    print(f"  → {len(all_items)}건")
    return all_items
