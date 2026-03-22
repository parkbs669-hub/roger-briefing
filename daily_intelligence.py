"""
폐렴구균 백신 주간 인텔리전스 시스템 v3
네이버 뉴스 추가
"""
import os, smtplib, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from g2b_collector         import collect_g2b_notices
from pubmed_collector      import collect_pneumo_papers
from kdca_collector        import collect_kdca
from mfds_collector        import collect_mfds
from hira_collector        import collect_hira
from naver_news_collector  import collect_naver_news
from claude_agent          import analyze_with_claude

NAVER_ADDRESS  = os.environ.get("NAVER_ADDRESS", "")
NAVER_PASSWORD = os.environ.get("NAVER_PASSWORD", "")


def send_email(subject, body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = NAVER_ADDRESS
    msg["To"]      = NAVER_ADDRESS

    lines = body.split("\n")
    html_lines = []
    for line in lines:
        if line.startswith("# "):
            html_lines.append(f"<h2 style='color:#1a3a5c;border-bottom:2px solid #1a3a5c;padding-bottom:5px;margin-top:25px;'>{line[2:]}</h2>")
        elif line.startswith("## "):
            html_lines.append(f"<h3 style='color:#2563a8;margin-top:18px;'>{line[3:]}</h3>")
        elif line.startswith("### "):
            html_lines.append(f"<h4 style='color:#333;margin-top:12px;'>{line[4:]}</h4>")
        elif line.startswith("- ") or line.startswith("* "):
            html_lines.append(f"<li style='margin:4px 0;'>{line[2:]}</li>")
        elif line.strip() == "":
            html_lines.append("<br>")
        else:
            html_lines.append(f"<p style='margin:4px 0;'>{line}</p>")

    today = datetime.date.today().strftime("%Y년 %m월 %d일")
    html = f"""
<html><body style="font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:20px;color:#333;">
<div style="background:linear-gradient(135deg,#1a3a5c,#2563a8);color:white;padding:25px;border-radius:10px;margin-bottom:25px;">
  <h1 style="margin:0;font-size:22px;">💉 폐렴구균 백신 인텔리전스</h1>
  <p style="margin:8px 0 0;opacity:0.85;font-size:13px;">{today} | 6개 데이터 소스 자동 수집</p>
</div>
<div style="line-height:1.8;">
{"".join(html_lines)}
</div>
<hr style="margin-top:30px;border:1px solid #eee;">
<p style="color:#999;font-size:11px;text-align:center;">
  📊 데이터: 나라장터 · 네이버뉴스 · PubMed · 질병관리청 · 식약처 · 심평원<br>
  🤖 AI 분석: Claude Haiku (Anthropic)<br>
  ⏰ 자동 발송: GitHub Actions (매주 월요일 오전 7시)
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
    print(f"  💉 폐렴구균 백신 주간 인텔리전스 v3")
    print(f"  {today}")
    print(f"{'='*60}")

    print("\n[1/6] 나라장터 수집 중...")
    g2b = collect_g2b_notices()
    print(f"  → {len(g2b)}건")

    print("\n[2/6] 네이버 뉴스 수집 중...")
    news = collect_naver_news()
    print(f"  → {len(news)}건")

    print("\n[3/6] PubMed 수집 중...")
    pubmed = collect_pneumo_papers()
    print(f"  → {len(pubmed)}건")

    print("\n[4/6] 질병관리청 수집 중...")
    kdca = collect_kdca()
    print(f"  → {len(kdca)}건")

    print("\n[5/6] 식약처 수집 중...")
    mfds = collect_mfds()
    print(f"  → {len(mfds)}건")

    print("\n[6/6] 심평원 수집 중...")
    hira = collect_hira()
    print(f"  → {len(hira)}건")

    print("\n[AI] Claude 종합 분석 중...")
    report = analyze_with_claude(g2b, pubmed, kdca, mfds, hira, news)
    print("  → 분석 완료")

    print("\n[📧] 이메일 발송 중...")
    subject = f"💉 폐렴구균 백신 주간 인텔리전스 — {today}"
    send_email(subject, report)

    print(f"\n{'='*60}")
    print("  ✅ 완료!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
