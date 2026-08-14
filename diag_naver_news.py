# 네이버 뉴스 수집 진단 스크립트 — 이메일 발송·vault 커밋 없이 응답 상태만 출력.
# 2026-08-12 NCP API HUB 이전 이후, 운영(Daily_Report_Briefing.py)과 동일한
# 엔드포인트·인증 헤더·키워드로 호출해 자격증명이 실제로 통과하는지 확인한다.
import os
import time
import requests

NCP_ID = os.environ.get("NCP_CLIENT_ID", "")
NCP_SECRET = os.environ.get("NCP_CLIENT_SECRET", "")
DEV_ID = os.environ.get("NAVER_CLIENT_ID", "")
DEV_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")

NCP_URL = "https://naverapihub.apigw.ntruss.com/search/v1/news"
LEGACY_URL = "https://openapi.naver.com/v1/search/news.json"

# Daily_Report_Briefing.py collect_naver_news()와 동일한 키워드·순서
KW_MAP = {
    "백신": ["폐렴구균 백신", "캡박시브", "프리베나"],
    "영양제": ["임산부 엽산", "임산부 철분제"],
    "대상포진": ["대상포진 백신", "싱그릭스", "스카이조스터"],
    "타파미디스": ["타파미디스", "심장 아밀로이드증", "빈다맥스"],
    "RSV": ["RSV 백신", "호흡기세포융합바이러스", "니르세비맙", "아브리스보", "엔플론시아", "아렉스비", "mResvia"],
}


def mask(v):
    """값은 절대 출력하지 않고 설정 여부와 길이만 보고한다."""
    return f"설정됨(길이 {len(v)})" if v else "❌ 미설정"


print("=" * 72)
print("[0] 자격증명 주입 상태")
print(f"  NCP_CLIENT_ID       : {mask(NCP_ID)}")
print(f"  NCP_CLIENT_SECRET   : {mask(NCP_SECRET)}")
print(f"  NAVER_CLIENT_ID     : {mask(DEV_ID)}  (구 Developers 폴백용)")
print(f"  NAVER_CLIENT_SECRET : {mask(DEV_SECRET)}")
if not (NCP_ID and NCP_SECRET):
    print("  ⚠️ NCP 키가 워크플로에 주입되지 않았습니다. "
          "Secrets 등록명이 NCP_CLIENT_ID / NCP_CLIENT_SECRET 인지 확인하세요.")
print("=" * 72)


def probe(label, url, headers, keywords):
    ok = err = 0
    for cat, kw in keywords:
        t0 = time.time()
        try:
            r = requests.get(url, headers=headers,
                             params={"query": kw, "display": 5, "sort": "date"}, timeout=15)
            try:
                d = r.json()
            except Exception:
                d = {}
            items = d.get("items", [])
            if r.status_code == 200 and items:
                ok += 1
            else:
                err += 1
            detail = ""
            if r.status_code != 200 or not items:
                # 오류 본문에서 원인 단서만 추린다 (NCP/Developers 응답 형식이 다름)
                msg = (f"{d.get('errorCode', d.get('error', ''))} "
                       f"{d.get('errorMessage', d.get('message', ''))}").strip()
                detail = f" | err={msg}" if msg else f" | raw={r.text[:120]}"
            print(f"  {cat:6s} | {kw!r:24s} | HTTP {r.status_code} | items={len(items)} "
                  f"| {time.time() - t0:.2f}s{detail}", flush=True)
        except Exception as e:
            err += 1
            print(f"  {cat:6s} | {kw!r:24s} | EXCEPTION {type(e).__name__}: {e}", flush=True)
    print(f"  → {label}: 성공 {ok}건 / 실패 {err}건")
    return ok, err


all_kws = [(cat, kw) for cat, kws in KW_MAP.items() for kw in kws]

print("\n[1] 운영 경로 — NCP API HUB (현재 Daily_Report_Briefing.py가 쓰는 설정)")
print(f"    {NCP_URL}")
ncp_headers = {
    "X-NCP-APIGW-API-KEY-ID": NCP_ID or DEV_ID,
    "X-NCP-APIGW-API-KEY": NCP_SECRET or DEV_SECRET,
}
ncp_ok, ncp_err = probe("NCP", NCP_URL, ncp_headers, all_kws)

print("\n[2] 대조군 — 구 Naver Developers Open API (8/12 이전 설정, 키워드 1개만)")
print(f"    {LEGACY_URL}")
legacy_headers = {"X-Naver-Client-Id": DEV_ID, "X-Naver-Client-Secret": DEV_SECRET}
legacy_ok, legacy_err = probe("Legacy", LEGACY_URL, legacy_headers, all_kws[:1])

print("\n" + "=" * 72)
print("[결론]")
if ncp_ok:
    print(f"  ✅ NCP 인증 정상 — {ncp_ok}/{len(all_kws)} 키워드 수집 성공. 뉴스 복구됨.")
elif not (NCP_ID and NCP_SECRET):
    print("  ❌ NCP 키 미주입 — Secrets 등록명/워크플로 env 배선을 확인하세요.")
else:
    print("  ❌ NCP 키는 주입됐으나 전량 실패 — 키 값 또는 API HUB 상품 이용신청 상태를 확인하세요.")
    print("     (NCP 콘솔에서 해당 API 이용신청·승인 여부, 발급 키가 API Gateway 키인지 확인)")
if legacy_ok:
    print("  ℹ️ 구 Developers API는 여전히 정상 응답 — 필요 시 롤백 가능.")
print("=" * 72)
print("진단 완료")
