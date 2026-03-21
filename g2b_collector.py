"""나라장터 수집기"""
import requests, xml.etree.ElementTree as ET, os, datetime

API_KEY = os.environ.get("G2B_API_KEY", "")
URL = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoThngPPSSrch"

def collect_g2b_notices():
    keywords = ["폐렴구균", "PCV20", "PCV21", "폐렴구균 백신"]
    all_items, seen = [], set()
    for kw in keywords:
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=7)
        params = {
            "ServiceKey": API_KEY, "inqryDiv": "1",
            "inqryBgnDt": start.strftime("%Y%m%d0000"),
            "inqryEndDt": end.strftime("%Y%m%d2359"),
            "bidNtceNm": kw, "numOfRows": "10", "pageNo": "1", "type": "xml",
        }
        try:
            resp = requests.get(URL, params=params, timeout=15)
            root = ET.fromstring(resp.text)
            if root.findtext(".//resultCode","") != "00": continue
            for item in root.findall(".//item"):
                data = {c.tag: (c.text or "") for c in item}
                bid_no = data.get("bidNtceNo","")
                if bid_no not in seen:
                    seen.add(bid_no)
                    all_items.append(data)
        except Exception as e:
            print(f"  G2B 오류: {e}")
    print(f"  나라장터 → {len(all_items)}건")
    return all_items
