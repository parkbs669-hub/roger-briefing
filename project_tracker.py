"""
프로젝트 누적 타임라인 트래커.

vault 파일에서 주요 프로젝트 언급을 추출해
data/projects/{프로젝트명}.json에 날짜별로 누적 저장.

복리 구조:
  매일 실행 → 새 내용 append → 쌓인 히스토리가 AI 프롬프트에 반영
  → 시간이 지날수록 더 정교한 프로젝트 분석
"""
import os
import re
import json
import glob
import datetime

from sales_collector import _date_from_filename, _read, VAULT_DIR

PROJECTS_DIR = os.environ.get("PROJECTS_DIR", "data/projects")

# 추적할 프로젝트 키워드 (파일명에 저장될 키)
PROJECT_KEYWORDS = {
    "천안_서북구청": ["서북구청", "천안", "이원 대표", "재중약품"],
    "인협_협력":     ["인구보건협회", "인협", "곽동희"],
    "제주도청":      ["제주도청", "제주"],
    "대한노인회":    ["대한노인회", "노인회"],
    "수성구청":      ["수성구청", "수성구"],
    "대구_코로나":   ["대구 코로나", "코로나 수요조사", "주민건"],
}

# 진행률 패턴 (예: "진행률: 40%" 또는 "40%")
_PROGRESS_RE = re.compile(r"진행률[:\s]*(\d+)%|(\d+)%\s*[|｜]\s*성공")
# 결과 패턴
_RESULT_RE   = re.compile(r"성공\s*확률[:\s]*(높음|중간|낮음|높다|낮다)")
# 마일스톤 완료 패턴 (✅)
_DONE_RE     = re.compile(r"✅\s*(.+)")
# 다음 단계 패턴
_NEXT_RE     = re.compile(r"다음\s*단계[:\s]*(.+)")


def _detect_projects(text: str) -> list[str]:
    """텍스트에서 언급된 프로젝트 키 반환."""
    found = []
    for key, keywords in PROJECT_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            found.append(key)
    return found


def _extract_snapshot(text: str, project_key: str) -> dict:
    """파일 본문에서 프로젝트 스냅샷 정보 추출."""
    snap = {}

    m = _PROGRESS_RE.search(text)
    if m:
        snap["progress"] = int(m.group(1) or m.group(2))

    m = _RESULT_RE.search(text)
    if m:
        snap["success_prob"] = m.group(1)

    done = _DONE_RE.findall(text)
    if done:
        snap["completed"] = [d.strip() for d in done[:5]]

    next_steps = _NEXT_RE.findall(text)
    if next_steps:
        snap["next_steps"] = [n.strip() for n in next_steps[:3]]

    # 프로젝트 관련 문단 요약 (최대 300자)
    keywords = PROJECT_KEYWORDS.get(project_key, [])
    relevant = []
    for para in text.split("\n\n"):
        if any(kw in para for kw in keywords):
            relevant.append(para.strip())
    if relevant:
        snap["excerpt"] = " ".join(relevant)[:300]

    return snap


def _load_timeline(project_key: str) -> dict:
    path = os.path.join(PROJECTS_DIR, f"{project_key}.json")
    if os.path.exists(path):
        return json.loads(open(path, encoding="utf-8").read())
    return {"project": project_key, "timeline": []}


def _save_timeline(project_key: str, data: dict):
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    path = os.path.join(PROJECTS_DIR, f"{project_key}.json")
    open(path, "w", encoding="utf-8").write(
        json.dumps(data, ensure_ascii=False, indent=2)
    )


def update_all_projects() -> dict[str, dict]:
    """vault 전체를 스캔해 모든 프로젝트 타임라인 업데이트. 변경된 프로젝트 반환."""
    updated = {}
    all_files = glob.glob(os.path.join(VAULT_DIR, "**", "*.md"), recursive=True)

    for path in sorted(all_files):
        text = _read(path)
        if not text:
            continue
        date = _date_from_filename(path)
        fname = os.path.basename(path).replace(".md", "")

        for project_key in _detect_projects(text):
            timeline = _load_timeline(project_key)
            # 같은 날짜+파일 중복 방지
            existing_dates = {e["date"] + e.get("source", "") for e in timeline["timeline"]}
            entry_id = date + fname
            if entry_id in existing_dates:
                continue

            snap = _extract_snapshot(text, project_key)
            if not snap:
                continue

            entry = {"date": date, "source": fname, **snap}
            timeline["timeline"].append(entry)
            timeline["timeline"].sort(key=lambda x: x["date"])
            _save_timeline(project_key, timeline)
            updated[project_key] = timeline

    return updated


def build_project_context() -> str:
    """AI 프롬프트용 프로젝트 누적 타임라인 요약 텍스트."""
    lines = ["=== 프로젝트 누적 타임라인 ==="]
    for fname in glob.glob(os.path.join(PROJECTS_DIR, "*.json")):
        data = json.loads(open(fname, encoding="utf-8").read())
        tl = data.get("timeline", [])
        if not tl:
            continue
        project = data["project"]
        latest = tl[-1]
        first_date = tl[0]["date"]
        last_date  = latest["date"]
        progress   = latest.get("progress", "?")
        prob       = latest.get("success_prob", "")
        weeks      = len(set(e["date"][:7] for e in tl))

        lines.append(f"\n[{project}] 추적 {weeks}주 | {first_date} → {last_date}")
        lines.append(f"  현재 진행률: {progress}% | 성공확률: {prob}")

        # 진행률 변화 추이
        progress_history = [(e["date"], e["progress"]) for e in tl if "progress" in e]
        if len(progress_history) >= 2:
            trend = " → ".join(f"{p}%({d[5:]})" for d, p in progress_history[-4:])
            lines.append(f"  진행 추이: {trend}")

        # 최근 완료 항목
        if latest.get("completed"):
            lines.append(f"  최근 완료: {', '.join(latest['completed'][:2])}")

        # 다음 단계
        if latest.get("next_steps"):
            lines.append(f"  다음 단계: {latest['next_steps'][0]}")

    return "\n".join(lines)


if __name__ == "__main__":
    updated = update_all_projects()
    print(f"업데이트된 프로젝트: {list(updated.keys())}")
    print(build_project_context())
