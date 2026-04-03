import requests
import os
import datetime
import xml.etree.ElementTree as ET

API_KEY = os.environ.get("PUBLIC_DATA_API_KEY", "")
URL = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoThngPPSSrch"

def collect_g2b_notices():
    kw_map = {"백신": ["폐렴구균", "PCV20"], "영양제": ["엽산", "철분제", "임산부 영양제"]}
    all_items, seen = [], set()
    start = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y%m%d0000")
    end = datetime.datetime.now().strftime("%Y%m%d2359")
    
    for cat, kws in kw_map.items():
        for kw in kws:
            params = {"ServiceKey": API_KEY, "inqryDiv": "1", "inqryBgnDt": start, 
                      "inqryEndDt": end, "bidNtceNm": kw, "numOfRows": "10", "type": "xml"}
            try:
                resp = requests.get(URL, params=params, timeout=15)
                root = ET.fromstring(resp.text.strip())
                for item in root.findall(".//item"):
                    data = {c.tag: (c.text or "") for c in item}
                    bid_no = data.get("bidNtceNo", "")
                    if bid_no and bid_no not in seen:
                        data['category'] = cat
                        seen.add(bid_no)
                        all_items.append(data)
            except: continue
    return all_items
