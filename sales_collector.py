"""
vault/ 폴더의 옵시디언 마크다운 파일을 읽어 영업 데이터를 수집하는 모듈.
GitHub Actions에서 실행되거나 로컬에서 직접 실행 가능.
"""
import os
import re
import glob
import datetime

VAULT_DIR = os.environ.get("VAULT_DIR", "vault")


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """YAML frontmatter와 본문을 분리."""
    meta = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].strip()
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    meta[k.strip()] = v.strip()
    return meta, body


def _recent_files(subdir: str, days: int = 7) -> list[str]:
    """지정 폴더에서 최근 N일 이내 수정된 마크다운 파일 목록 반환."""
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    result = []
    pattern = os.path.join(VAULT_DIR, subdir, "**", "*.md")
    for path in glob.glob(pattern, recursive=True):
        if datetime.datetime.fromtimestamp(os.path.getmtime(path)) >= cutoff:
            result.append(path)
    return sorted(result, reverse=True)


def collect_meetings(days: int = 3) -> list[dict]:
    """최근 회의록·병원방문일지 수집."""
    items = []
    for subdir in ("meetings", "sales"):
        for path in _recent_files(subdir, days):
            text = open(path, encoding="utf-8").read()
            meta, body = _parse_frontmatter(text)
            if meta.get("type") not in ("meeting", "sales_visit"):
                continue
            items.append({
                "type": meta.get("type"),
                "date": meta.get("date", ""),
                "hospital": meta.get("hospital", ""),
                "doctor": meta.get("doctor", ""),
                "product": meta.get("product", ""),
                "result": meta.get("result", ""),
                "visit_type": meta.get("visit_type", ""),
                "body": body,
                "filename": os.path.basename(path),
            })
    return sorted(items, key=lambda x: x["date"], reverse=True)


def collect_marketing(days: int = 7) -> list[dict]:
    """최근 마케팅 활동 수집."""
    items = []
    for path in _recent_files("marketing", days):
        text = open(path, encoding="utf-8").read()
        meta, body = _parse_frontmatter(text)
        if meta.get("type") != "marketing":
            continue
        items.append({
            "date": meta.get("date", ""),
            "activity_type": meta.get("activity_type", ""),
            "product": meta.get("product", ""),
            "attendees_count": meta.get("attendees_count", ""),
            "body": body,
            "filename": os.path.basename(path),
        })
    return sorted(items, key=lambda x: x["date"], reverse=True)


def collect_weekly_plans(limit: int = 2) -> list[dict]:
    """최근 주간 계획 수집."""
    items = []
    for path in _recent_files("weekly", 14):
        text = open(path, encoding="utf-8").read()
        meta, body = _parse_frontmatter(text)
        if meta.get("type") != "weekly_plan":
            continue
        items.append({
            "week": meta.get("week", ""),
            "date_start": meta.get("date_start", ""),
            "body": body,
            "filename": os.path.basename(path),
        })
    return sorted(items, key=lambda x: x["date_start"], reverse=True)[:limit]


def collect_pending_actions() -> list[str]:
    """vault 전체에서 미완료 Action Item(- [ ]) 수집."""
    pending = []
    for path in glob.glob(os.path.join(VAULT_DIR, "**", "*.md"), recursive=True):
        if "/templates/" in path.replace("\\", "/"):
            continue
        try:
            text = open(path, encoding="utf-8").read()
        except Exception:
            continue
        meta, _ = _parse_frontmatter(text)
        date = meta.get("date", "")
        hospital = meta.get("hospital", "")
        for line in text.splitlines():
            if re.match(r"\s*-\s\[ \]", line):
                task = line.strip().lstrip("- [ ]").strip()
                if task:
                    label = f"[{date}] {hospital} | {task}" if hospital else f"[{date}] {task}"
                    pending.append(label)
    return pending


def build_summary_text() -> str:
    """AI에 넘길 영업 데이터 요약 텍스트 생성."""
    meetings = collect_meetings(days=3)
    marketing = collect_marketing(days=7)
    plans = collect_weekly_plans()
    pending = collect_pending_actions()

    lines = []

    if meetings:
        lines.append("=== 최근 회의/방문 (3일) ===")
        for m in meetings[:10]:
            lines.append(f"[{m['date']}] {m['type']} | {m['hospital']} {m['doctor']} | 제품:{m['product']} | 결과:{m['result']}")
            lines.append(m["body"][:300])
            lines.append("")

    if marketing:
        lines.append("=== 최근 마케팅 활동 (7일) ===")
        for mk in marketing[:5]:
            lines.append(f"[{mk['date']}] {mk['activity_type']} | 제품:{mk['product']} | 참석:{mk['attendees_count']}명")
            lines.append(mk["body"][:200])
            lines.append("")

    if pending:
        lines.append("=== 미완료 후속 조치 ===")
        for p in pending[:15]:
            lines.append(f"  • {p}")
        lines.append("")

    if plans:
        lines.append("=== 이번 주 계획 ===")
        lines.append(plans[0]["body"][:500])

    return "\n".join(lines) if lines else "(vault에 아직 데이터가 없습니다)"
