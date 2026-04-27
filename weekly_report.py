import os, smtplib, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import anthropic

A = os.environ["ANTHROPIC_API_KEY"]
N = os.environ["NAVER_ADDRESS"]
P = os.environ["NAVER_PASSWORD"]
# 📧 수신자 설정 (주간 보고서 전용 - 환경변수 또는 기본값)
RECIPIENTS_STR = os.environ.get("WEEKLY_REPORT_RECIPIENTS", "parkbs669@naver.com")
RECIPIENTS = [r.strip() for r in RECIPIENTS_STR.split(",") if r.strip()]

def get_weekly_report():
    client = anthropic.Anthropic(api_key=A)
    today = datetime.date.today()
    week_start = (today - datetime.timedelta(days=4)).strftime("%m월 %d일")
    week_end = today.strftime("%m월 %d일")
    year = today.strftime("%Y년")
    week_num = today.isocalendar()[1]

    prompt = f"""이번 주({year} {week_start}~{week_end}) 폐렴구균 백신 관련 정보를 검색하고
아래 두 가지 형식의 보고서를 모두 작성해 주세요.

## 검색 키워드
- 폐렴구균 백신 뉴스 이번 주
- PCV20 PCV21 Prevnar Capvaxive 동향
- 질병관리청 NIP 보건소 폐렴구균
- pneumococcal vaccine news this week
- pneumococcal market Korea 2026

================================================================
📊 [버전 1] 임원/팀장용 핵심 요약 보고서
================================================================

■ 폐렴구균 백신 주간 업무 보고
{year} {week_num}주차 ({week_start}~{week_end})

[이번 주 3대 핵심 이슈]
1.
2.
3.

[시장/경쟁 동향 요약]
• 화이자(PCV20):
• MSD(PCV21 캡박시브):
• 기타 경쟁사:

[정책/보건소 변화]
• 질병관리청:
• NIP 변경사항:
• 보건소 접종 현황:

[학술/임상 동향]
• 주요 논문:
• 임상시험:

[다음 주 주목할 사항]
1.
2.

[권고 액션 아이템]
1.
2.
3.

================================================================
📋 [버전 2] 실무자용 상세 분석 보고서
================================================================

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 시장/경쟁 상세 동향
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[기사/이슈별 상세 분석]
■ 제목 (출처, 날짜)
• 배경:
• 핵심 내용:
• 시장 영향:
• 대응 전략:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏥 보건소/NIP 정책 상세
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 이번 주 질병관리청 공지:
• NIP 변경 세부사항:
• 지역별 보건소 동향:
• 급여 변경사항:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 학술/임상 상세
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 주요 논문 상세 요약:
• 임상시험 업데이트:
• 학술대회 발표:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 종합 시사점 및 전략적 제언
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 단기 (1개월 이내):
• 중기 (3~6개월):
• 장기 (1년 이상):"""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=6000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )
    return "".join(b.text for b in response.content if hasattr(b, "text")).strip()

def send_email(body):
    today = datetime.date.today()
    week_num = today.isocalendar()[1]
    subject = f"[폐렴구균 백신 주간보고] {today.strftime('%Y년')} {week_num}주차"
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = N
    msg["To"] = ", ".join(RECIPIENTS)
    text = f"안녕하세요,\n\n이번 주 폐렴구균 백신 종합 업무 보고서입니다.\n임원용 요약본과 실무자용 상세본 두 가지를 함께 보내드립니다.\n\n{body}\n\n---\nClaude AI 자동 발송"
    msg.attach(MIMEText(text, "plain", "utf-8"))
    with smtplib.SMTP_SSL("smtp.naver.com", 465) as s:
        s.login(N, P)
        s.sendmail(N, ",".join(RECIPIENTS), msg.as_string())
    print(f"✅ 주간 보고서 발송 완료! (수신자: {', '.join(RECIPIENTS)})")

if __name__ == "__main__":
    print("주간 보고서 작성 중...")
    report = get_weekly_report()
    print("이메일 발송 중...")
    send_email(report)
    print("완료!")
