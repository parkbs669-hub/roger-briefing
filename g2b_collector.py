"""
나라장터 수집기 - 입찰공고정보
End Point: http://apis.data.go.kr/1230000/ad/BidPublicInfoService
오퍼레이션: getBidPblancListInfoThngPPSSrch
"""
import requests
import os
import datetime
import xml.etree.ElementTree as ET

API_KEY = (
    os.environ.get("PUBLIC_DATA_API_KEY") or
    os.environ.get("HIRA_SERVICE_KEY") or
    os.environ.get("G2B_API_KEY", "")
)

URL = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoThngPPSSrch"
KEYWORDS = ["폐렴구균", "PCV20", "PCV21", "폐렴구균 백신"]


def collect_g2b_notices():
    all_items = []
    seen = set()

    for kw in KEYWORDS:
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=7)
        params = {
            "ServiceKey": API_KEY,
            "inqryDiv": "1",
            "inqryBgnDt": start.strftime("%Y%m%d0000"),
            "inqryEndDt": end.strftime("%Y%m%d2359"),
            "bidNtceNm": kw,
            "numOfRows": "10",
            "pageNo": "1",
            "type": "xml",
        }
        try:
            resp = requests.get(URL, params=params, timeout=15)
            print(f"  G2B '{kw}' HTTP: {resp.status_code}")

            text = resp.text.strip()
            if not text:
                print(f"  G2B 응답: 빈 응답")
                continue

            if not text.startswith("<"):
                print(f"  G2B 응답: {text[:150]}")
                continue

            root = ET.fromstring(text)
            code = root.findtext(".//resultCode", "")
            msg  = root.findtext(".//resultMsg", "")
            print(f"  G2B 결과: {code} / {msg}")

            if code not in ("00", "0000"):
                continue

            for item in root.findall(".//item"):
                data = {c.tag: (c.text or "") for c in item}
                bid_no = data.get("bidNtceNo", "") or str(data)[:50]
                if bid_no not in seen:
                    seen.add(bid_no)
                    all_items.append(data)

        except ET.ParseError as e:
            print(f"  G2B XML 파싱 오류: {e}")
            print(f"  G2B 응답 일부: {resp.text[:200] if resp else 'N/A'}")
        except Exception as e:
            print(f"  G2B '{kw}' 오류: {e}")

    print(f"  나라장터 → {len(all_items)}건")
    return all_items
