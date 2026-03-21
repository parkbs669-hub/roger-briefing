"""
질병관리청 수집기 - 폐렴구균 감염병 발생현황
"""
import requests
import xml.etree.ElementTree as ET
import os
import datetime

API_KEY = os.environ.get("G2B_API_KEY", "")
URL = "https://apis.data.go.kr/B551182/msupUserInfoService1.2/getInfecStatus"

def collect_kdca():
    """감염병 발생현황 수집"""
    today = datetime.date.today()
    start = (today - datetime.timedelta(days=7)).strftime("%Y%m%d")
    end   = today.strftime("%Y%m%d")

    params = {
        "ServiceKey": API_KEY,
        "pageNo":     1,
        "numOfRows":  10,
        "startCreateDt": start,
        "endCreateDt":   end,
    }
    try:
        resp = requests.get(URL, params=params, timeout=15)
        print(f"  KDCA HTTP: {resp.status_code}")
        print(f"  KDCA 응답: {resp.text[:200]}")

        if resp.text.strip().startswith("<"):
            root = ET.fromstring(resp.text)
            code = root.findtext(".//resultCode", "")
            msg  = root.findtext(".//resultMsg", "")
            print(f"  KDCA 결과: {code} / {msg}")
            if code == "00":
                items = []
                for item in root.findall(".//item"):
                    data = {child.tag: (child.text or "") for child in item}
                    items.append(data)
                return items
        return []
    except Exception as e:
        print(f"  KDCA 오류: {e}")
        return []
