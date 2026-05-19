"""
MyVault_Roger 옵시디언 볼트에서 영업 데이터를 수집하는 모듈.

실제 볼트 구조:
  영업_협력활동/        ← 영업 종합보고, 일정 메모
    주간회의/           ← SHP/HAS 주간회의
    파트너협의/         ← 도매상·기관 협의
    마케팅미팅/         ← 마케팅 활동
    영업활동 정리/      ← 활동 정리
    주간학술브리핑/     ← 학술 브리핑
  PCV20_정책자료/       ← 정책 근거 자료
  폐렴구균_지역정책/    ← 지역 정책
  산출물/              ← 제안서, 팜플렛 등

파일명 규칙: YYYY-MM-DD_제목.md (YAML frontmatter 없음)
"""
import os
import re
import glob
import datetime

VAULT_DIR = os.environ.get("VAULT_DIR", "vault")

# 폴더 경로 매핑
DIRS = {
    "sales":        "영업_협력활동",
    "meetings":     "영업_협력활동/주간회의",
    "partner":      "영업_협력활동/파트너협의",
    "marketing":    "영업_협력활동/마케팅미팅",
    "summary":      "영업_협력활동/영업활동 정리",
    "academic":     "영업_협력활동/주간학술브리핑",
    "emails":       "Emails",
    "pcv20":        "PCV20_정책자료",
    "local_policy": "폐렴구균_지역정책",
    "output":       "산출물",
}


def _date_from_filename(path: str) -> str:
    """파일명에서 YYYY-MM-DD 추출. 없으면 mtime 사용."""
    name = os.path.basename(path)
    m = re.match(r"(\d{4}-\d{2}-\d{2})", name)
    if m:
        return m.group(1)
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
    return mtime.strftime("%Y-%m-%d")


def _all_md(subdir_key: str, days: int = 14) -> list[str]:
    """해당 폴더에서 최근 N일 이내 파일 반환 (날짜는 파일명 기준)."""
    subdir = DIRS.get(subdir_key, subdir_key)
    pattern = os.path.join(VAULT_DIR, subdir, "**", "*.md")
    cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    result = []
    for path in glob.glob(pattern, recursive=True):
        if _date_from_filename(path) >= cutoff:
            result.append(path)
    # 루트 파일도 포함 (재귀 없이)
    for path in glob.glob(os.path.join(VAULT_DIR, subdir, "*.md")):
        if path not in result and _date_from_filename(path) >= cutoff:
            result.append(path)
    return sorted(result, key=_date_from_filename, reverse=True)


def _read(path: str) -> str:
    try:
        return open(path, encoding="utf-8").read()
    except Exception:
        return ""


def collect_sales_reports(days: int = 7) -> list[dict]:
    """영업_협력활동 루트 + 영업활동 정리 폴더의 종합 보고서 수집."""
    items = []
    for key in ("sales", "summary"):
        for path in _all_md(key, days):
            text = _read(path)
            if not text:
                continue
            items.append({
                "date": _date_from_filename(path),
                "title": os.path.basename(path).replace(".md", ""),
                "body": text,
                "folder": key,
            })
    return sorted(items, key=lambda x: x["date"], reverse=True)


def collect_meetings(days: int = 7) -> list[dict]:
    """주간회의 + 파트너협의 수집."""
    items = []
    for key in ("meetings", "partner"):
        for path in _all_md(key, days):
            text = _read(path)
            if not text:
                continue
            items.append({
                "date": _date_from_filename(path),
                "title": os.path.basename(path).replace(".md", ""),
                "body": text,
                "folder": key,
            })
    return sorted(items, key=lambda x: x["date"], reverse=True)


def collect_marketing(days: int = 14) -> list[dict]:
    """마케팅미팅 수집."""
    items = []
    for path in _all_md("marketing", days):
        text = _read(path)
        if not text:
            continue
        items.append({
            "date": _date_from_filename(path),
            "title": os.path.basename(path).replace(".md", ""),
            "body": text,
        })
    return sorted(items, key=lambda x: x["date"], reverse=True)


def collect_academic(days: int = 14) -> list[dict]:
    """주간학술브리핑 수집."""
    items = []
    for path in _all_md("academic", days):
        text = _read(path)
        if not text:
            continue
        items.append({
            "date": _date_from_filename(path),
            "title": os.path.basename(path).replace(".md", ""),
            "body": text,
        })
    return sorted(items, key=lambda x: x["date"], reverse=True)


def collect_emails(days: int = 14) -> list[dict]:
    """Emails/ 폴더의 수신 이메일·브리핑 수집."""
    items = []
    for path in _all_md("emails", days):
        text = _read(path)
        if not text:
            continue
        items.append({
            "date":  _date_from_filename(path),
            "title": os.path.basename(path).replace(".md", ""),
            "body":  text,
        })
    return sorted(items, key=lambda x: x["date"], reverse=True)


def collect_pcv20_policy(days: int = 9999) -> list[dict]:
    """PCV20_정책자료/ 전체 수집 (고정 지식베이스 — 날짜 무관)."""
    items = []
    pattern = os.path.join(VAULT_DIR, DIRS["pcv20"], "*.md")
    for path in glob.glob(pattern):
        text = _read(path)
        if not text:
            continue
        items.append({
            "date":  _date_from_filename(path),
            "title": os.path.basename(path).replace(".md", ""),
            "body":  text,
        })
    return sorted(items, key=lambda x: x["title"])


def collect_local_policy(days: int = 9999) -> list[dict]:
    """폐렴구균_지역정책/ 전체 수집 (고정 지식베이스 — 날짜 무관)."""
    items = []
    pattern = os.path.join(VAULT_DIR, DIRS["local_policy"], "*.md")
    for path in glob.glob(pattern):
        text = _read(path)
        if not text:
            continue
        items.append({
            "date":  _date_from_filename(path),
            "title": os.path.basename(path).replace(".md", ""),
            "body":  text,
        })
    return sorted(items, key=lambda x: x["title"])


def collect_pending_actions() -> list[dict]:
    """볼트 전체에서 미완료 체크박스(- [ ]) 수집."""
    pending = []
    for path in glob.glob(os.path.join(VAULT_DIR, "**", "*.md"), recursive=True):
        text = _read(path)
        date = _date_from_filename(path)
        fname = os.path.basename(path).replace(".md", "")
        for line in text.splitlines():
            if re.match(r"\s*-\s\[ \]", line):
                task = re.sub(r"^\s*-\s\[ \]\s*", "", line).strip()
                if task:
                    pending.append({
                        "date": date,
                        "source": fname,
                        "task": task,
                    })
    return sorted(pending, key=lambda x: x["date"], reverse=True)


def build_summary_text() -> str:
    """AI 프롬프트에 넘길 볼트 데이터 요약 텍스트."""
    sales        = collect_sales_reports(days=7)
    meetings     = collect_meetings(days=7)
    marketing    = collect_marketing(days=14)
    academic     = collect_academic(days=14)
    emails       = collect_emails(days=14)
    pcv20        = collect_pcv20_policy()
    local_policy = collect_local_policy()
    pending      = collect_pending_actions()

    sections = []

    if sales:
        sections.append("=== 최근 영업 활동 보고 (7일) ===")
        for s in sales[:5]:
            sections.append(f"[{s['date']}] {s['title']}")
            sections.append(s["body"][:600])
            sections.append("")

    if meetings:
        sections.append("=== 최근 회의·파트너 협의 (7일) ===")
        for m in meetings[:3]:
            sections.append(f"[{m['date']}] {m['title']}")
            sections.append(m["body"][:400])
            sections.append("")

    if marketing:
        sections.append("=== 최근 마케팅 활동 (14일) ===")
        for mk in marketing[:3]:
            sections.append(f"[{mk['date']}] {mk['title']}")
            sections.append(mk["body"][:300])
            sections.append("")

    if academic:
        sections.append("=== 최근 학술 브리핑 ===")
        for ac in academic[:2]:
            sections.append(f"[{ac['date']}] {ac['title']}")
            sections.append(ac["body"][:400])
            sections.append("")

    if emails:
        sections.append("=== 최근 수신 이메일·보고서 (14일) ===")
        for e in emails[:5]:
            sections.append(f"[{e['date']}] {e['title']}")
            sections.append(e["body"][:400])
            sections.append("")

    if pcv20:
        sections.append("=== PCV20 정책 근거 자료 (전체) ===")
        for p in pcv20:
            sections.append(f"• {p['title']}")
            sections.append(p["body"][:200])
            sections.append("")

    if local_policy:
        sections.append("=== 폐렴구균 지역 정책 자료 (전체) ===")
        for lp in local_policy:
            sections.append(f"• {lp['title']}")
            sections.append(lp["body"][:200])
            sections.append("")

    if pending:
        sections.append("=== 미완료 후속 조치 ===")
        for p in pending[:20]:
            sections.append(f"  • [{p['date']}] {p['source']} → {p['task']}")
        sections.append("")

    return "\n".join(sections) if sections else "(vault에 데이터가 없습니다)"
