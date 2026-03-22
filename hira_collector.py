"""
심평원 수집기 - 약가기준정보조회서비스
End Point: https://apis.data.go.kr/B551182/dgamtCrtrInfoService1.2
Operation: getDgamtList (약가 목록 조회)
"""

import requests
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ✅ 실제 확인된 오퍼레이션 (1개)
BASE_URL = "https://apis.data.go.kr/B551182/dgamtCrtrInfoService1.2/getDgamtList"

# ✅ 프로젝트 공통 API 키 사용 (GitHub Secret: HIRA_SERVICE_KEY 또는 PUBLIC_DATA_API_KEY)
API_KEY = (
    os.environ.get("HIRA_SERVICE_KEY") or
    os.environ.get("PUBLIC_DATA_API_KEY") or
    os.environ.get("G2B_API_KEY", "")
)

# 폐렴구균 백신 검색 키워드
KEYWORDS = ["폐렴구균", "프리베나", "캡박시브", "뉴모박스", "뉴모"]


def collect_hira():
    """
    심평원 약가기준정보에서 폐렴구균 백신 데이터 수집
    Returns: list of item dicts
    """
    all_items = []
    seen = set()

    for kw in KEYWORDS:
        try:
            items = _fetch_dgamt_list(kw)
            logger.info(f"HIRA '{kw}': {len(items)}건 수집")
            print(f"  HIRA '{kw}': {len(items)}건 수집")

            for item in items:
                # itmCd(품목코드) 기준 중복 제거, 없으면 itmNm 사용
                key = item.get("itmCd") or item.get("itmNm", str(item)[:80])
                if key not in seen:
                    seen.add(key)
                    all_items.append(item)

        except Exception as e:
            logger.error(f"HIRA '{kw}' 오류: {e}")
            print(f"  HIRA '{kw}' 오류: {e}")

    print(f"  HIRA 최종 수집: {len(all_items)}건 (중복제거)")
    return all_items


def _fetch_dgamt_list(keyword: str, num_of_rows: int = 100) -> list:
    """
    getDgamtList 오퍼레이션 호출 (페이지네이션 포함)

    요청 파라미터:
        serviceKey  : 서비스키
        pageNo      : 페이지번호
        numOfRows   : 페이지당 결과수
        type        : 응답형식 (json)
        itmNm       : 품목명 (검색어)  ← 확인된 파라미터명
    """
    all_items = []
    page = 1

    while True:
        params = {
            "serviceKey": API_KEY,
            "pageNo":     page,
            "numOfRows":  num_of_rows,
            "type":       "json",   # JSON 응답 요청
            "itmNm":      keyword,  # ✅ 확인된 파라미터명
        }

        resp = requests.get(BASE_URL, params=params, timeout=30)
        print(f"    HTTP {resp.status_code} | page={page} | kw='{keyword}'")

        resp.raise_for_status()

        data = resp.json()

        # 응답 구조: response > body > items > item
        header      = data.get("response", {}).get("header", {})
        result_code = header.get("resultCode", "")
        result_msg  = header.get("resultMsg", "")
        print(f"    결과코드: {result_code} / {result_msg}")

        if result_code != "00":
            logger.warning(f"HIRA API 오류 응답: {result_code} - {result_msg}")
            break

        body        = data.get("response", {}).get("body", {})
        total_count = int(body.get("totalCount", 0))
        items_raw   = body.get("items")

        # items가 없거나 빈 경우
        if not items_raw:
            break

        # items > item 구조 처리 (단건이면 dict, 다건이면 list)
        item_list = items_raw.get("item", [])
        if isinstance(item_list, dict):
            item_list = [item_list]

        all_items.extend(item_list)

        # 페이지네이션 종료 조건
        if len(all_items) >= total_count or len(item_list) < num_of_rows:
            break

        page += 1

    return all_items


def get_hira_summary(items: list) -> dict:
    """수집 결과 요약 (브리핑용)"""
    if not items:
        return {"total": 0, "note": "수집된 데이터 없음"}

    return {
        "total":        len(items),
        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "products": [
            {
                "name":    item.get("itmNm", ""),
                "company": item.get("cpnyNm", ""),
                "price":   item.get("mxPatntAmt", ""),  # 최대환자부담금
                "applied": item.get("aplYmd", ""),       # 적용일자
            }
            for item in items[:10]  # 상위 10건만
        ]
    }


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    result = collect_hira()
    print(json.dumps(get_hira_summary(result), ensure_ascii=False, indent=2))
