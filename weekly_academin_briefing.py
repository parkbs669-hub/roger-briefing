import os, smtplib, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import anthropic

A = os.environ["ANTHROPIC_API_KEY"]
N = os.environ["NAVER_ADDRESS"]
P = os.environ["NAVER_PASSWORD"]

# 📧 수신자 설정 (주간 브리핑 전용 - 환경변수 또는 기본값)
RECIPIENTS_STR = os.environ.get("WEEKLY_REPORT_RECIPIENTS", "parkbs669@naver.com")
RECIPIENTS = [r.strip() for r in RECIPIENTS_STR.split(",") if r.strip()]

def get_weekly_briefing():
    client = anthropic.Anthropic(api_key=A)
    today = datetime.date.today().strftime("%Y년 %m월 %d일")
    
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
• 국내 혈청형 분포 최신 현황
• 보건소 NIP 운영 현황
• 성인 접종률 및 정책 변화
• 건강보험 급여 관련 동향

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 이번 주 핵심 시사점
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 
2. 
3. 

해당 정보가 없는 카테고리는 "이번 주 해당 없음"으로 표시해주세요."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=6000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )
    return "".join(b.text for b in response.content if hasattr(b, "text")).strip()

def send_email(body):
    today = datetime.date.today().strftime("%Y년 %m월 %d일")
    msg = MIMEMultipart()
    msg["Subject"] = f"[폐렴구균 주간 학술 브리핑] {today}"
    msg["From"] = N
    msg["To"] = ", ".join(RECIPIENTS)
    text = f"안녕하세요,\n\n{today} 폐렴구균 백신 주간 학술 브리핑입니다.\n\n{body}\n\n---\nClaude AI 자동 발송"
    msg.attach(MIMEText(text, "plain", "utf-8"))
    with smtplib.SMTP_SSL("smtp.naver.com", 465) as s:
        s.login(N, P)
        s.sendmail(N, ",".join(RECIPIENTS), msg.as_string())
    print(f"✅ 주간 브리핑 발송 완료! (수신자: {', '.join(RECIPIENTS)})")

if __name__ == "__main__":
    print("주간 학술 브리핑 수집 중...")
    briefing = get_weekly_academin_briefing()
    print("이메일 발송 중...")
    send_email(briefing)
    print("완료!")
