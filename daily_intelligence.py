"""
폐렴구균 백신 일일 인텔리전스 시스템
실행: python daily_intelligence.py

데이터 수집:
  - 나라장터 API (입찰공고)
  - PubMed API (최신 논문)

AI 분석:
  - Gemini 1.5 Flash (무료)

결과:
  - 이메일 발송 (네이버 SMTP)
"""
import os
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 수집기 임포트
from g2b_collector import collect_g2b_notices
from pubmed_collector import collect_pneumo_papers
from gemini_agent import analyze_with_gemini

# 환경변수
NAVER_ADDRESS  = os.environ.get("NAVER_ADDRESS", "")
NAVER_PASSWORD = os.environ.get("NAVER_PASSWORD", "")
TO_EMAIL       = NAVER_ADDRESS  # 본인에게 발송


def send_email(subject, body):
    """네이버 SMTP로 이메일 발송"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = NAVER_ADDRESS
    msg["To"]      = TO_EMAIL

    # HTML 형식으로 변환 (줄바꿈 처리)
    html_body = body.replace("\n", "<br>").replace("# ", "<h2>").replace("## ", "<h3>")
    html = f"""
<html><body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
<div style="background: #1a3a5c; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
  <h1 style="margin:0;">💉 폐렴구균 백신 인텔리전스</h1>
  <p style="margin:5px 0 0 0; opacity:0.8;">{datetime.date.today().strftime('%Y년 %m월 %d일')}</p>
</div>
<div style="line-height: 1.8; color: #333;">
{html_body}
</div>
<hr style="margin-top:30px;">
<p style="color:#999; font-size:12px;">
  📊 데이터 출처: 나라장터(조달청), PubMed(NIH)<br>
  🤖 AI 분석: Google Gemini 1.5 Flash<br>
  ⏰ 자동 발송: GitHub Actions
</p>
</body></html>"""

    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.naver.com", 465) as server:
            server.login(NAVER_ADDRESS, NAVER_PASSWORD)
            server.send_message(msg)
        print(f"  ✅ 이메일 발송 완료 → {TO_EMAIL}")
    except Exception as e:
        print(f"  ❌ 이메일 발송 실패: {e}")


def main():
    today = datetime.date.today().strftime("%Y년 %m월 %d일")
    print(f"\n{'='*60}")
    print(f"  💉 폐렴구균 백신 일일 인텔리전스 시스템")
    print(f"  {today}")
    print(f"{'='*60}")

    # 1단계: 나라장터 수집
    print("\n[1/3] 나라장터 입찰공고 수집 중...")
    g2b_data = collect_g2b_notices()
    print(f"  → 총 {len(g2b_data)}건 수집 완료")

    # 2단계: PubMed 수집
    print("\n[2/3] PubMed 최신 논문 수집 중...")
    pubmed_data = collect_pneumo_papers()
    print(f"  → 총 {len(pubmed_data)}건 수집 완료")

    # 3단계: Gemini AI 분석
    print("\n[3/3] Gemini AI 종합 분석 중...")
    report = analyze_with_gemini(g2b_data, pubmed_data)
    print("  → 분석 완료")

    # 이메일 발송
    print("\n📧 이메일 발송 중...")
    subject = f"💉 폐렴구균 백신 인텔리전스 브리핑 — {today}"
    send_email(subject, report)

    print(f"\n{'='*60}")
    print("  ✅ 모든 작업 완료!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
