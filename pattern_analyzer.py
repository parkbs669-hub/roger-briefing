"""
주간 패턴 분석기 — 복리 구조의 핵심.

매주 금요일 실행:
  1. 이번 주 vault 데이터 분석
  2. AI가 성공/실패 패턴 추출
  3. data/patterns/cumulative.md 에 append (누적)

누적 효과:
  1주차: 단순 기록
  4주차: "이 메시지가 이 유형 의사에게 효과적"
  12주차: "서북구청 모델을 다른 구청에 적용 가능"
  1년차: 개인화된 영업 공략집 자동 완성
"""
import os
import datetime
import glob

from sales_collector import build_summary_text, _date_from_filename, _read, VAULT_DIR
from project_tracker import build_project_context, update_all_projects
from ai_processor import generate

PATTERNS_DIR   = os.environ.get("PATTERNS_DIR", "data/patterns")
CUMULATIVE_FILE = os.path.join(PATTERNS_DIR, "cumulative.md")
WEEKLY_DIR      = os.path.join(PATTERNS_DIR, "weekly")


def _this_week_label() -> str:
    today = datetime.date.today()
    return f"{today.year}-W{today.isocalendar()[1]:02d}"


def _load_cumulative() -> str:
    if os.path.exists(CUMULATIVE_FILE):
        return open(CUMULATIVE_FILE, encoding="utf-8").read()
    return "(아직 누적된 패턴 없음 — 첫 주 분석 시작)"


def analyze_week() -> str:
    """이번 주 데이터를 AI로 분석해 패턴 텍스트 반환."""
    week_label = _this_week_label()
    today = datetime.date.today().strftime("%Y-%m-%d")
    vault_summary  = build_summary_text()
    project_context = build_project_context()
    cumulative     = _load_cumulative()

    prompt = f"""
주간 패턴 분석 — {week_label} ({today})

[이번 주 영업 활동 데이터]
{vault_summary}

[프로젝트 누적 타임라인]
{project_context}

[지금까지 쌓인 누적 패턴]
{cumulative[:2000]}

위 데이터를 분석해 아래 형식으로 이번 주 패턴 보고서를 작성하세요.
기존 누적 패턴과 비교해 **새로 발견된 것**에 집중하세요.

## {week_label} 주간 패턴 분석

### 1. 이번 주 효과적이었던 것
- (구체적 메시지, 접근법, 자료 등)

### 2. 효과 없었거나 개선 필요한 것
- (무엇이 왜 안 됐는지)

### 3. 고객 반응 패턴 발견
- (어떤 유형의 고객이 어떤 것에 반응했는지)

### 4. 프로젝트 진행 패턴
- (진행 속도, 병목 지점, 돌파구)

### 5. 다음 주 적용할 전략 (패턴 기반)
- (이번 주 배운 것을 다음 주에 어떻게 적용)

### 6. 누적 인사이트 업데이트
- (기존 패턴이 이번 주로 강화/수정된 내용)
"""
    system = "당신은 제약영업 전문가 코치입니다. 데이터 기반으로 패턴을 발견하고 실행 가능한 인사이트를 제공하세요."
    return generate(prompt, system)


def save_weekly_pattern(analysis: str) -> str:
    """이번 주 분석 결과를 weekly 폴더에 저장."""
    os.makedirs(WEEKLY_DIR, exist_ok=True)
    week_label = _this_week_label()
    path = os.path.join(WEEKLY_DIR, f"{week_label}.md")
    open(path, "w", encoding="utf-8").write(analysis)
    return path


def update_cumulative(analysis: str):
    """누적 패턴 파일에 이번 주 분석 append — 복리의 핵심."""
    os.makedirs(PATTERNS_DIR, exist_ok=True)
    week_label = _this_week_label()
    today = datetime.date.today().strftime("%Y-%m-%d")

    # 기존 누적 파일 읽기
    existing = _load_cumulative()

    # 이번 주 내용 append
    new_entry = f"\n\n---\n<!-- {week_label} | {today} -->\n{analysis}"

    with open(CUMULATIVE_FILE, "w", encoding="utf-8") as f:
        if existing.startswith("(아직"):
            f.write(f"# 영업 패턴 누적 지식베이스\n\n")
            f.write(f"> 매주 자동 업데이트 — 쌓일수록 더 정교해집니다\n")
        else:
            f.write(existing)
        f.write(new_entry)


def build_pattern_context(max_chars: int = 3000) -> str:
    """AI 프롬프트용 누적 패턴 요약 (최근 것 우선)."""
    if not os.path.exists(CUMULATIVE_FILE):
        return "(아직 누적 패턴 없음)"

    content = open(CUMULATIVE_FILE, encoding="utf-8").read()

    # 최근 4주 섹션만 추출
    sections = content.split("---")
    recent = sections[-4:] if len(sections) > 4 else sections
    summary = "=== 누적 영업 패턴 (최근 4주) ===\n" + "---".join(recent)

    return summary[:max_chars]


def main():
    print(f"🔍 주간 패턴 분석 시작 — {_this_week_label()}")

    # 프로젝트 타임라인 먼저 업데이트
    updated = update_all_projects()
    print(f"  프로젝트 업데이트: {list(updated.keys())}")

    # 패턴 분석
    analysis = analyze_week()
    print("  AI 패턴 분석 완료")

    # 저장
    weekly_path = save_weekly_pattern(analysis)
    update_cumulative(analysis)
    print(f"  저장: {weekly_path}")
    print(f"  누적 파일 업데이트: {CUMULATIVE_FILE}")

    print("\n" + "="*50)
    print(analysis)


if __name__ == "__main__":
    main()
