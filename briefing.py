import os
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import anthropic

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
NAVER_ADDRESS     = os.environ["NAVER_ADDRESS"]
NAVER_PASSWORD    = os.environ["NAVER_PASSWORD"]
RECIPIENT_EMAIL   = "parkbs669@naver.com"

def get_briefing():
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    today = datetime.date.today().strftime("%Y년 %m월 %d일")
    prompt = f"""
오늘({today}) 폐렴구균 백신(PCV20, PCV21) 관련 최신 뉴스를 검색하고 상세 브리핑을 작성해 주세요.

검색 키워드:
- 한국어: 폐렴구균 백신, PCV20 20가, PCV21 21가, 폐렴구균 시장 동향
- 영어: pneumococcal vaccine PCV20 PCV21 news, Prevnar 20, Capvaxive

아래 카테고리별로 정리 (해당 없으면 생략):

━━━━━━━━━━━━━━━━━━━━━━━━
📈 시장/경쟁 동향
━━━━━━━━━━━━━━━━━━━━━━━━
[기사별]
■ 제목 (출처, 날짜)
- 배경: ...
- 핵심 내용: ...
- 시장 영향: ...
- 시사점: ...

━━━━━━━━━━━━━━━━━━━━━━━━
📋 임상/허가 동향
━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━
🏥 접종 정책
━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━
🔬 연구/학술
━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━
🌏 기타 동향
━━━━━━━━━━━━━━━━━━━━━━━━

마지막에 오늘의 핵심 시사점 2~3줄 요약.
"""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )
    result = ""
    for block in response.content:
        if hasattr(block, "text"):
            result += block.text
    return result.strip()

def send_email(body):
    today = datetime.date.today().strftime("%Y년 %m월 %d일")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[폐렴구균 백신 동향] {today} 뉴스 브리핑"
    msg["From"]    = NAVER_ADDRESS
    msg["To"]      = RECIPIENT_EMAIL
    intro = f"안녕하세요,\n\n오늘({today}) 폐렴구균 백신(PCV20/PCV21) 시장 동향 브리핑입니다.\n\n"
    outro = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n이 브리핑은 Claude AI가 자동 수집·분석한 내용입니다.\n"
    full_body = intro + body + outro
    msg.attach(MIMEText(full_body, "plain", "utf-8"))
    with smtplib.SMTP_SSL("smtp.naver.com", 465) as server:
        server.login(NAVER_ADDRESS, NAVER_PASSWORD)
        server.sendmail(NAVER_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
    print(f"✅ 이메일 발송 완료 → {RECIPIENT_EMAIL}")

if __name__ == "__main__":
    print("🔍 뉴스 수집 중...")
    briefing = get_briefing()
    print("📧 이메일 발송 중...")
    send_email(briefing)
    print("🎉 완료!")
