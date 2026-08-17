import os, sys, smtplib, datetime, json, urllib.request, base64, time
import requests
from urllib.parse import quote
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from news_collector import (
    collect_google_news, collect_google_news_kr,
    collect_pubmed, format_news_text, format_pubmed_text,
)

N = os.environ["NAVER_ADDRESS"]
P = os.environ["NAVER_PASSWORD"]

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")


def _generate_briefing(prompt: str) -> str:
    system_instruction = (
        "당신은 제약회사 폐렴구균 백신 학술 전문가 어시스턴트입니다. 브리핑을 작성할 때 다음 규칙을 반드시 준수하세요:\n"
        "1. 제공된 검색 결과나 뉴스에 명확히 나온 정보를 우선 사용하세요.\n"
        "2. 날짜, 접종률, 통계 수치 등은 출처(URL 또는 기관명)가 확인된 경우에만 기재하세요.\n"
        "3. 확인된 출처가 없는 항목은 '이번 주 확인된 정보 없음'으로 표시하세요.\n"
        "4. 근거 없는 수치나 날짜를 절대 창작하거나 추측하지 마세요.\n"
        "5. 양식의 빈칸을 채우기 위해 내용을 꾸며내지 마세요.\n"
        "6. 단, 제공된 검색 결과가 모두 비어있거나 오류인 경우에도, "
        "당신이 알고 있는 최근 공개된 학술 정보를 활용하여 브리핑을 작성하되, "
        "해당 내용 앞에 '※ AI 지식 기반 참고 정보 (검색 미확인):' 표시를 붙이세요. "
        "모든 항목이 '없음'인 브리핑은 작성하지 마세요."
    )

    # 1. DeepSeek 시도
    if DEEPSEEK_API_KEY:
        try:
            body = json.dumps({
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 6000,
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.deepseek.com/chat/completions", data=body,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                content = json.loads(r.read())["choices"][0]["message"]["content"]
                if content and len(content.strip()) > 200:
                    return content
        except Exception as e:
            print(f"  ⚠️  DeepSeek API 오류 ({e}), Gemini로 대체 시도합니다...")

    # 2. Gemini 폴백 시도
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            body = json.dumps({
                "system_instruction": {"parts": [{"text": system_instruction}]},
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": 6000}
            }).encode("utf-8")
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                res_data = json.loads(resp.read())
                content = res_data["candidates"][0]["content"]["parts"][0]["text"]
                if content and len(content.strip()) > 200:
                    print("  ✨ Gemini 대체 생성 성공")
                    return content
        except Exception as e:
            print(f"  ⚠️  Gemini 폴백 API 오류: {e}")

    return "(AI 학술 브리핑 생성 실패: DeepSeek 및 Gemini 모두 실패)"

RECIPIENTS = [
    "parkbs669@naver.com",
    "jaehwan.bae@pfizer.com",
    "Eun-Hye.Han@pfizer.com",
    "daeyoung.kang@pfizer.com",
    "Jeong-Jun.Kim@Pfizer.com",
    "In-Sun.Lee@pfizer.com",
    "Kyoung-Soo.Moon@pfizer.com",
]  # email-to-vault 주소 제거 (2026-07-07) — vault는 commit_to_vault()로 직접 저장



GH_PAT = os.environ.get("GH_PAT", "")


def commit_to_vault(markdown: str, filename: str, gh_pat: str):
    """MyVault_Roger/Emails/에 직접 커밋 (email-to-vault 의존성 제거, sales_daily_briefing과 동일 패턴)."""
    owner, repo = "parkbs669-hub", "MyVault_Roger"
    path = f"Emails/{filename}"
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{quote(path)}"
    headers = {
        "Authorization": f"token {gh_pat}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    sha = None
    try:
        r = requests.get(api_url, headers=headers, timeout=15)
        if r.status_code == 200:
            sha = r.json().get("sha")
    except Exception:
        pass

    body = {
        "message": f"chore: 학술브리핑 자동 저장 {filename[:10]}",
        "content": base64.b64encode(markdown.encode("utf-8")).decode("ascii"),
    }
    if sha:
        body["sha"] = sha

    try:
        r = requests.put(api_url, headers=headers, data=json.dumps(body), timeout=30)
        if r.status_code in (200, 201):
            print(f"vault 커밋 완료: {path}")
        else:
            print(f"vault 커밋 실패 ({r.status_code}): {r.text[:200]}")
    except Exception as e:
        print(f"vault 커밋 오류: {e}")


def collect_gemini_search() -> str:
    """Gemini 2.5 Flash REST API와 Google Search 도구로 실시간 웹 검색 수행 (재시도 포함)"""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "(GEMINI_API_KEY가 설정되지 않아 실시간 검색을 생략합니다)"
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    prompt = """오늘 기준 최근 7일간 아래 주제들에 대한 글로벌 및 한국의 최신 학술 논문, 임상시험 결과, 보건당국(WHO, CDC, FDA, 한국 질병관리청) 정책 동향 정보를 검색하고 요약해 주세요.
반드시 각 정보의 출처 웹사이트 URL을 함께 명시하세요.

주요 주제:
1. 성인 및 소아 폐렴구균 백신 (PCV20 프리베나20, PCV21 캡팍시브, PPSV23 프로디악스23 등) 최신 임상/학술/승인/NIP 정책 동향
2. 대상포진 백신 (싱그릭스 Shingrix 등) 최신 연구 및 허가 동향
3. RSV 백신 및 항체주사 (MSD Clesrovimab/Enflonsia, 화이자 Abrysvo, 모더나 mResvia, GSK Arexvy) 최신 임상/학술 동향
"""
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {"maxOutputTokens": 4096}
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                res_data = json.loads(resp.read())
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            last_err = e
            print(f"  ⚠️  Gemini 검색 시도 {attempt+1}/3 실패: {e}")
            if attempt < 2:
                time.sleep(5)
    return f"(Gemini 실시간 검색 3회 실패: {last_err})"


def get_weekly_briefing():
    KST = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(KST).date().strftime("%Y년 %m월 %d일")
    
    prompt = f"""오늘({today}) 기준 최근 7일간 폐렴구균 백신 관련 학술/정책 정보를 검색하고 한국어로 상세 브리핑을 작성해 주세요.

## 집중 검색 분야
- 성인 폐렴구균 백신 (PCV20, PCV21, PPSV23)
- 혈청형별 분포 및 역학 (특히 한국)
- 한국 시장 동향
- 한국 지역 보건소 접종 현황
- 국가예방접종(NIP) 정책 변화

## 검색 키워드
한국어: 폐렴구균 백신 논문, 폐렴구균 혈청형 한국, 보건소 폐렴구균, NIP 폐렴구균, 성인 폐렴구균 접종
영어: pneumococcal vaccine adult serotype Korea, PCV20 PCV21 clinical trial, pneumococcal NIP Korea, pneumococcal immunization policy

## 브리핑 형식 (각 항목 상세하게 작성)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 이번 주 주요 논문 (PubMed)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
논문별:
■ 논문 제목 (저널명, 발표일)
• 연구 배경: 
• 연구 방법: 
• 핵심 결과: 
• 임상적 의미: 
• 한국 시장 시사점: 

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔬 임상시험 현황 (ClinicalTrials.gov)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
신규 등록 또는 업데이트된 임상시험:
■ 임상시험명 (단계, 국가)
• 대상: 
• 목적: 
• 현황: 
• 예상 완료일: 

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏛 WHO/CDC 정책 동향
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 기관명 및 정책 제목
• 내용: 
• 한국 NIP에 미치는 영향: 
• 보건소 접종 정책 변화 가능성: 

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎓 학술대회 발표
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 학회명 및 발표 제목
• 발표자/기관: 
• 핵심 내용: 
• 시사점: 

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🇰🇷 한국 특화 동향
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 국내 혈청형 분포 최신 현황: (구체적 논문/보고서 인용 필수 — 없으면 '확인된 정보 없음')
• 보건소 NIP 운영 현황: (공식 질병관리청 발표 또는 URL 필수 — 없으면 '확인된 정보 없음')
• 성인 접종률 및 정책 변화: (공식 통계 출처 필수 — 없으면 '확인된 정보 없음' — 수치 추측 금지)
• 건강보험 급여 관련 동향: (출처 URL 필수 — 없으면 '확인된 정보 없음')

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🫁 RSV 학술/임상 동향
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• ABRYSVO (Pfizer, 60세 이상 / 산모 접종) 임상 최신 결과:
• ENFLONSIA (Clesrovimab, MSD) 임상 최신 결과:
• mResvia (Moderna mRNA RSV 백신) 논문/학술 동향:
• Arexvy (GSK) 임상·효능 업데이트:
• 국내 RSV 역학 및 NIP 도입 논의:
• 주요 RSV 관련 논문 (PubMed 최신):

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 이번 주 핵심 시사점
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1.
2.
3.

해당 정보가 없는 카테고리는 "이번 주 해당 없음"으로 표시해주세요."""

    # ── 1) Google News RSS 수집 (영문 + 한국어) ──
    keywords_en = [
        "pneumococcal vaccine serotype Korea clinical",
        "PCV20 PCV21 clinical trial results",
        "pneumococcal immunization policy WHO CDC",
        "herpes zoster vaccine shingrix update",
        "RSV vaccine nirsevimab clesrovimab ABRYSVO clinical trial 2026",
    ]
    keywords_kr = [
        "폐렴구균 백신",
        "폐렴구균 NIP 보건소",
        "RSV 백신 한국",
    ]
    print("  📰 Google News RSS 수집 중...")
    articles_en = collect_google_news(keywords_en)
    articles_kr = collect_google_news_kr(keywords_kr)
    all_news = articles_en + articles_kr
    news_text = format_news_text(all_news)
    print(f"  📰 뉴스 {len(all_news)}건 수집 완료")

    # ── 2) PubMed E-utilities 수집 ──
    pubmed_queries = [
        "pneumococcal vaccine",
        "PCV20 OR PCV21 OR pneumococcal conjugate",
        "RSV vaccine OR respiratory syncytial virus vaccine",
    ]
    print("  📚 PubMed 논문 수집 중...")
    all_pubmed = []
    for q in pubmed_queries:
        all_pubmed.extend(collect_pubmed(q, days=7, max_results=3))
    pubmed_text = format_pubmed_text(all_pubmed)
    print(f"  📚 PubMed 논문 {len(all_pubmed)}건 수집 완료")

    # ── 3) Gemini 실시간 검색 ──
    print("  🔍 Gemini 실시간 검색 중...")
    gemini_search_text = collect_gemini_search()
    print("  🔍 Gemini 검색 완료")

    # ── 4) 프롬프트 조합 ──
    full_prompt = (
        f"{prompt}\n\n"
        f"[Google News RSS 수집 뉴스 (최근 7일) — 실제 기사만 사용, 미검증 추측 내용 배제]\n{news_text}\n\n"
        f"[PubMed 최신 논문 (최근 7일) — 실제 등재된 논문만 참고]\n{pubmed_text}\n\n"
        f"[구글 실시간 검색 참고 정보 (최근 7일) — ⚠️ 검색 결과는 참고용이며, 공식 출처가 확인된 내용만 보고서에 반영할 것. 날짜·수치는 원문 URL 없으면 기재 금지]\n{gemini_search_text}"
    )
    return _generate_briefing(full_prompt)

def send_email(body):
    KST = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(KST).date().strftime("%Y년 %m월 %d일")
    msg = MIMEMultipart()
    msg["Subject"] = f"[폐렴구균 주간 학술 브리핑] {today}"
    msg["From"] = N
    msg["To"] = ", ".join(RECIPIENTS)
    text = f"안녕하세요,\n\n{today} 폐렴구균 백신 주간 학술 브리핑입니다.\n\n{body}\n\n---\nAI 자동 발송"
    msg.attach(MIMEText(text, "plain", "utf-8"))
    with smtplib.SMTP("smtp.naver.com", 587) as s:
        s.starttls()
        s.login(N, P)
        s.sendmail(N, RECIPIENTS, msg.as_string())
    print(f"✅ 주간 브리핑 발송 완료! (수신자: {', '.join(RECIPIENTS)})")

if __name__ == "__main__":
    print("주간 학술 브리핑 수집 중...")
    briefing = get_weekly_briefing()

    # ── 유효성 및 빈 브리핑 발송 방지 가드 ──
    if not briefing or briefing.startswith("(") or len(briefing.strip()) < 200:
        print(f"⚠️ 브리핑 생성에 실패하였거나 내용이 유효하지 않습니다:\n{briefing}\n발송을 건너뜁니다.")
        sys.exit(1)

    empty_count = briefing.count("확인된 정보 없음") + briefing.count("해당 없음")
    if empty_count >= 8 and "※ AI 지식 기반" not in briefing:
        print(f"⚠️ 브리핑 내용이 대부분 비어있습니다 (빈 항목 {empty_count}개). 발송을 건너뜁니다.")
        sys.exit(1)

    print("이메일 발송 중...")
    send_email(briefing)
    # vault 직접 저장 — 같은 파일명 재실행 시 sha 덮어쓰기라 중복 파일이 생기지 않음
    if GH_PAT:
        KST = datetime.timezone(datetime.timedelta(hours=9))
        now = datetime.datetime.now(KST)
        today_str = now.date().strftime("%Y년 %m월 %d일")
        subject = f"[폐렴구균 주간 학술 브리핑] {today_str}"
        md = f"""---
from: "{N}"
subject: "{subject}"
date: {now.isoformat()}
---

안녕하세요,

{today_str} 폐렴구균 백신 주간 학술 브리핑입니다.

{briefing}

---
DeepSeek AI 자동 발송
"""
        commit_to_vault(md, f"{now.date().isoformat()} {subject}.md", GH_PAT)
    else:
        print("GH_PAT 없음 — vault 직접 커밋 건너뜀")
    print("완료!")
