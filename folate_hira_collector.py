import requests
import os
import xml.etree.ElementTree as ET

API_KEY = os.environ.get("PUBLIC_DATA_API_KEY", "")
URL = "https://apis.data.go.kr/B551182/dgamtCrtrInfoService1.2/getDgamtList"

def collect_hira():
    kws = {"백신": ["프리베나", "캡박시브"], "영양제": ["폴산", "철분"]}
    all_items, seen = [], set()
    for cat, words in kws.items():
        for kw in words:
            try:
                # 심평원은 파라미터가 itmNm 또는 itemName 일 수 있음
                params = {"serviceKey": API_KEY, "itmNm": kw, "numOfRows": 10}
                resp = requests.get(URL, params=params, timeout=15)
                root = ET.fromstring(resp.text.strip())
                for item in root.findall(".//item"):
                    d = {c.tag: (c.text or "") for c in item}
                    item_code = d.get("itmCd", "")
                    if item_code and item_code not in seen:
                        d['category'] = cat
                        seen.add(item_code)
                        all_items.append(d)
            except: continue
    return all_items[:15]
