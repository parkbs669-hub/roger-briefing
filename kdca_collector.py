"""
질병관리청 수집기 - 전수신고 감염병 발생현황
Base URL: https://apis.data.go.kr/1790387/EIDAPIService
오퍼레이션: /Disease (감염병별 발생현황)
"""
import requests
import os
import json
import xml.etree.ElementTree as ET

API_KEY = (
    os.environ.get("PUBLIC_DATA_API_KEY") or
    os.environ.get("HIRA_SERVICE_KEY") or
    os.environ.get("G2B_API_KEY", "")
)

BASE_URL = "https://apis.data.go.kr/1790387/EIDAPIService"
PNEUMO_KEYWORDS = ["폐렴구균", "Streptococcus"]


def collect_kdca():
    # 파라미터 조합별 시도 (날짜 파라미터 없이 시작)
    param_sets = [
        # 1) 날짜 없이 기본 조회
        {"serviceKey": API_KEY, "pageNo": 1, "numOfRows": 100},
        # 2) 연도 파라미터
        {"serviceKey": API_KEY, "pageNo": 1, "numOfRows": 100, "year": "2025"},
        # 3) 기간 파라미터 (다른 형식)
        {"serviceKey": API_KEY, "pageNo": 1, "numOfRows": 100,
         "startYearMonth": "202501", "endYearMonth": "202503"},
        # 4) 연도범위
        {"serviceKey": API_KEY, "pageNo": 1, "numOfRows": 100,
         "startYear": "2025", "endYear": "2026"},
    ]

    for op in ["/Disease", "/PeriodBasic", "/Gender"]:
        url = BASE_URL + op
        for params in param_sets:
            try:
                resp = requests.get(url, params=params, timeout=15)
                print(f"  KDCA {op} HTTP: {resp.status_code} | params: {list(params.keys())[-1] if len(params) > 3 else '기본'}")

                if resp.status_code != 200:
                    break

                text = resp.text.strip()
                if not text:
                    continue

                print(f"  KDCA {op} 응답: {text[:120]}")

                # JSON 파싱
                if text.startswith("{") or text.startswith("["):
                    data = resp.json()
                    # resultCode 추출
                    code = (data.get("response", {})
                                .get("header", {})
                                .get("resultCode", ""))
                    msg = (data.get("response", {})
                               .get("header", {})
                               .get("resultMsg", ""))
                    print(f"  KDCA resultCode: '{code}' / {msg}")

                    if code == "104":  # 파라미터 오류 → 다음 파라미터 셋 시도
                        continue

                    # items 추출 시도
                    items = (
                        data.get("response", {}).get("body", {}).get("items", {})
                        or data.get("items", {})
                        or {}
                    )
                    if isinstance(items, dict):
                        items = items.get("item", []) or []
                    if isinstance(items, dict):
                        items = [items]
                    items = items or []

                    if items:
                        pneumo = [i for i in items if any(
                            kw in str(i) for kw in PNEUMO_KEYWORDS
                        )]
                        print(f"  KDCA 전체: {len(items)}건, 폐렴구균: {len(pneumo)}건")
                        return pneumo if pneumo else items[:5]
                    else:
                        print(f"  KDCA items 없음, keys: {list(data.keys())[:5]}")
                        # 결과는 있는데 items만 없으면 다음 파라미터 시도
                        if code == "00":
                            break

                # XML 파싱
                elif text.startswith("<"):
                    root = ET.fromstring(text)
                    code = root.findtext(".//resultCode", "")
                    msg = root.findtext(".//resultMsg", "")
                    print(f"  KDCA XML resultCode: '{code}' / {msg}")
                    if code == "104":
                        continue
                    all_items = []
                    for item in root.findall(".//item"):
                        d = {c.tag: (c.text or "") for c in item}
                        all_items.append(d)
                    if all_items:
                        pneumo = [i for i in all_items if any(
                            kw in str(i) for kw in PNEUMO_KEYWORDS
                        )]
                        print(f"  KDCA XML 전체: {len(all_items)}건, 폐렴구균: {len(pneumo)}건")
                        return pneumo if pneumo else all_items[:5]

            except Exception as e:
                print(f"  KDCA {op} 오류: {e}")
                break

    print("  KDCA 최종: 0건")
    return []
