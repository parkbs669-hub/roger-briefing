"""
질병관리청 수집기 - 전수신고 감염병 발생현황
Base URL: https://apis.data.go.kr/1790387/EIDAPIService
오퍼레이션: /Disease (감염병별 감염병 발생 현황)
"""
import requests
import os
import datetime

API_KEY = (
    os.environ.get("PUBLIC_DATA_API_KEY") or
    os.environ.get("HIRA_SERVICE_KEY") or
    os.environ.get("G2B_API_KEY", "")
)

BASE_URL = "https://apis.data.go.kr/1790387/EIDAPIService"
PNEUMO_KEYWORDS = ["폐렴구균", "Streptococcus"]


def collect_kdca():
    today = datetime.date.today()
    year  = today.strftime("%Y")

    params = {
        "serviceKey": API_KEY,
        "resType":    "2",
        "searchType": "1",
        "searchYear": year,
        "patntType":  "1",
        "pageNo":     1,
        "numOfRows":  100,
    }
    url = BASE_URL + "/Disease"

    try:
        resp = requests.get(url, params=params, timeout=15)
        print(f"  KDCA /Disease HTTP: {resp.status_code}")
        text = resp.text.strip()
        print(f"  KDCA 응답: {text[:150]}")
        if not text:
            return []

        data = resp.json()
        code = (data.get("header", {}).get("resultCode", "") or
                data.get("response", {}).get("header", {}).get("resultCode", ""))
        msg  = (data.get("header", {}).get("resultMsg", "") or
                data.get("response", {}).get("header", {}).get("resultMsg", ""))
        print(f"  KDCA resultCode: '{code}' / {msg}")

        items = (
            data.get("body", {}).get("items", {}) or
            data.get("response", {}).get("body", {}).get("items", {}) or
            data.get("items", {}) or {}
        )
        if isinstance(items, dict):
            items = items.get("item", []) or []
        if isinstance(items, dict):
            items = [items]
        items = items or []

        print(f"  KDCA 전체: {len(items)}건")

        if items:
            pneumo = [i for i in items if any(kw in str(i) for kw in PNEUMO_KEYWORDS)]
            print(f"  KDCA 폐렴구균: {len(pneumo)}건")

            # ── 디버그: 월별 필드명 확인 ──
            sample = pneumo[0] if pneumo else items[0]
            print(f"  [DEBUG] item 전체 키: {list(sample.keys())}")
            print(f"  [DEBUG] item 전체 값: {sample}")

            return pneumo if pneumo else items[:5]

    except Exception as e:
        print(f"  KDCA /Disease 오류: {e}")

    # 전년도 재시도
    prev_year = str(int(year) - 1)
    params["searchYear"] = prev_year
    try:
        resp = requests.get(url, params=params, timeout=15)
        print(f"  KDCA /Disease ({prev_year}) HTTP: {resp.status_code}")
        text = resp.text.strip()
        if text:
            data = resp.json()
            items = (
                data.get("body", {}).get("items", {}) or
                data.get("response", {}).get("body", {}).get("items", {}) or {}
            )
            if isinstance(items, dict):
                items = items.get("item", []) or []
            if isinstance(items, dict):
                items = [items]
            items = items or []
            print(f"  KDCA ({prev_year}) 전체: {len(items)}건")
            if items:
                pneumo = [i for i in items if any(kw in str(i) for kw in PNEUMO_KEYWORDS)]
                print(f"  KDCA ({prev_year}) 폐렴구균: {len(pneumo)}건")

                sample = pneumo[0] if pneumo else items[0]
                print(f"  [DEBUG] item 전체 키: {list(sample.keys())}")
                print(f"  [DEBUG] item 전체 값: {sample}")

                return pneumo if pneumo else items[:5]
    except Exception as e:
        print(f"  KDCA ({prev_year}) 오류: {e}")

    print("  KDCA 최종: 0건")
    return []
