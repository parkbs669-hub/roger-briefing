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
    "인협_협력":     ["인구보건협회", "인협", "곽동희"],
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


def _detect_projects_based_on_keywords(text: str) -> list[str]:
    """텍스트에서 언급된 프로젝트 키 반환."""
    found = []
    for key, keywords in PROJECT_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            found.append(key)
    return found


_detect_projects = _detect_projects_based_on_keywords


def _detect_projects_with_ai(text: str) -> list[str]:
    from ai_processor import generate
    
    project_list = ", ".join(PROJECT_KEYWORDS.keys())
    prompt = f"""
다음 영업 메모 텍스트에서 언급되거나 관련된 프로젝트를 아래 목록에서 찾아내세요.
목록: {project_list}

[텍스트]
{text}

[매핑 가이드]
- '인구보건협회'나 '인협', '곽동희' 관련 언급이 있으면 '인협_협력' 프로젝트에 매핑하세요.
- '대구 코로나', '코로나 수요조사', '주민건' 관련 언급이 있으면 '대구_코로나' 프로젝트에 매핑하세요.

반드시 아래 JSON 리스트 형식으로만 응답하세요. 다른 설명은 포함하지 마십시오.
예: ["대구_코로나"]
"""
    system = "당신은 텍스트에서 프로젝트 관련성을 판별하는 매핑 어시스턴트입니다."
    try:
        res = generate(prompt, system)
        m = re.search(r"\[.*\]", res, re.DOTALL)
        if m:
            keys = json.loads(m.group(0))
            return [k for k in keys if k in PROJECT_KEYWORDS]
    except Exception as e:
        print(f"AI 프로젝트 감지 오류: {e}")
    return _detect_projects_based_on_keywords(text)


def _extract_snapshot_based_on_regex(text: str, project_key: str) -> dict:
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

_extract_snapshot = _extract_snapshot_based_on_regex


def _extract_snapshot_with_ai(text: str, project_key: str) -> dict:
    from ai_processor import generate
    
    prompt = f"""
다음은 제약 영업 메모 텍스트입니다. 이 텍스트에서 프로젝트 '{project_key}'와 관련된 진행상황 정보를 추출하세요.

[텍스트]
{text}

[추출할 정보]
1. progress (진행률 %, 숫자로만, 예: 40)
   - 만약 '프로젝트 끝', '종료', '안 된다고 함', '해결 불가', '2026년은 안 된다고 함' 등의 표현이 있으면 진행률을 0으로 판단하세요.
   - 만약 진행률 수치 변경 언급이 없고 '보류', '연기' 등의 상황이면 기존 진행률을 유지하거나 생략하세요.
2. success_prob (성공 확률: 높음 / 중간 / 낮음)
3. completed (이번에 완료된 마일스톤 목록, 리스트)
4. next_steps (다음 단계 작업 목록, 리스트)
5. excerpt (해당 프로젝트와 관련된 구체적 내용 요약, 최대 250자)

반드시 아래 JSON 형식으로만 응답하세요. 다른 설명은 포함하지 마십시오.
{{
  "progress": 40, 
  "success_prob": "높음", 
  "completed": ["마일스톤1"], 
  "next_steps": ["다음단계1"], 
  "excerpt": "요약 내용..."
}}
"""
    system = "당신은 제약 영업 데이터를 분석하여 구조화된 JSON으로 변환하는 전문가 데이터 추출기입니다."
    try:
        res = generate(prompt, system)
        m = re.search(r"\{.*\}", res, re.DOTALL)
        if m:
            raw_data = json.loads(m.group(0))
            snap = {}
            if "progress" in raw_data and raw_data["progress"] is not None:
                snap["progress"] = int(raw_data["progress"])
            if "success_prob" in raw_data and raw_data["success_prob"]:
                snap["success_prob"] = str(raw_data["success_prob"])
            if "completed" in raw_data and isinstance(raw_data["completed"], list) and raw_data["completed"]:
                snap["completed"] = raw_data["completed"]
            if "next_steps" in raw_data and isinstance(raw_data["next_steps"], list) and raw_data["next_steps"]:
                snap["next_steps"] = raw_data["next_steps"]
            if "excerpt" in raw_data and raw_data["excerpt"]:
                snap["excerpt"] = str(raw_data["excerpt"])
            return snap
    except Exception as e:
        print(f"AI 추출 오류: {e}")
    return _extract_snapshot_based_on_regex(text, project_key)


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


def _is_recent(date_str: str) -> bool:
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.date.today()
        return (today - dt).days <= 3
    except:
        return False


def _has_ai_credentials() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY"))


def update_all_projects() -> dict[str, dict]:
    """vault 전체를 스캔해 모든 프로젝트 타임라인 업데이트. 변경된 프로젝트 반환."""
    updated = {}
    all_files = glob.glob(os.path.join(VAULT_DIR, "**", "*.md"), recursive=True)

    use_ai = False  # 비용 폭주 방지 (2026-07-11): AI 기반 감지 비활성화, 키워드만 사용

    for path in sorted(all_files):
        text = _read(path)
        if not text:
            continue
        date = _date_from_filename(path)
        fname = os.path.basename(path).replace(".md", "")

        is_recent_file = _is_recent(date)

        if use_ai and is_recent_file:
            detected_projects = _detect_projects_with_ai(text)
        else:
            detected_projects = _detect_projects_based_on_keywords(text)

        for project_key in detected_projects:
            timeline = _load_timeline(project_key)
            # 같은 날짜+파일 중복 방지
            existing_dates = {e["date"] + e.get("source", "") for e in timeline["timeline"]}
            entry_id = date + fname
            if entry_id in existing_dates:
                continue

            if use_ai and is_recent_file:
                snap = _extract_snapshot_with_ai(text, project_key)
            else:
                snap = _extract_snapshot_based_on_regex(text, project_key)

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
