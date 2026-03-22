"""
질병관리청 수집기 - 전수신고 감염병 발생현황
Base URL: https://apis.data.go.kr/1790387/EIDAPIService
오퍼레이션: /Disease, /PeriodBasic
"""
import requests
import os
import datetime
import json
import xml.etree.ElementTree as ET

API_KEY = (
    os.environ.get("PUBLIC_DATA_API_KEY") or
    os.environ.get("HIRA_SERVICE_KEY") or
    os.environ.get("G2B_API_KEY", "")
)

BASE_URL = "https://apis.data.go.kr/1790387/EIDAPIService"
PNEUMO_KEYWORDS = ["폐렴구균"]


def collect_kdca():
    today = datetime.date.today()
    year = today.strftime("%Y")
    prev_year = str(int(year) - 1)

    for op in ["/Disease", "/PeriodBasic", "/PeriodRegion", "/Gender"]:
        url = BASE_URL + op
        params = {
            "serviceKey": API_KEY,
            "pageNo": 1,
            "numOfRows": 100,
            "startCreateDt": prev_year + "0101",
            "endCreateDt": year + "1231",
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            print(f"  KDCA {op} HTTP: {resp.status_code}")
            if resp.status_code != 200:
                continue

            text = resp.text.strip()
            if not text:
                continue

            print(f"  KDCA {op} 응답 앞 100자: {text[:100]}")

            # JSON 파싱
            if text.startswith("{") or text.startswith("["):
                data = resp.json()
                # 다양한 응답 구조 처리
                # 구조 1: response.header.resultCode
                code = (data.get("response", {})
                            .get("header", {})
                            .get("resultCode", ""))
                # 구조 2: resultCode 직접
                if not code:
                    code = data.get("resultCode", "")
                # 구조 3: items 바로 존재
                if not code and ("items" in data or "item" in data):
                    code = "00"
                print(f"  KDCA {op} resultCode: '{code}'")

                # 결과코드 무관하게 items 추출 시도
                items = (
                    data.get("response", {}).get("body", {}).get("items", {})
                    or data.get("items", {})
                    or data.get("body", {}).get("items", {})
                    or {}
                )
                if isinstance(items, dict):
                    items = items.get("item", [])
                if isinstance(items, dict):
                    items = [items]
                items = items or []

                if items:
                    pneumo = [i for i in items if any(
                        kw in str(i) for kw in PNEUMO_KEYWORDS
                    )]
                    result = pneumo if pneumo else items[:5]
                    print(f"  KDCA {op} 전체: {len(items)}건, 폐렴구균: {len(pneumo)}건")
                    return result
                else:
                    print(f"  KDCA {op} items 없음, 전체 키: {list(data.keys())}")

            # XML 파싱
            elif text.startswith("<"):
                root = ET.fromstring(text)
                code = root.findtext(".//resultCode", "")
                print(f"  KDCA {op} XML resultCode: '{code}'")
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
            continue

    print("  KDCA 최종: 0건")
    return []
