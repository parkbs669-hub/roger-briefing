"""
폐렴구균 백신 일일 인텔리전스 시스템 (5개 API 통합)
실행: python daily_intelligence.py
"""
import os, smtplib, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from g2b_collector    import collect_g2b_notices
from pubmed_collector import collect_pneumo_papers
from kdca_collector   import collect_kdca
from mfds_collector   import collect_mfds
from hira_collector   import collect_hira
from gemini_agent     import analyze_with_gemini

NAVER_ADDRESS  = os.environ.get("NAVER_ADDRESS", "")
NAVER_PASSWORD = os.environ.get("NAVER_PASSWORD", "")


def send_email(subject, body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = NAVER_ADDRESS
    msg["To"]      = NAVER_ADDRESS

    # 마크다운 → HTML 간단 변환
    html_body = body
    for h2 in ["## "]:
        lines = html_body.split("\n")
        new_lines = []
        for line in lines:
            if line.startswith("# "):
                line = f"<h2 style='color:#1a3a5c;border-bottom:2px solid #1a3a5c;padding-bottom:5px;'>{line[2:]}</h2>"
            elif line.startswith("## "):
                line = f"<h3 style='color:#2563a8;margin-top:20px;'>{line[3:]}</h3>"
            elif line.startswith("- "):
                line = f"<li>{line[2:]}</li>"
            else:
                line = line + "<br>"
            new_lines.append(line)
        html_body = "\n".join(new_lines)

    today = datetime.date.today().strftime("%Y년 %m월 %d일")
    html = f"""
<html><body style="font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:20px;color:#333;">
<div style="background:linear-gradient(135deg,#1a3a5c,#2563a8);color:white;padding:25px;border-radius:10px;margin-bottom:25px;">
  <h1 style="margin:0;font-size:24px;">💉 폐렴구균 백신 인텔리전스</h1>
  <p style="margin:8px 0 0;opacity:0.85;">{today} | 5개 공공 API 자동 수집</p>
</div>
<div style="line-height:1.8;">
{html_body}
</div>
<hr style="margin-top:30px;border:1px solid #eee;">
<p style="color:#999;font-size:11px;text-align:center;">
  📊 데이터: 나라장터(조달청) · PubMed(NIH) · 질병관리청 · 식약처 · 심평원<br>
  🤖 AI 분석: Google Gemini 2.0 Flash (무료)<br>
  ⏰ 자동 발송: GitHub Actions (매일 오전 8시)
</p>
</body></html>"""

    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        with smtplib.SMTP_SSL("smtp.naver.com", 465) as s:
            s.login(NAVER_ADDRESS, NAVER_PASSWORD)
            s.send_message(msg)
        print(f"  ✅ 이메일 발송 완료 → {NAVER_ADDRESS}")
    except Exception as e:
        print(f"  ❌ 이메일 실패: {e}")


def main():
    today = datetime.date.today().strftime("%Y년 %m월 %d일")
    print(f"\n{'='*60}")
    print(f"  💉 폐렴구균 백신 일일 인텔리전스")
    print(f"  {today}")
    print(f"{'='*60}")

    print("\n[1/5] 나라장터 수집 중...")
    g2b = collect_g2b_notices()

    print("\n[2/5] PubMed 수집 중...")
    pubmed = collect_pneumo_papers()

    print("\n[3/5] 질병관리청 수집 중...")
    kdca = collect_kdca()

    print("\n[4/5] 식약처 수집 중...")
    mfds = collect_mfds()

    print("\n[5/5] 심평원 수집 중...")
    hira = collect_hira()

    print("\n[AI] Gemini 종합 분석 중...")
    report = analyze_with_gemini(g2b, pubmed, kdca, mfds, hira)

    print("\n[📧] 이메일 발송 중...")
    subject = f"💉 폐렴구균 백신 인텔리전스 — {today}"
    send_email(subject, report)

    print(f"\n{'='*60}")
    print("  ✅ 완료!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
