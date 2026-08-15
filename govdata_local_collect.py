"""공공데이터포털(apis.data.go.kr) 수집기 — 사장님 PC(한국 IP)에서 실행.

배경 (2026-08-15 확정):
  data.go.kr이 2026-08-09 전후로 해외/클라우드 IP를 차단해, 미국에서 도는
  GitHub Actions 러너에서는 connect timeout이 난다. 한국 IP에서는 정상이다.
  (한국 PC 확인: /1790387/EIDAPIService/Disease → SERVICE_KEY_IS_NULL 응답)

그래서 '수집'만 한국에 있는 이 PC가 맡고, '발송'은 GitHub가 계속한다.
이 스크립트가 결과를 data/govdata/latest.json 에 저장·푸시하면,
Daily_Report_Briefing.py 가 실시간 수집 실패 시 그 파일을 대신 읽는다.

실행: python govdata_local_collect.py
필요 환경변수: PUBLIC_DATA_API_KEY (공공데이터포털 서비스키)
"""
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

# 수집 로직은 Daily_Report_Briefing.py 것을 그대로 재사용한다.
# (여기서 따로 구현하면 키워드·파싱 규칙이 갈라져 두 경로가 어긋난다.)
from Daily_Report_Briefing import collect_g2b, collect_kdca, collect_mfds, collect_hira

OUT_PATH = Path("data/govdata/latest.json")
SOURCES = {"G2B": collect_g2b, "KDCA": collect_kdca, "MFDS": collect_mfds, "HIRA": collect_hira}


def main():
    if not os.environ.get("PUBLIC_DATA_API_KEY", "").strip():
        print("❌ 중단: PUBLIC_DATA_API_KEY 환경변수가 없습니다.")
        return 1

    KST = datetime.timezone(datetime.timedelta(hours=9))
    now_kst = datetime.datetime.now(KST)
    print(f"🚀 공공데이터 수집 시작 (한국시간 {now_kst:%Y-%m-%d %H:%M})")

    collected, failed = {}, []
    for name, fn in SOURCES.items():
        try:
            items = fn() or []
        except Exception as e:
            items = []
            print(f"  {name}: 예외 — {e}")
        print(f"  {name}: {len(items)}건")
        if items:
            collected[name] = items
        else:
            failed.append(name)

    if not collected:
        # 전부 실패면 기존 스냅샷을 덮어쓰지 않는다. 오래된 데이터라도 없는 것보단 낫다.
        print("❌ 4개 소스 전부 0건 — 기존 스냅샷을 보존하고 종료합니다.")
        print("   (한국 IP에서도 실패했다면 서비스키·API 신청상태를 확인하세요.)")
        return 1

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    prev = {}
    if OUT_PATH.exists():
        try:
            prev = json.loads(OUT_PATH.read_text(encoding="utf-8")).get("data", {})
        except Exception:
            prev = {}

    # 이번에 실패한 소스는 직전 스냅샷 값을 유지한다(부분 실패로 통째 날리지 않도록).
    merged = dict(prev)
    merged.update(collected)

    payload = {
        "collected_at": now_kst.isoformat(),
        "collected_date": now_kst.strftime("%Y-%m-%d"),
        "ok_sources": sorted(collected),
        "failed_sources": sorted(failed),
        "data": merged,
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 저장 완료: {OUT_PATH} (성공 {sorted(collected)} / 실패 {sorted(failed) or '없음'})")

    push_to_github()
    return 0


def push_to_github():
    """스냅샷을 origin/main에 커밋·푸시한다. 실패해도 수집 자체는 성공으로 둔다."""
    try:
        if not subprocess.run(["git", "diff", "--quiet", "--", str(OUT_PATH)]).returncode:
            print("ℹ️ 변경 없음 — 커밋 생략")
            return
        stamp = datetime.date.today().strftime("%Y-%m-%d")
        subprocess.run(["git", "add", str(OUT_PATH)], check=True)
        subprocess.run(["git", "commit", "-m", f"chore: 공공데이터 스냅샷 갱신 {stamp}"], check=True)
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ GitHub 푸시 완료")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ git 작업 실패({e}) — 파일은 저장됐으니 수동으로 커밋·푸시하세요.")


if __name__ == "__main__":
    sys.exit(main())
