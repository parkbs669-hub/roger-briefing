import os, smtplib, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import anthropic

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
NAVER_ADDRESS = os.environ["NAVER_ADDRESS"]
NAVER_PASSWORD = os.environ["NAVER_PASSWORD"]
RECIPIENT_EMAIL = "parkbs669@naver.com"

def get_briefing():
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    today = datetime.date.today().strftime("%Y년 %m월 %d일")
    prompt = f"오늘({today}) 폐렴구균 백신 PCV20 PCV21 관련 최신 뉴스를 한국어와 영어로 검색하고, 시장동향/임상허가/접종정책/연구학술 카테고리로 상세히 요약해주세요."
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )
    return "".join(b.text for b in response.content if hasattr(b, "text")).strip()

def send_email(body):
    today = datetime.date.today().strftime("%Y년 %m월 %d일")
    msg = MIMEMultipart()
    msg["Subject"] = f"[폐렴구균 백신 동향] {today} 브리핑"
    msg["From"] = NAVER_ADDRESS
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(f"안녕하세요,\n\n{today} 브리핑입니다.\n\n{body}\n\n※ Claude AI 자동 발송", "plain", "utf-8"))
    with smtplib.SMTP_SSL("smtp.naver.com", 465) as s:
        s.login(NAVER_ADDRESS, NAVER_PASSWORD)
        s.sendmail(NAVER_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
    print("✅ 발송 완료!")

if __name__ == "__main__":
    print("🔍 뉴스 수집 중...")
    send_email(get_briefing())
    print("🎉 완료!")
