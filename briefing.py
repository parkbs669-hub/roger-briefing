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
    prompt = f"""오늘({today}) 폐렴구균 백신(PCV20, PCV21) 관련 최신 뉴스를 한국어와 영어로 검색하고 상세 브리핑을 작성해 주세요.

검색 키워드:
- 한국어: 폐렴구균 백신, PCV20 20가, PCV21 21가, 폐렴구균 시장 동향
- 영어: pneumococcal vaccine PCV20 PCV21 news, Prevnar 20, Capvaxive

아래 카테고리별로 정리 (해당 없으면 생략):
[시장/경쟁 동향] [임상/허가 동향] [접종 정책] [연구/학술] [기타 동향]

각 기사마다 배경, 핵심내용, 시장영향, 시사점을 상세히 작성해주세요."""

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
    msg["Subject"] = f"[폐렴구균 백신 동향] {today} 뉴스 브리핑"
    msg["From"] = NAVER_ADDRESS
    msg["To"] = RECIPIENT_EMAIL
    text = f"안녕하세요,\n\n{today} 폐렴구균 백신 시장 동향 브리핑입니다.\n\n{body}\n\n---\nClaude AI 자동 발송"
    msg.attach(MIMEText(text, "plain", "utf-8"))
    with smtplib.SMTP_SSL("smtp.naver.com", 465) as s:
        s.login(NAVER_ADDRESS, NAVER_PASSWORD)
        s.sendmail(NAVER_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
    print("이메일 발송 완료!")

if __name__ == "__main__":
    print("뉴스 수집 중...")
    briefing = get_briefing()
    print("이메일 발송 중...")
    send_email(briefing)
    print("완료!")
