"""
질병관리청 수집기 - 전수신고 감염병 발생현황
공식 참고문서 기반 정확한 파라미터 사용
End Point: https://apis.data.go.kr/1790387/EIDAPIService
오퍼레이션: getInfectDissOccrrncInfoList (기간별 감염병 발생 현황)
"""
import requests, os, datetime
import xml.etree.ElementTree as ET
import json

API_KEY = os.environ.get("G2B_API_KEY", "")
BASE_URL = "https://apis.data.go.kr/1790387/EIDAPIService"

def collect_kdca():
    today = datetime.date.today()
    year  = today.strftime("%Y")
    prev_year = str(int(year) - 1)

    # 공식 문서 확인된 정확한 파라미터
    params = {
        "serviceKey":       API_KEY,
        "resType":          "2",       # 1:xml, 2:json
        "searchPeriodType": "1",       # 1:연도별, 2:월별, 3:주별
        "searchStartYear":  prev_year,
        "searchEndYear":    year,
        "pageNo":           1,
        "numOfRows":        100,
    }

    # 오퍼레이션 목록 시도
    operations = [
        "/getInfectDissOccrrncInfoList",
        "/getInfectDissOccrrncInfo",
        "/getDissOccrrncInfoList",
    ]

    for op in operations:
        url = BASE_URL + op
        try:
            resp = requests.get(url, params=params, timeout=15)
            print(f"  KDCA {op} HTTP: {resp.status_code}")
            print(f"  KDCA 응답: {resp.text[:200]}")

            if resp.status_code != 200:
                continue

            # JSON 파싱
            try:
                data = resp.json()
                code = data.get("response",{}).get("header",{}).get("resultCode","")
                print(f"  KDCA JSON 결과코드: {code}")

                if code == "00":
                    items = data.get("response",{}).get("body",{}).get("items",{}).get("item",[])
                    if isinstance(items, dict):
                        items = [items]

                    # 폐렴구균 필터링
                    pneumo = [i for i in items if "폐렴구균" in str(i.get("icdNm",""))]
                    print(f"  KDCA 전체: {len(items)}건, 폐렴구균: {len(pneumo)}건")
                    return pneumo if pneumo else items[:10]

            except:
                pass

            # XML 파싱 시도 (resType=1)
            params2 = dict(params)
            params2["resType"] = "1"
            resp2 = requests.get(url, params=params2, timeout=15)
            if resp2.text.strip().startswith("<"):
                root = ET.fromstring(resp2.text)
                code = root.findtext(".//resultCode","")
                print(f"  KDCA XML 결과코드: {code}")
                if code == "00":
                    items = []
                    for item in root.findall(".//item"):
                        data = {c.tag:(c.text or "") for c in item}
                        if "폐렴구균" in data.get("icdNm",""):
                            items.append(data)
                    return items

        except Exception as e:
            print(f"  KDCA 오류: {e}")

    return []
