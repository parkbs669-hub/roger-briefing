# 네이버 뉴스 수집 진단 스크립트 — 이메일 발송 없이 쿼리별 응답 상태만 출력 (통합브리핑 타파미디스/RSV 빈칸 원인 조사)
import os
import time
import requests

URL = "https://openapi.naver.com/v1/search/news.json"
H = {
    "X-Naver-Client-Id": os.environ["NAVER_CLIENT_ID"],
    "X-Naver-Client-Secret": os.environ["NAVER_CLIENT_SECRET"],
}
# Daily_Report_Briefing.py collect_naver_news()와 동일한 키워드·순서
KW_MAP = {
    "백신": ["폐렴구균 백신", "캡박시브", "프리베나"],
    "영양제": ["임산부 엽산", "임산부 철분제"],
    "대상포진": ["대상포진 백신", "싱그릭스", "스카이조스터"],
    "타파미디스": ["타파미디스", "심장 아밀로이드증", "빈다맥스"],
    "RSV": ["RSV 백신", "호흡기세포융합바이러스", "니르세비맙", "아브리스보", "엔플론시아", "아렉스비", "mResvia"],
}

n = 0
for cat, kws in KW_MAP.items():
    for kw in kws:
        n += 1
        t0 = time.time()
        try:
            r = requests.get(URL, headers=H, params={"query": kw, "display": 5, "sort": "date"}, timeout=15)
            try:
                d = r.json()
            except Exception:
                d = {}
            items = d.get("items", [])
            print(f"#{n:02d} {cat} | {kw!r} | HTTP {r.status_code} | items={len(items)} total={d.get('total', '?')} "
                  f"| err={d.get('errorCode', '')} {d.get('errorMessage', '')} | {time.time() - t0:.2f}s", flush=True)
        except Exception as e:
            print(f"#{n:02d} {cat} | {kw!r} | EXCEPTION {type(e).__name__}: {e}", flush=True)
print("진단 완료")
