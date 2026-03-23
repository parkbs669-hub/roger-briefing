"""
심평원 수집기 - 약가기준정보조회서비스
End Point: https://apis.data.go.kr/B551182/dgamtCrtrInfoService1.2
Operation: getDgamtList
응답형식: XML (서비스 기본값)
"""
import requests
import os
import datetime
import xml.etree.ElementTree as ET

API_KEY = (
    os.environ.get("HIRA_SERVICE_KEY") or
    os.environ.get("PUBLIC_DATA_API_KEY") or
    os.environ.get("G2B_API_KEY", "")
)

BASE_URL = "https://apis.data.go.kr/B551182/dgamtCrtrInfoService1.2/getDgamtList"

# ✅ 정확한 폐렴구균 백신 품목명만 검색 (일반 약품 제외)
KEYWORDS = ["프리베나", "신플로릭스", "뉴모박스", "캡박시브"]

# 최근 5년치만 수집
CUTOFF_YEAR = str(datetime.date.today().year - 5)


def collect_hira():
    all_items = []
    seen = set()

    for kw in KEYWORDS:
        try:
            items = _fetch_dgamt_list(kw)
            print(f"  HIRA '{kw}': {len(items)}건 수집")
            for item in items:
                key = item.get("itmCd") or item.get("itmNm", str(item)[:80])
                if key not in seen:
                    seen.add(key)
                    all_items.append(item)
        except Exception as e:
            print(f"  HIRA '{kw}' 오류: {e}")

    print(f"  HIRA 최종 수집: {len(all_items)}건 (중복제거)")
    return all_items


def _fetch_dgamt_list(keyword, num_of_rows=100):
    all_items = []
    page = 1

    while True:
        params = {
            "serviceKey": API_KEY,
            "pageNo": page,
            "numOfRows": num_of_rows,
            "itmNm": keyword,
        }

        resp = requests.get(BASE_URL, params=params, timeout=30)
        print(f"    HTTP {resp.status_code} | page={page} | kw='{keyword}'")
        resp.raise_for_status()

        text = resp.text.strip()
        if not text:
            break

        root = ET.fromstring(text)
        result_code = root.findtext(".//resultCode", "")
        result_msg  = root.findtext(".//resultMsg", "")
        print(f"    결과코드: {result_code} / {result_msg}")

        if result_code not in ("00", "0000", "OK"):
            break

        total_count_text = root.findtext(".//totalCount", "0")
        total_count = int(total_count_text) if total_count_text.isdigit() else 0

        items = root.findall(".//item")
        if not items:
            break

        for item_el in items:
            data = {child.tag: (child.text or "") for child in item_el}

            # ── 날짜 필터: 최근 5년 이내만 ──
            date_val = (
                data.get("adtStaDd") or
                data.get("aplYmd") or
                data.get("chgYmd") or ""
            )
            if date_val and len(date_val) >= 4:
                if date_val[:4] < CUTOFF_YEAR:
                    continue

            all_items.append(data)

        print(f"    누적: {len(all_items)}/{total_count}건")

        if len(all_items) >= total_count or len(items) < num_of_rows:
            break

        page += 1

    return all_items


def get_hira_summary(items):
    if not items:
        return {"total": 0, "note": "수집된 데이터 없음"}
    return {
        "total": len(items),
        "products": [
            {
                "name":    item.get("itmNm", ""),
                "company": item.get("mnfEntpNm", item.get("cpnyNm", "")),
                "price":   item.get("mxPatntAmt", ""),
                "applied": item.get("adtStaDd", item.get("aplYmd", "")),
            }
            for item in items[:10]
        ]
    }


if __name__ == "__main__":
    import json, logging
    logging.basicConfig(level=logging.INFO)
    result = collect_hira()
    print(json.dumps(get_hira_summary(result), ensure_ascii=False, indent=2))
