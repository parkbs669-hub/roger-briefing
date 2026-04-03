import requests
import os
import xml.etree.ElementTree as ET

API_KEY = os.environ.get("PUBLIC_DATA_API_KEY", "")
URL = "http://apis.data.go.kr/1471000/DrugNatnShipmntAprvInfoService/getDrugNatnShipmntAprvInfoInq"

def collect_mfds():
    targets = {"백신": ["폐렴구균", "프리베나"], "영양제": ["엽산", "철분"]}
    all_items, seen = [], set()
    for cat, kws in targets.items():
        for kw in kws:
            params = {"serviceKey": API_KEY, "pageNo": 1, "numOfRows": 20, "goods_name": kw}
            try:
                resp = requests.get(URL, params=params, timeout=15)
                root = ET.fromstring(resp.text.strip())
                for item in root.findall(".//item"):
                    d = {c.tag: (c.text or "") for c in item}
                    receipt_no = d.get("RECEIPT_NO", "")
                    if receipt_no and receipt_no not in seen:
                        d['category'] = cat
                        seen.add(receipt_no)
                        all_items.append(d)
            except: continue
    return all_items
