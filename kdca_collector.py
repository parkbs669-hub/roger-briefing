"""
질병관리청 수집기 - 전수신고 감염병 발생현황
End Point: https://apis.data.go.kr/1790387/EIDAPIService
"""
import requests, os, datetime
import xml.etree.ElementTree as ET

API_KEY = os.environ.get("G2B_API_KEY", "")
BASE_URL = "https://apis.data.go.kr/1790387/EIDAPIService"

# 오퍼레이션 목록 (순서대로 시도)
OPERATIONS = [
    "/getInfectDissOccrrncInfoList",
    "/getInfectDissBaseInfo",
    "/getDissOccrrncInfoList",
    "/getOccrrncInfoList",
]

def collect_kdca():
    today = datetime.date.today()
    year  = today.strftime("%Y")
    start = (today - datetime.timedelta(days=30)).strftime("%Y%m%d")
    end   = today.strftime("%Y%m%d")

    for op in OPERATIONS:
        url = BASE_URL + op
        for disease in ["폐렴구균", ""]:  # 빈 문자열은 전체 조회
            params = {
                "serviceKey": API_KEY,
                "pageNo":     1,
                "numOfRows":  10,
                "startCreateDt": start,
                "endCreateDt":   end,
            }
            if disease:
                params["diseaseNm"] = disease

            try:
                resp = requests.get(url, params=params, timeout=15)
                print(f"  KDCA {op} HTTP: {resp.status_code}")

                if resp.status_code != 200:
                    continue

                text = resp.text.strip()
                print(f"  KDCA 응답: {text[:150]}")

                # XML 파싱
                if text.startswith("<"):
                    root = ET.fromstring(text)
                    code = root.findtext(".//resultCode", "")
                    msg  = root.findtext(".//resultMsg", "")
                    print(f"  KDCA 결과코드: {code} / {msg}")

                    if code == "00":
                        items = []
                        for item in root.findall(".//item"):
                            data = {c.tag: (c.text or "") for c in item}
                            items.append(data)
                        if items:
                            print(f"  KDCA 수집: {len(items)}건!")
                            return items

                # JSON 파싱
                elif text.startswith("{"):
                    data = resp.json()
                    body = data.get("response",{}).get("body",{})
                    items = body.get("items",{}).get("item",[])
                    if isinstance(items, dict):
                        items = [items]
                    if items:
                        return items

            except Exception as e:
                print(f"  KDCA 오류: {e}")
                continue

    return []
