"""
나라장터 수집기 - 폐렴구균 입찰공고
"""
import requests
import xml.etree.ElementTree as ET
import datetime
import os

API_KEY = os.environ.get("G2B_API_KEY", "")
URL = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoThngPPSSrch"

def search_g2b(keyword, days=7):
    end   = datetime.datetime.now()
    start = end - datetime.timedelta(days=days)
    params = {
        "ServiceKey":  API_KEY,
        "inqryDiv":    "1",
        "inqryBgnDt":  start.strftime("%Y%m%d0000"),
        "inqryEndDt":  end.strftime("%Y%m%d2359"),
        "bidNtceNm":   keyword,
        "numOfRows":   "10",
        "pageNo":      "1",
        "type":        "xml",
    }
    try:
        resp = requests.get(URL, params=params, timeout=15)
        root = ET.fromstring(resp.text)
        code = root.findtext(".//resultCode", "")
        if code != "00":
            return []
        items = []
        for item in root.findall(".//item"):
            data = {child.tag: (child.text or "") for child in item}
            items.append(data)
        return items
    except Exception as e:
        print(f"  나라장터 오류: {e}")
        return []


def collect_g2b_notices():
    """폐렴구균 관련 입찰공고 수집"""
    keywords = ["폐렴구균", "PCV20", "PCV21", "폐렴구균 백신"]
    all_items = []
    seen = set()

    for kw in keywords:
        print(f"  🔍 나라장터 검색: {kw}")
        items = search_g2b(kw, days=7)
        for item in items:
            bid_no = item.get("bidNtceNo", "")
            if bid_no not in seen:
                seen.add(bid_no)
                all_items.append(item)
        print(f"     → {len(items)}건 발견")

    return all_items
