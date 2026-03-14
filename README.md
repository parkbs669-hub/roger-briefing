# 🫁 폐렴구균 백신 뉴스 자동 브리핑

매일 오전 8시, PCV20·PCV21 관련 뉴스를 자동 수집·요약하여 이메일로 발송합니다.

---

## 📋 세팅 순서 (총 4단계, 약 20분 소요)

---

### 1단계: Anthropic API 키 발급

1. https://console.anthropic.com 접속 → 구글/이메일로 회원가입
2. 좌측 메뉴 **"API Keys"** 클릭
3. **"Create Key"** 버튼 클릭 → 이름 입력 (예: `pneumo-briefing`)
4. 생성된 키 복사 (`sk-ant-...` 로 시작하는 문자열)

> ⚠️ API 키는 한 번만 표시됩니다. 반드시 복사해 두세요!
> 💳 요금: 브리핑 1회 실행 시 약 $0.01~0.03 수준 (월 약 300~900원)

---

### 2단계: Gmail 앱 비밀번호 발급

일반 Gmail 비밀번호 대신 앱 전용 비밀번호가 필요합니다.

1. https://myaccount.google.com 접속
2. **"보안"** 탭 클릭
3. **"2단계 인증"** 활성화 (아직 안 된 경우)
4. 검색창에 **"앱 비밀번호"** 검색 → 클릭
5. 앱 선택: **"메일"**, 기기 선택: **"기타"** → 이름 입력 (예: `briefing`)
6. 생성된 16자리 비밀번호 복사 (예: `abcd efgh ijkl mnop`)

---

### 3단계: GitHub 저장소 만들기

1. https://github.com 접속 → 회원가입 or 로그인
2. 우상단 **"+"** → **"New repository"** 클릭
3. Repository name: `pneumo-briefing` 입력
4. **Private** 선택 (키 보안을 위해 권장)
5. **"Create repository"** 클릭

#### 파일 업로드
6. **"uploading an existing file"** 클릭
7. 이 패키지에 포함된 파일들을 드래그 업로드:
   - `briefing.py`
   - `.github/workflows/daily-briefing.yml`
8. **"Commit changes"** 클릭

#### Secrets(비밀값) 등록
9. 저장소 상단 **"Settings"** 탭 클릭
10. 좌측 **"Secrets and variables"** → **"Actions"** 클릭
11. **"New repository secret"** 으로 아래 3개 등록:

| Name | Value |
|------|-------|
| `ANTHROPIC_API_KEY` | 1단계에서 복사한 API 키 |
| `GMAIL_ADDRESS` | 발신에 사용할 Gmail 주소 (예: yourname@gmail.com) |
| `GMAIL_APP_PASSWORD` | 2단계에서 복사한 16자리 앱 비밀번호 |

---

### 4단계: 테스트 실행

1. 저장소 상단 **"Actions"** 탭 클릭
2. 좌측에서 **"폐렴구균 백신 뉴스 브리핑"** 클릭
3. 우측 **"Run workflow"** 버튼 클릭 → **"Run workflow"** 확인
4. 실행 완료 후 parkbs669@naver.com 받은편지함 확인

> ✅ 이메일이 오면 세팅 완료! 이후 매일 오전 8시에 자동 발송됩니다.

---

## ⏰ 발송 시간 변경 방법

`.github/workflows/daily-briefing.yml` 파일에서 cron 값 수정:

```yaml
# 오전 7시로 변경하고 싶다면 (KST 7시 = UTC 22시)
- cron: "0 22 * * *"

# 오전 9시로 변경하고 싶다면 (KST 9시 = UTC 0시)
- cron: "0 0 * * *"
```

---

## 💰 비용 요약

| 항목 | 비용 |
|------|------|
| GitHub Actions | 무료 (월 2,000분 제공) |
| Anthropic API | 약 $0.01~0.03/회 → 월 $0.3~0.9 |
| Gmail 발송 | 무료 |
| **합계** | **월 약 400~1,300원** |

---

## 🆘 문제 해결

**이메일이 안 올 때**
- Actions 탭 → 실패한 워크플로 클릭 → 에러 메시지 확인
- Gmail 앱 비밀번호 재발급 후 Secret 업데이트

**스팸함에 들어올 때**
- 받은편지함으로 이동 후 "스팸 아님" 처리
- 발신 주소를 주소록에 추가
