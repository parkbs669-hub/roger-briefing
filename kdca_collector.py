"""
질병관리청 수집기 v2 - 전수신고 감염병 발생현황
"""
import requests
import xml.etree.ElementTree as ET
import os
import datetime

API_KEY = os.environ.get("G2B_API_KEY", "")

# 공식 확인된 정확한 URL
URL = "https://apis.data.go.kr/1790387/incidntOccrrncInfoInq/getIncidntOccrrncInfoList"

def collect_kdca():
    """폐렴구균 감염병 발생현황 수집"""
    today = datetime.date.today()
    start = (today - datetime.timedelta(days=30)).strftime("%Y%m%d")
    end   = today.strftime("%Y%m%d")

    params = {
        "ServiceKey":  API_KEY,
        "pageNo":      1,
        "numOfRows":   10,
        "bsrDt":       start,
        "endDt":       end,
        "diseaseNm":   "폐렴구균",
        "type":        "xml",
    }

    try:
        resp = requests.get(URL, params=params, timeout=15)
        print(f"  KDCA HTTP: {resp.status_code}")
        print(f"  KDCA 응답: {resp.text[:300]}")

        if not resp.text.strip().startswith("<"):
            return []

        root = ET.fromstring(resp.text)
        code = root.findtext(".//resultCode", "")
        msg  = root.findtext(".//resultMsg", "")
        print(f"  KDCA 결과코드: {code} / {msg}")

        if code != "00":
            return []

        items = []
        for item in root.findall(".//item"):
            data = {child.tag: (child.text or "") for child in item}
            items.append(data)
        return items

    except Exception as e:
        print(f"  KDCA 오류: {e}")
        return []
