import os, smtplib, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import anthropic

A = os.environ["ANTHROPIC_API_KEY"]
N = os.environ["NAVER_ADDRESS"]
P = os.environ["NAVER_PASSWORD"]
R = "parkbs669@naver.com"

def get_nip_briefing():
    client = anthropic.Anthropic(api_key=A)
    today = datetime.date.today().strftime("%Y년 %m월 %d일")

    prompt = f"""오늘({today}) 기준 최신 정보를 검색하고 한국어로 상세 브리핑을 작성해 주세요.

## 검색 대상 사이트 (반드시 포함)
- 질병관리청 공식 사이트: kdca.go.kr
- 예방접종도우미: nip.kdca.go.kr
- 보건복지부: mohw.go.kr
- 건강보험심사평가원: hira.or.kr
- 국민건강보험공단: nhis.or.kr

## 검색 키워드
- 질병관리청 폐렴구균 공지 2026
- 보건소 폐렴구균 예방접종 정책
- 국가예방접종 NIP 폐렴구균 변경
- 성인 폐렴구균 접종 보건소
- 폐렴구균 건강보험 급여 2026
- pneumococcal vaccine Korea NIP policy 2026

## 브리핑 형식

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏥 질병관리청 최신 공지사항
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 공지 제목 (날짜)
• 주요 내용:
• 시행일:
• 현장 영향:
• 보건소 대응 필요사항:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💉 전국 보건소 예방접종 정책 현황
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 정책명
• 대상자:
• 접종 백신:
• 보건소 무료 접종 여부:
• 지역별 차이:
• 변경 예정 사항:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 국가예방접종(NIP) 사업 동향
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 사업명
• 현황:
• 변경사항:
• 예산/지원 현황:
• 향후 계획:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💊 건강보험 급여 동향
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 폐렴구균 백신 급여 현황:
• 변경 예정 사항:
• 본인부담금 현황:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🗺 시도별 특이 동향
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 서울/경기 등 주요 지역 보건소 정책 차이
• 지역별 접종률 현황
• 특별 캠페인 진행 지역

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 오늘의 핵심 시사점
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1.
2.
3.

해당 정보가 없는 카테고리는 "오늘 해당 없음"으로 표시해주세요."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=5000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )
    return "".join(b.text for b in response.content if hasattr(b, "text")).strip()

def send_email(body):
    today = datetime.date.today().strftime("%Y년 %m월 %d일")
    msg = MIMEMultipart()
    msg["Subject"] = f"[보건소/NIP 정책 동향] {today}"
    msg["From"] = N
    msg["To"] = R
    text = f"안녕하세요,\n\n{today} 보건소 및 국가예방접종(NIP) 정책 동향 브리핑입니다.\n\n{body}\n\n---\nClaude AI 자동 발송"
    msg.attach(MIMEText(text, "plain", "utf-8"))
    with smtplib.SMTP_SSL("smtp.naver.com", 465) as s:
        s.login(N, P)
        s.sendmail(N, R, msg.as_string())
    print("NIP 트래커 발송 완료!")

if __name__ == "__main__":
    print("보건소/NIP 정책 수집 중...")
    briefing = get_nip_briefing()
    print("이메일 발송 중...")
    send_email(briefing)
    print("완료!")
