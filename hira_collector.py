"""
심평원 수집기 - 약가기준정보조회서비스
End Point: https://apis.data.go.kr/B551182/dgamtCrtrInfoService1.2
Operation: getDgamtList
응답형식: XML (서비스 기본값)
"""

import requests
import os
import logging
import xml.etree.ElementTree as ET
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_URL = "https://apis.data.go.kr/B551182/dgamtCrtrInfoService1.2/getDgamtList"

API_KEY = (
        os.environ.get("HIRA_SERVICE_KEY") or
        os.environ.get("PUBLIC_DATA_API_KEY") or
        os.environ.get("G2B_API_KEY", "")
)

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
            getDgamtList 오퍼레이션 호출 - XML 응답 파싱
                """
    all_items = []
    page = 1

    while True:
                params = {
                    "serviceKey": API_KEY,
                    "pageNo":     page,
                    "numOfRows":  num_of_rows,
                    "itmNm":      keyword,  # JSON type 파라미터 제거 (XML 기본값 사용)
    }

        resp = requests.get(BASE_URL, params=params, timeout=30)
        print(f"    HTTP {resp.status_code} | page={page} | kw='{keyword}'")
        resp.raise_for_status()

        text = resp.text.strip()
        if not text:
                        print(f"    빈 응답")
                        break

        # XML 파싱
        root = ET.fromstring(text)

        # 결과코드 확인
        result_code = root.findtext(".//resultCode", "")
        result_msg  = root.findtext(".//resultMsg", "")
        print(f"    결과코드: {result_code} / {result_msg}")

        if result_code not in ("00", "0000", "OK"):
                        logger.warning(f"HIRA 오류 응답: {result_code} - {result_msg}")
                        break

        # totalCount
        total_count_text = root.findtext(".//totalCount", "0")
        total_count = int(total_count_text) if total_count_text.isdigit() else 0

        # item 목록 추출
        items = root.findall(".//item")
        if not items:
                        break

        for item_el in items:
                        data = {child.tag: (child.text or "") for child in item_el}
                        all_items.append(data)

        print(f"    누적: {len(all_items)}/{total_count}건")

        if len(all_items) >= total_count or len(items) < num_of_rows:
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
                                                    "price":   item.get("mxPatntAmt", ""),
                                                    "applied": item.get("aplYmd", ""),
                                }
                                for item in items[:10]
                ]
    }


if __name__ == "__main__":
        import json
    logging.basicConfig(level=logging.INFO)
    result = collect_hira()
    print(json.dumps(get_hira_summary(result), ensure_ascii=False, indent=2))
