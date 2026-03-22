"""
폐렴구균 백신 일일 데이터 브리핑 (AI 분석 없음 - 완전 무료)
매일 오전 8시 자동 실행
"""
import os, smtplib, datetime, json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from g2b_collector        import collect_g2b_notices
from pubmed_collector     import collect_pneumo_papers
from kdca_collector       import collect_kdca
from mfds_collector       import collect_mfds
from hira_collector       import collect_hira
from naver_news_collector import collect_naver_news

NAVER_ADDRESS  = os.environ.get("NAVER_ADDRESS", "")
NAVER_PASSWORD = os.environ.get("NAVER_PASSWORD", "")


def build_html(today, g2b, news, pubmed, kdca, mfds, hira):
    """HTML 이메일 본문 생성"""

    # 나라장터 섹션
    g2b_html = ""
    if g2b:
        for item in g2b[:5]:
            price = item.get("presmptPrce", "0") or "0"
            try: price_fmt = f"{int(float(price)):,}원"
            except: price_fmt = "미정"
            deadline = item.get("bidClseDt", "-")
            # 마감 임박 체크 (3일 이내)
            badge = ""
            try:
                dl = datetime.datetime.strptime(deadline[:10], "%Y-%m-%d")
                diff = (dl - datetime.datetime.now()).days
                if diff <= 3:
                    badge = f"<span style='background:#e53e3e;color:white;padding:2px 8px;border-radius:10px;font-size:11px;margin-left:8px;'>마감 {diff}일!</span>"
            except: pass

            g2b_html += f"""
<div style="background:#f0f7ff;border-left:4px solid #2563a8;padding:12px;margin:8px 0;border-radius:0 8px 8px 0;">
  <div style="font-weight:bold;color:#1a3a5c;">{item.get('bidNtceNm','-')}{badge}</div>
  <div style="color:#666;font-size:13px;margin-top:4px;">
    🏛 {item.get('ntceInsttNm','-')} &nbsp;|&nbsp;
    📅 공고: {item.get('bidNtceDt','-')[:10]} &nbsp;|&nbsp;
    ⏰ 마감: {deadline[:10]} &nbsp;|&nbsp;
    💰 {price_fmt}
  </div>
</div>"""
    else:
        g2b_html = "<div style='color:#999;padding:10px;'>최근 7일 신규 공고 없음</div>"

    # 네이버 뉴스 섹션
    news_html = ""
    if news:
        for item in news[:8]:
            news_html += f"""
<div style="border-bottom:1px solid #eee;padding:10px 0;">
  <div style="font-weight:bold;color:#1a3a5c;font-size:14px;">
    📰 {item.get('title','-')}
  </div>
  <div style="color:#666;font-size:12px;margin-top:3px;">
    {item.get('description','')[:120]}...
  </div>
  <div style="color:#999;font-size:11px;margin-top:3px;">
    🔑 키워드: {item.get('keyword','')} &nbsp;|&nbsp; 📅 {item.get('pubDate','')[:16]}
  </div>
</div>"""
    else:
        news_html = "<div style='color:#999;padding:10px;'>오늘 관련 뉴스 없음</div>"

    # PubMed 섹션
    pubmed_html = ""
    if pubmed:
        for p in pubmed[:3]:
            pubmed_html += f"""
<div style="background:#f5f0ff;border-left:4px solid #6b46c1;padding:12px;margin:8px 0;border-radius:0 8px 8px 0;">
  <div style="font-weight:bold;color:#44337a;font-size:13px;">{p.get('title','-')}</div>
  <div style="color:#666;font-size:12px;margin-top:4px;">
    📚 {p.get('journal','-')} ({p.get('year','-')}) &nbsp;|&nbsp;
    👤 {p.get('authors','-')[:50]}
  </div>
  <div style="color:#555;font-size:12px;margin-top:4px;">{p.get('abstract','')[:150]}...</div>
  <div style="margin-top:4px;">
    <a href="{p.get('url','')}" style="color:#6b46c1;font-size:12px;">🔗 논문 보기</a>
  </div>
</div>"""
    else:
        pubmed_html = "<div style='color:#999;padding:10px;'>최근 30일 신규 논문 없음</div>"

    # 질병관리청/식약처/심평원 섹션
    def make_gov_section(data, label, color):
        if data:
            rows = ""
            for item in data[:3]:
                rows += f"<div style='padding:6px 0;border-bottom:1px solid #eee;font-size:13px;'>{str(item)[:200]}</div>"
            return rows
        return f"<div style='color:#999;padding:10px;'>{label} 데이터 없음</div>"

    kdca_html = make_gov_section(kdca, "질병관리청", "#e65100")
    mfds_html = make_gov_section(mfds, "식약처", "#880e4f")
    hira_html = make_gov_section(hira, "심평원", "#2e7d32")

    # 통계 요약
    total = len(g2b) + len(news) + len(pubmed) + len(kdca) + len(mfds) + len(hira)

    html = f"""
<html><body style="font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:20px;color:#333;">

<!-- 헤더 -->
<div style="background:linear-gradient(135deg,#1a3a5c,#2563a8);color:white;padding:25px;border-radius:10px;margin-bottom:20px;">
  <h1 style="margin:0;font-size:20px;">💉 폐렴구균 백신 일일 데이터 브리핑</h1>
  <p style="margin:8px 0 0;opacity:0.85;font-size:13px;">
    {today} &nbsp;|&nbsp; 총 {total}건 수집 &nbsp;|&nbsp; 🤖 AI 분석 없음 (원시 데이터)
  </p>
</div>

<!-- 수집 현황 요약 -->
<div style="display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;">
  <div style="background:#e8f4fd;padding:10px 15px;border-radius:8px;text-align:center;flex:1;min-width:80px;">
    <div style="font-size:20px;font-weight:bold;color:#2563a8;">{len(g2b)}</div>
    <div style="font-size:11px;color:#666;">나라장터</div>
  </div>
  <div style="background:#fef3c7;padding:10px 15px;border-radius:8px;text-align:center;flex:1;min-width:80px;">
    <div style="font-size:20px;font-weight:bold;color:#d97706;">{len(news)}</div>
    <div style="font-size:11px;color:#666;">뉴스</div>
  </div>
  <div style="background:#f5f0ff;padding:10px 15px;border-radius:8px;text-align:center;flex:1;min-width:80px;">
    <div style="font-size:20px;font-weight:bold;color:#6b46c1;">{len(pubmed)}</div>
    <div style="font-size:11px;color:#666;">논문</div>
  </div>
  <div style="background:#fff3e0;padding:10px 15px;border-radius:8px;text-align:center;flex:1;min-width:80px;">
    <div style="font-size:20px;font-weight:bold;color:#e65100;">{len(kdca)}</div>
    <div style="font-size:11px;color:#666;">질병관리청</div>
  </div>
  <div style="background:#fce4ec;padding:10px 15px;border-radius:8px;text-align:center;flex:1;min-width:80px;">
    <div style="font-size:20px;font-weight:bold;color:#880e4f;">{len(mfds)}</div>
    <div style="font-size:11px;color:#666;">식약처</div>
  </div>
  <div style="background:#e8f5e9;padding:10px 15px;border-radius:8px;text-align:center;flex:1;min-width:80px;">
    <div style="font-size:20px;font-weight:bold;color:#2e7d32;">{len(hira)}</div>
    <div style="font-size:11px;color:#666;">심평원</div>
  </div>
</div>

<!-- 나라장터 -->
<div style="margin-bottom:20px;">
  <h3 style="color:#2563a8;border-bottom:2px solid #2563a8;padding-bottom:5px;">
    🏛 나라장터 입찰공고 ({len(g2b)}건)
  </h3>
  {g2b_html}
</div>

<!-- 네이버 뉴스 -->
<div style="margin-bottom:20px;">
  <h3 style="color:#d97706;border-bottom:2px solid #d97706;padding-bottom:5px;">
    📰 국내 최신 뉴스 ({len(news)}건)
  </h3>
  {news_html}
</div>

<!-- PubMed -->
<div style="margin-bottom:20px;">
  <h3 style="color:#6b46c1;border-bottom:2px solid #6b46c1;padding-bottom:5px;">
    📚 최신 논문 ({len(pubmed)}건)
  </h3>
  {pubmed_html}
</div>

<!-- 질병관리청 -->
<div style="margin-bottom:20px;">
  <h3 style="color:#e65100;border-bottom:2px solid #e65100;padding-bottom:5px;">
    🦠 질병관리청 감염병 현황 ({len(kdca)}건)
  </h3>
  {kdca_html}
</div>

<!-- 식약처 -->
<div style="margin-bottom:20px;">
  <h3 style="color:#880e4f;border-bottom:2px solid #880e4f;padding-bottom:5px;">
    💊 식약처 국가출하승인 ({len(mfds)}건)
  </h3>
  {mfds_html}
</div>

<!-- 심평원 -->
<div style="margin-bottom:20px;">
  <h3 style="color:#2e7d32;border-bottom:2px solid #2e7d32;padding-bottom:5px;">
    💰 심평원 약가/급여 ({len(hira)}건)
  </h3>
  {hira_html}
</div>

<!-- 푸터 -->
<hr style="border:1px solid #eee;margin-top:30px;">
<p style="color:#999;font-size:11px;text-align:center;">
  📊 데이터: 나라장터 · 네이버뉴스 · PubMed · 질병관리청 · 식약처 · 심평원<br>
  ⏰ 자동 발송: GitHub Actions (매일 오전 8시) &nbsp;|&nbsp; 💰 비용: 완전 무료<br>
  🤖 AI 분석 브리핑은 매주 월요일 오전 7시 별도 발송
</p>
</body></html>"""
    return html


def send_email(subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = NAVER_ADDRESS
    msg["To"]      = NAVER_ADDRESS
    msg.attach(MIMEText(html_body, "html", "utf-8"))
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
    print(f"  💉 폐렴구균 백신 일일 데이터 브리핑 (무료 버전)")
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

    print("\n[📧] 이메일 발송 중...")
    total = len(g2b)+len(news)+len(pubmed)+len(kdca)+len(mfds)+len(hira)
    subject = f"💉 폐렴구균 일일 데이터 — {today} ({total}건 수집)"
    html = build_html(today, g2b, news, pubmed, kdca, mfds, hira)
    send_email(subject, html)

    print(f"\n{'='*60}")
    print(f"  ✅ 완료! 총 {total}건 수집")
    print(f"  💰 비용: 0원")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
