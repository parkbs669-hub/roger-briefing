# DeepSeek 비용 폭증 방지 대책

**작성**: 2026-07-11  
**문제**: 7월 11일 DeepSeek 비용 $4.11 (평상시 3~4배)  
**원인**: project_tracker.py의 무분별한 AI 호출 반복

---

## 🔍 **근본 원인 분석**

### 1. project_tracker.py - 중복 AI 호출
```
for path in all_files:                          # Vault 모든 파일 순회
    if is_recent_file:
        _detect_projects_with_ai(text)          # AI 호출 #1
        
    for project_key in detected_projects:
        if is_recent_file:
            _extract_snapshot_with_ai(text)     # AI 호출 #2 (프로젝트당)
```

**문제점:**
- Vault에 100개 파일 × (1감지 + 2추출 평균) = **300회 AI 호출/일**
- 이미 처리된 파일도 매일 재처리
- 프로젝트당 별도 AI 호출로 인한 중복

**7월 11일 상황:**
- 10일(일요일) 스케줄 미실행 → 작업 백로그 축적
- 11일(금요일) 일괄 처리 시 누적 → 955 요청 발생

---

## ✅ **즉시 시행 대책 (Level 1 - 구현 우선순위)**

### 1.1 AI 호출 결과 캐싱
**file**: `project_tracker.py`  
**변경**:
```python
# 처리 이력 파일 추가
PROCESSED_CACHE = os.path.join(PROJECTS_DIR, ".processed.json")

def _load_processed_cache() -> set:
    """이미 처리된 파일 목록 로드."""
    if os.path.exists(PROCESSED_CACHE):
        try:
            data = json.load(open(PROCESSED_CACHE))
            return set(data.get("processed_files", []))
        except:
            return set()
    return set()

def update_all_projects() -> dict[str, dict]:
    updated = {}
    all_files = glob.glob(os.path.join(VAULT_DIR, "**", "*.md"), recursive=True)
    processed = _load_processed_cache()
    
    for path in sorted(all_files):
        fname = os.path.basename(path).replace(".md", "")
        # ✅ NEW: 이미 처리한 파일은 스킵
        if fname in processed and not _is_recent(date):
            continue
        
        # ... 기존 로직 ...
        
        # ✅ NEW: 처리 완료 후 캐시 저장
        processed.add(fname)
    
    # 캐시 저장
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    json.dump(
        {"processed_files": list(processed)},
        open(PROCESSED_CACHE, "w", encoding="utf-8")
    )
    
    return updated
```

**효과**: 중복 처리 제거 → **50~70% 비용 절감**

---

### 1.2 키워드 기반 감지 우선 적용
**file**: `project_tracker.py`  
**변경**:
```python
def update_all_projects() -> dict[str, dict]:
    use_ai = False  # ← AI 기반 감지 비활성화
    
    for path in sorted(all_files):
        # 모두 키워드 기반만 사용
        detected_projects = _detect_projects_based_on_keywords(text)  # No AI
        
        for project_key in detected_projects:
            # 스냅샷도 regex 기반만
            snap = _extract_snapshot_based_on_regex(text, project_key)  # No AI
```

**효과**: AI 호출 완전 제거 → **100% 비용 절감** (단, 정확도 ↓)

---

### 1.3 일일 AI 호출 한도 설정
**file**: `sales_daily_briefing.py` (최상단에 추가)  
```python
MAX_DEEPSEEK_CALLS_PER_DAY = 50  # 일일 최대 50회

deepseek_call_count = 0

def _check_daily_limit(cost_so_far_usd: float = 0):
    """AI 호출 한도 체크. 초과하면 조용히 스킵."""
    global deepseek_call_count
    if deepseek_call_count >= MAX_DEEPSEEK_CALLS_PER_DAY:
        print(f"⚠️  일일 AI 호출 한도 도달 ({MAX_DEEPSEEK_CALLS_PER_DAY}회). 스킵.")
        return False
    deepseek_call_count += 1
    return True

def _make_ai_section(...) -> str:
    if not _check_daily_limit():
        return "[AI 호출 한도 도달 — 생성 스킵]"
    
    # 기존 AI 호출
    return generate(prompt, system)
```

**효과**: 일일 최대 비용 선별적 제어

---

## 📊 **장기 개선안 (Level 2 - 1주일 내)**

### 2.1 증분 업데이트 (Incremental Update)
**파일**: `project_tracker.py` 전면 리팩토링  
**개념**: 
- 기존: 매일 **모든 파일** 재스캔 + 재처리
- 변경: **신규 파일 + 수정된 파일만** 처리

```python
def update_all_projects() -> dict[str, dict]:
    processed = _load_processed_cache()
    all_files = glob.glob(os.path.join(VAULT_DIR, "**", "*.md"), recursive=True)
    
    for path in sorted(all_files):
        mtime = os.path.getmtime(path)
        cached_mtime = processed.get(fname, {}).get("mtime", 0)
        
        # ✅ 수정되지 않은 파일은 건너뛰기
        if mtime == cached_mtime:
            continue
        
        # 신규/수정된 파일만 처리
        # ...
```

**효과**: 일일 처리 파일 1/10로 축소 → 95% 비용 절감

---

### 2.2 배치 호출 최적화 (Batch API)
**DeepSeek Batch API 활용** (가능 시)
- 개별 요청: 5¢/1K 토큰
- 배치 요청: 0.5¢/1K 토큰 (90% 할인)

변경안: 매일 밤 11시에 누적된 요청을 배치로 제출

---

### 2.3 정책 기반 Regex 확장
**파일**: `project_tracker.py`  
**개념**: 영업 메모의 패턴을 분석해 AI 없이 판별
```python
PROJECT_KEYWORDS = {
    "인협_협력": [
        "인구보건협회", "인협", "곽동희",
        "협력", "MOU", "양해각서",  # 패턴 추가
    ],
    "대구_코로나": [
        "대구", "코로나", "수요조사",
        "주민건강", "역학조사",  # 패턴 추가
    ],
}
```

---

## 🚨 **긴급 조치 (즉시 실행)**

**1. sales_daily_briefing.py 비활성화** (Level 2 개선까지)
```yaml
# .github/workflows/Sales_Daily_Briefing.yml
on:
  workflow_run:
    workflows: ["Daily_Report_Briefing"]
    types:
      - completed

  workflow_dispatch:

jobs:
  run:
    if: false  # ← 비활성화 (테스트만 가능)
```

**2. project_tracker.py에서 AI 호출 비활성화**
```python
_ENABLE_AI_DETECTION = False  # 키워드 기반으로만 처리
```

---

## 📈 **효과 예상**

| 대책 | 실행 난이도 | 효과 | 예상 절감 |
|-----|----------|------|---------|
| 1.1 캐싱 추가 | ⭐️ 낮음 | 중복 제거 | 50% |
| 1.2 키워드만 사용 | ⭐️ 낮음 | AI 호출 제거 | 100% (프로젝트 추적) |
| 1.3 일일 한도 | ⭐️ 낮음 | 폭주 방지 | 선별적 |
| 2.1 증분 업데이트 | ⭐️⭐️ 중간 | 근본 해결 | 95% |
| 2.2 배치 API | ⭐️⭐️ 중간 | 10배 할인 | 90% |

---

## 📅 **실행 계획**

### **Phase 1 (즉시 - 7월 11일 오후)**
- [ ] sales_daily_briefing 워크플로우 비활성화 (`if: false`)
- [ ] project_tracker.py AI 호출 비활성화

### **Phase 2 (내일 - 7월 12일)**
- [ ] 캐싱 로직 추가 (1.1)
- [ ] 일일 한도 설정 (1.3)
- [ ] 테스트 실행

### **Phase 3 (1주일 - 7월 18일)**
- [ ] 증분 업데이트 구현 (2.1)
- [ ] 정책 키워드 확장 (2.3)
- [ ] 정상 운영 재개

---

## ⚠️ **주의**

- **project_tracker의 AI 감지 기능**: 정확도 ↓ (키워드만 사용)
  - 새 프로젝트 추가 시 `PROJECT_KEYWORDS`에 수동 등록 필요
  - 모호한 문맥 감지 불가

- **sales_daily_briefing 일시 중단**: 평일 업무 영향
  - Daily_Report_Briefing은 계속 실행 (원자료 수집)
  - 사장님 피드백 없이 자동 재개하지 않기

---

## 참고: GitHub Actions 워크플로우 비활성화

```yaml
# .github/workflows/Sales_Daily_Briefing.yml
jobs:
  run:
    if: false  # ← 이 한 줄 추가
    runs-on: ubuntu-latest
    steps:
      # ...
```

변경 후:
```bash
git add .github/workflows/Sales_Daily_Briefing.yml
git commit -m "chore: DeepSeek 비용 폭주 방지 — Sales_Daily_Briefing 일시 비활성화"
git push
```
