# Roger-Briefing 작업 기록 & 계획

작성일: 2026-07-01  
상태: 진행 중

---

## ✅ 완료된 작업

### 1. 주간 보고서 시간 변경 (08:00 → 06:00 KST)
- **파일**: `.github/workflows/Weekly_Report_Briefing.yml`, `.github/workflows/weekly_academic_briefing.yml`
- **변경**: cron `"0 23 * * 0"` → `"0 21 * * 0"` (UTC 기준, KST는 -9시간)
- **상태**: ✅ main에 병합됨

### 2. email-to-vault 도메인 교체
- **이유**: mail.tm 도메인 `wshu.net` 만료 → `web-library.net`으로 교체
- **수정 파일**:
  - `weekly_academic_briefing.py` (line 18)
  - `Weekly_Report_Briefing.py` (line 17)
  - `Daily_Report_Briefing.py` (line 340)
- **주소**: `email-to-vault-ks4bvu6d3r@web-library.net`
- **상태**: ✅ main에 병합됨

### 3. Claude 모델 마이그레이션 (claude-sonnet-4-5 → claude-sonnet-4-6)
- **이유**: claude-sonnet-4-5 은퇴 (2026-06-15)
- **수정 파일**:
  - `Weekly_Report_Briefing.py` (line 111)
  - `weekly_academic_briefing.py` (line 96)
- **웹검색 도구 업그레이드**:
  - `web_search_20250305` → `web_search_20260209` (동적 필터링 지원)
- **상태**: ✅ main에 병합됨

### 4. sales_daily_briefing.py DeepSeek 통합
- **파일**: `ai_processor.py`, `.github/workflows/Sales_Daily_Briefing.yml`
- **변경 사항**:
  - `ai_processor.py`에 `_call_deepseek()` 함수 추가
  - 우선순위: **DeepSeek → Claude → Gemini → LM Studio**
  - `.github/workflows/Sales_Daily_Briefing.yml`에 `DEEPSEEK_API_KEY` env 추가
- **비용 절감**: Claude($1.85/월) → DeepSeek($0.05/월) **약 97% 절감**
- **상태**: ✅ main에 병합됨
- **필수**: GitHub Secrets에 `DEEPSEEK_API_KEY` 등록 필요 (이미 완료)

### 5. GH_PAT 환경변수 워크플로우 추가
- **파일**: `.github/workflows/Sales_Daily_Briefing.yml`
- **목적**: GitHub API 직접 커밋 (vault 저장) 지원
- **상태**: ✅ main에 병합됨

### 6. 월간 비용 분석
| 프로그램 | 빈도 | 모델 | 월 비용 |
|---|---|---|---|
| `sales_daily_briefing.py` | 평일 매일(~22회) | claude-sonnet-4-6 | $1.85 |
| `Weekly_Report_Briefing.py` | 주 1회 | claude-sonnet-4-6 | $0.54 |
| `weekly_academic_briefing.py` | 주 1회 | claude-sonnet-4-6 | $0.54 |
| `Daily_Report_Briefing.py` | 매일 | 없음 (원자료 수집만) | $0 |
| **합계** | | | **~$2.93/월** |

---

## 📋 진행 중인 작업

### 주간 브리핑 2개 newsapi.org + DeepSeek 전환
**목표**: 비용 95% 절감 + 웹검색 기능 유지

#### 현재 상태 (문제점)
- `Weekly_Report_Briefing.py`, `weekly_academic_briefing.py`는 Claude의 built-in `web_search_20260209` 도구 사용
- 이 도구는 **Anthropic 전용** — DeepSeek에는 없음

#### 해결책
newsapi.org API(무료)로 뉴스 수집 → DeepSeek에 결과 텍스트로 전달 → 한국어 분석

#### 계획 상세

**1단계: news_collector.py 생성**

```python
import requests
from datetime import datetime, timedelta

def collect_news_from_newsapi(keywords: list[str], api_key: str) -> list[dict]:
    """
    newsapi.org에서 뉴스 수집
    - 최근 1주일 뉴스만
    - 상위 3개 기사/키워드
    - 영문 결과
    """
    base_url = "https://newsapi.org/v2/everything"
    results = []
    
    from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    for kw in keywords:
        try:
            r = requests.get(base_url, params={
                "q": kw,
                "apiKey": api_key,
                "language": "en",
                "sortBy": "publishedAt",
                "from": from_date,
                "pageSize": 3
            }, timeout=10)
            
            articles = r.json().get("articles", [])
            for a in articles[:3]:
                results.append({
                    "title": a.get("title", ""),
                    "source": a.get("source", {}).get("name", ""),
                    "url": a.get("url", ""),
                    "publishedAt": a.get("publishedAt", ""),
                    "description": a.get("description", ""),
                    "keyword": kw
                })
        except Exception as e:
            print(f"Error collecting {kw}: {e}")
            continue
    
    return results
```

**2단계: Weekly_Report_Briefing.py 수정**

기존:
```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    tools=[{"type": "web_search_20260209", "name": "web_search"}],
    messages=[{"role": "user", "content": prompt}]
)
```

변경:
```python
from news_collector import collect_news_from_newsapi
import json

# 뉴스 수집 (newsapi.org)
keywords = ["pneumococcal vaccine PCV20", "pneumococcal vaccine PCV21", "pneumococcal immunization policy Korea"]
news = collect_news_from_newsapi(keywords, os.environ.get("NEWS_API_KEY", ""))

# 프롬프트에 뉴스 데이터 포함
news_text = json.dumps([
    {"title": n["title"], "source": n["source"], "url": n["url"], "keyword": n["keyword"]}
    for n in news
], ensure_ascii=False, indent=2)

prompt = f"""이번 주({year} {week_start}~{week_end}) 폐렴구균 백신 관련 정보 분석

[검색된 뉴스 (newsapi.org)]
{news_text}

위 뉴스들을 분석하고 아래 두 가지 형식의 보고서를 한국어로 작성해 주세요:
...기존 프롬프트...
"""

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=6000,
    messages=[{"role": "user", "content": prompt}]
    # ← tools 제거 (웹검색 도구 불필요)
)
```

**3단계: weekly_academic_briefing.py 동일하게 수정**

키워드 조정:
```python
keywords = [
    "pneumococcal vaccine serotype Korea",
    "PCV20 PCV21 clinical trial",
    "pneumococcal immunization policy",
    "herpes zoster vaccine shingrix"
]
```

**4단계: 환경변수 추가**

`.github/workflows/Weekly_Report_Briefing.yml`:
```yaml
- env:
    ANTHROPIC_API_KEY:   ${{ secrets.ANTHROPIC_API_KEY }}
    NEWS_API_KEY:        ${{ secrets.NEWS_API_KEY }}  # ← 추가
    ...
```

`.github/workflows/weekly_academic_briefing.yml`:
```yaml
- env:
    ANTHROPIC_API_KEY:   ${{ secrets.ANTHROPIC_API_KEY }}
    NEWS_API_KEY:        ${{ secrets.NEWS_API_KEY }}  # ← 추가
    ...
```

---

## 🔧 필요한 작업

### A. newsapi.org 구현 (우선순위: 높음)

1. `news_collector.py` 생성
2. `Weekly_Report_Briefing.py` 수정 (뉴스 수집 통합)
3. `weekly_academic_briefing.py` 수정 (뉴스 수집 통합)
4. GitHub Secrets에 `NEWS_API_KEY` 추가
5. 워크플로우 YAML 2개 수정 (env에 NEWS_API_KEY 추가)
6. 테스트 실행 & 검증

### B. DeepSeek 마이그레이션 검토 (향후)

- sales_daily_briefing.py는 이미 DeepSeek 적용됨
- 주간 보고서 2개는 아직 Claude 사용 (newsapi.org 도입 후 추가 검토)

---

## 📊 예상 효과

| 항목 | 현재 | 전환 후 |
|---|---|---|
| **Weekly_Report 비용** | $0.54/월 | $0.01/월 |
| **academic_briefing 비용** | $0.54/월 | $0.01/월 |
| **월 합계** | $2.93 | ~$1.07 |
| **절감액** | - | **63% 절감** |

---

## 🔑 필요한 API 키 (GitHub Secrets)

| 키 | 상태 | 용도 |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ 있음 | Claude API |
| `DEEPSEEK_API_KEY` | ✅ 있음 | DeepSeek API |
| `NEWS_API_KEY` | ❓ 등록 필요 | newsapi.org |
| `NAVER_CLIENT_ID` | ✅ 있음 | Naver News API |
| `NAVER_CLIENT_SECRET` | ✅ 있음 | Naver News API |
| `GEMINI_API_KEY` | ✅ 있음 | Gemini (폴백) |
| `GH_PAT` | ✅ 있음 | GitHub API (vault 커밋) |

---

## 📝 작업 체크리스트

- [ ] `news_collector.py` 생성
- [ ] `Weekly_Report_Briefing.py` 수정
- [ ] `weekly_academic_briefing.py` 수정
- [ ] GitHub Secrets에 `NEWS_API_KEY` 추가
- [ ] `.github/workflows/Weekly_Report_Briefing.yml` env 수정
- [ ] `.github/workflows/weekly_academic_briefing.yml` env 수정
- [ ] 로컬 테스트 실행
- [ ] main에 병합
- [ ] 다음 주간 실행 모니터링

---

## 📌 주의사항

1. **newsapi.org 무료 사용량**: 월 100 requests (현재 계획: 월 ~40 requests → 충분함)
2. **최신성**: newsapi.org는 약 15분 지연 (RT가 아님)
3. **언어**: newsapi.org 결과는 영어 → Claude/DeepSeek이 번역+분석
4. **30일 제한**: Free 플랜은 최근 30일 뉴스만 검색 가능

---

## 참고 링크

- newsapi.org: https://newsapi.org
- 토큰 사용: sales_daily_briefing이 이미 DeepSeek 사용 중 (ai_processor.py 우선순위)
- 비용 명세: 월 $2.93 (현재) → $1.07 (전환 후)

## 2026-07-07 — 주간보고·학술브리핑 vault 직접 커밋 이식

- 배경: 주간보고·학술브리핑이 email-to-vault 수신으로 vault에 들어와, 재실행 시 ` 1.md` 중복 발생 (2026-07-06 사례: 스케줄 실패 → 수동 재실행 2회 → 중복 2건 + 1차 발송분에 DeepSeek 거절 문구 포함).
- 조치: sales_daily_briefing의 검증된 commit_to_vault() 패턴을 Weekly_Report_Briefing.py·weekly_academic_briefing.py에 이식. RECIPIENTS에서 email-to-vault 주소 제거. 두 워크플로에 GH_PAT env 추가.
- 효과: vault 파일은 GitHub API 직접 커밋(같은 파일명 재실행 시 sha 덮어쓰기 → 중복 원천 차단), 이메일은 사람 수신자 7명에게만.
- 검증: py_compile + 스텁 임포트 + commit_to_vault 실제 API 왕복(생성→확인→삭제) 통과. 실전 검증은 다음 월요일 06:00 스케줄 실행에서 vault 파일 생성 확인.
- 남은 개선(별건): DeepSeek 거절 문구 감지 후 재시도 가드 — 팀원에게 오류 문구 든 메일이 나가는 것 방지.

## 2026-07-07 — 통합브리핑 타파미디스/RSV 뉴스 빈칸 원인 수정

- 증상: 볼트 마크다운(및 PDF)의 네이버 뉴스에서 타파미디스(항상)·RSV(7/2 섹션 신설 이래) "관련 데이터가 없습니다".
- 원인: build_markdown_report의 `data["NEWS"][:30]` 전역 상한. 카테고리 3개 시절 유물로, 수집 순서상 뒤인 타파미디스·RSV가 통째로 잘림 (증거: 대상포진이 매일 정확히 5건 = 15+10+5에서 30 도달). HTML 이메일은 전체 리스트를 써서 정상이었음.
- 진단 과정: 로컬 API 재현 정상 → Actions 진단 워크플로(diag_naver_news)로 실행 환경도 정상 확인 → 렌더러로 범위 축소.
- 수정: 전역 상한 제거 (섹션별 [:10] 표시 제한은 유지). 가짜 뉴스 45건 끝-대-끝 렌더 테스트 통과.

## 2026-07-07 — 데일리 브리핑 꼬리 섹션 3종 제거 (사장님 지시)

- 미완료 후속 조치(723건 비대)·최근 영업 활동·최근 회의·파트너 협의 섹션을 이메일(HTML)과 vault 저장본(plain) 출력에서 제거.
- 데이터 수집(collect_pending_actions 등)은 유지 — AI 요약(섹션 1~3) 입력으로 계속 사용. 대시보드는 섹션 3만 파싱하므로 영향 없음.
- 고아가 된 _pending_html 함수 제거. "수신 이메일·보고서" 섹션은 지시 범위 밖이라 유지.

## 2026-07-07 — 미완료 수집기 제외 규칙 (사장님 승인)

- collect_pending_actions에서 Emails/(브리핑 출력물 재수집 루프)·copilot/(대화록)·archive/(보관) 제외.
- 실측: 498건 → 127건. 남은 127건은 wiki/projects·폐렴구균_지역정책 등 실제 프로젝트 문서의 체크박스.
- 사장님이 종합보고 정리(18개)·정책협력 통합 연계(6개) 체크 완료 확인.
