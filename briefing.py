"""
폐렴구균 백신 뉴스 자동 브리핑 스크립트
매일 아침 GitHub Actions에서 실행됩니다.
"""

import os
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import anthropic

# ─────────────────────────────────────────
# 설정값 (GitHub Secrets에서 자동으로 불러옴)
# ─────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GMAIL_ADDRESS     = os.environ["GMAIL_ADDRESS"]      # 발신 Gmail 주소
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"] # Gmail 앱 비밀번호
RECIPIENT_EMAIL   = "parkbs669@naver.com"

# ─────────────────────────────────────────
# Claude API 호출 - 뉴스 수집 + 요약
# ─────────────────────────────────────────
def get_briefing() -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    today = datetime.date.today().strftime("%Y년 %m월 %d일")

    prompt = f"""
오늘({today}) 폐렴구균 백신(PCV20, PCV21) 관련 최신 뉴스를 검색하고 상세 브리핑을 작성해 주세요.

## 검색 키워드 (모두 검색)
- 한국어: 폐렴구균 백신, PCV20 20가, PCV21 21가, 폐렴구균 시장 동향
- 영어: pneumococcal vaccine PCV20 PCV21 news, Prevnar 20, Capvaxive, pneumococcal market 2025 2026

## 브리핑 형식
아래 카테고리별로 정리하되, 해당 뉴스가 없는 카테고리는 생략:

━━━━━━━━━━━━━━━━━━━━━━━━
📈 시장/경쟁 동향
━━━━━━━━━━━━━━━━━━━━━━━━
[기사별]
■ 제목 (출처, 날짜)
• 배경: ...
• 핵심 내용: ...
• 시장 영향: ...
• 시사점: ...

━━━━━━━━━━━━━━━━━━━━━━━━
📋 임상/허가 동향
━━━━━━━━━━━━━━━━━━━━━━━━
[동일 형식]

━━━━━━━━━━━━━━━━━━━━━━━━
🏥 접종 정책
━━━━━━━━━━━━━━━━━━━━━━━━
[동일 형식]

━━━━━━━━━━━━━━━━━━━━━━━━
🔬 연구/학술
━━━━━━━━━━━━━━━━━━━━━━━━
[동일 형식]

━━━━━━━━━━━━━━━━━━━━━━━━
🌏 기타 동향
━━━━━━━━━━━━━━━━━━━━━━━━
[동일 형식]

마지막에 오늘의 핵심 시사점 2~3줄 요약 추가.
"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )

    # 텍스트 블록만 추출
    result = ""
    for block in response.content:
        if hasattr(block, "text"):
            result += block.text

    return result.strip()


# ─────────────────────────────────────────
# 이메일 발송
# ─────────────────────────────────────────
def send_email(body: str):
    today = datetime.date.today().strftime("%Y년 %m월 %d일")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[폐렴구균 백신 동향] {today} 뉴스 브리핑"
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = RECIPIENT_EMAIL

    # 텍스트 본문
    intro = f"안녕하세요,\n\n오늘({today}) 폐렴구균 백신(PCV20/PCV21) 시장 동향 브리핑입니다.\n\n"
    outro = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n이 브리핑은 Claude AI가 자동 수집·분석한 내용입니다.\n"
    full_body = intro + body + outro

    msg.attach(MIMEText(full_body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())

    print(f"✅ 이메일 발송 완료 → {RECIPIENT_EMAIL}")


# ─────────────────────────────────────────
# 실행
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("🔍 뉴스 수집 중...")
    briefing = get_briefing()
    print("📧 이메일 발송 중...")
    send_email(briefing)
    print("🎉 완료!")
