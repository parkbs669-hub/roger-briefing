"""
엽산 일일 데이터 브리핑 (무료 버전)
매일 오전 8시 자동 실행 - 5개 소스 수집 후 이메일 발송
"""

import os
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from g2b_collector        import collect_g2b_notices
from naver_news_collector import collect_naver_news
from pubmed_collector     import collect_folate_papers
from kdca_collector       import collect_kdca
from mfds_collector       import collect_mfds

NAVER_ADDRESS  = os.environ.get("NAVER_ADDRESS", "")
NAVER_PASSWORD = os.environ.get("NAVER_PASSWORD", "")

def fmt_g2b(items):
    if not items:
        return "<p style='color:#888;'>최근 7일 신규 공고 없음</p>"
    rows = ""
    for i in items:
        title     = i.get("bidNtceNm", i.get("prdctClsfcNoNm", "제목 없음"))
        org       = i.get("ntceInsttNm", i.get("dminsttNm", ""))
        date      = i.get("bidNtceDt", i.get("rgstDt", ""))[:10] if i.get("bidNtceDt") or i.get("rgstDt") else ""
        price     = i.get("asignBdgtAmt", i.get("presmptPrce", ""))
        url       = i.get("bidNtceUrl", "")
        price_str = f"{int(price):,}원" if price and str(price).isdigit() else (price or "")
        link_str  = f"<a href='{url}' style='color:#1a73e8;'>공고보기</a>" if url else ""
        rows += f"""
        <tr>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;'>{title}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{org}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{date}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#e67e22;'>{price_str}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;'>{link_str}</td>
        </tr>"""
    return f"""<table width='100%' style='border-collapse:collapse;font-size:13px;'>
      <tr style='background:#f8f9fa;'><th style='padding:8px;text-align:left;'>공고명</th><th style='padding:8px;text-align:left;'>기관</th><th style='padding:8px;text-align:left;'>날짜</th><th style='padding:8px;text-align:left;'>금액</th><th style='padding:8px;text-align:left;'>링크</th></tr>
      {rows}</table>"""

def fmt_naver(items):
    if not items:
        return "<p style='color:#888;'>오늘 관련 뉴스 없음</p>"
    rows = ""
    for i in items:
        title    = i.get("title", "제목 없음")
        desc     = i.get("description", "")[:80] + "..." if len(i.get("description", "")) > 80 else i.get("description", "")
        date     = i.get("pubDate", "")[:16] if i.get("pubDate") else ""
        link     = i.get("link", "")
        link_str = f"<a href='{link}' style='color:#1a73e8;'>기사보기</a>" if link else ""
        rows += f"""
        <tr>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;'><b>{title}</b><br><span style='color:#777;font-size:12px;'>{desc}</span></td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;white-space:nowrap;'>{date}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;'>{link_str}</td>
        </tr>"""
    return f"""<table width='100%' style='border-collapse:collapse;font-size:13px;'>
      <tr style='background:#f8f9fa;'><th style='padding:8px;text-align:left;'>제목 / 요약</th><th style='padding:8px;text-align:left;'>날짜</th><th style='padding:8px;text-align:left;'>링크</th></tr>
      {rows}</table>"""

def fmt_pubmed(items):
    if not items:
        return "<p style='color:#888;'>최근 관련 학술 데이터 없음</p>"
    rows = ""
    for i in items:
        title    = i.get("title", "제목 없음")
        authors  = i.get("authors", "")
        journal  = i.get("journal", "")
        year     = i.get("year", "")
        pmid     = i.get("pmid", "")
        link     = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "#"
        rows += f"""
        <tr>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;'><b>{title}</b><br><span style='color:#777;font-size:12px;'>{authors}</span></td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{journal}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{year}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;'><a href='{link}' style='color:#1a73e8;'>PubMed</a></td>
        </tr>"""
    return f"""<table width='100%' style='border-collapse:collapse;font-size:13px;'>
      <tr style='background:#f8f9fa;'><th style='padding:8px;text-align:left;'>제목 / 저자</th><th style='padding:8px;text-align:left;'>저널</th><th style='padding:8px;text-align:left;'>연도</th><th style='padding:8px;text-align:left;'>링크</th></tr>
      {rows}</table>"""

def fmt_kdca(items):
    if not items:
        return "<p style='color:#888;'>관련 통계 데이터 없음</p>"
    cards = ""
    for i in items:
        year    = i.get("year", "").replace("년", "")
        disease = i.get("icdNm", i.get("diseaseNm", "관련 지표"))
        group   = i.get("icdGroupNm", "")
        count   = i.get("resultVal", i.get("patntCnt", "0"))
        cards += f"""
        <div style='display:inline-block;background:#fff5f5;border:1px solid #fcc;border-left:4px solid #e74c3c;border-radius:6px;padding:12px 16px;margin:4px;min-width:200px;vertical-align:top;'>
          <div style='font-size:15px;font-weight:bold;color:#c0392b;'>{disease}</div>
          <div style='font-size:12px;color:#888;margin:4px 0;'>{group} | {year}년</div>
          <div style='font-size:22px;font-weight:bold;color:#e74c3c;'>{count}<span style='font-size:13px;color:#888;'>건</span></div>
        </div>"""
    return f"<div style='padding:4px;'>{cards}</div>"

def fmt_mfds(items):
    if not items:
        return "<p style='color:#888;'>최근 승인 내역 없음</p>"
    rows = ""
    for i in items:
        sample   = i.get("SAMPLE_TYPE", i.get("sampleType", "의약품"))
        company  = i.get("MANUF_ENTP_NAME", i.get("manufEntpName", ""))
        date_raw = i.get("RESULT_TIME", i.get("resultTime", ""))
        date     = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:8]}" if len(str(date_raw)) == 8 else date_raw
        rows += f"<tr><td style='padding:8px;border-bottom:1px solid #f0f0f0;'><b>{sample}</b></td><td style='padding:8px;border-bottom:1px solid #f0f0f0;'>{company}</td><td style='padding:8px;border-bottom:1px solid #f0f0f0;'>{date}</td></tr>"
    return f"<table width='100%' style='border-collapse:collapse;font-size:13px;'><tr style='background:#f8f9fa;'><th style='padding:8px;text-align:left;'>제품명</th><th style='padding:8px;text-align:left;'>제조사</th><th style='padding:8px;text-align:left;'>승인일</th></tr>{rows}</table>"

def build_html_email(today_str, g2b, news, pubmed, kdca, mfds):
    total = len(g2b) + len(news) + len(pubmed) + len(kdca) + len(mfds)
    def card(emoji, name, badge, color):
        return f"<td style='padding:4px;'><div style='background:white;border-radius:8px;padding:12px 6px;text-align:center;border-top:3px solid {color};box-shadow:0 1px 3px rgba(0,0,0,0.08);'><div style='font-size:20px;'>{emoji}</div><div style='font-size:11px;color:#666;margin:2px 0;'>{name}</div><div style='font-size:18px;font-weight:bold;color:{color};'>{badge}</div></div></td>"
    def section(emoji, title, count, color, content):
        return f"<div style='margin-bottom:28px;'><div style='background:{color};color:white;padding:10px 16px;border-radius:6px 6px 0 0;'><b>{emoji} {title}</b><span style='float:right;background:rgba(255,255,255,0.3);padding:2px 10px;border-radius:122px;font-size:12px;'>{count}건</span></div><div style='border:1px solid #e0e0e0;border-top:none;padding:12px;border-radius:0 0 6px 6px;background:#fff;'>{content}</div></div>"

    return f"""<!DOCTYPE html><html><body style='font-family:sans-serif;background:#f5f5f5;padding:20px;'><div style='max-width:720px;margin:0 auto;'>
    <div style='background:linear-gradient(135deg,#2e7d32,#4caf50);color:white;padding:24px;border-radius:10px;text-align:center;'>
      <div style='font-size:22px;font-weight:bold;'>💊 엽산(Folate) 일일 데이터 브리핑</div>
      <div style='opacity:0.85;font-size:14px;'>{today_str} | 총 {total}건 수집</div>
    </div>
    <table width='100%' style='margin:20px 0;'><tr>
      {card("🏛️", "공고", f"{len(g2b)}건", "#e67e22")}
      {card("📰", "뉴스", f"{len(news)}건", "#3498db")}
      {card("🔬", "논문", f"{len(pubmed)}건", "#9b59b6")}
      {card("🏥", "현황", f"{len(kdca)}건", "#e74c3c")}
      {card("💊", "식약처", f"{len(mfds)}건", "#1abc9c")}
    </tr></table>
    {section("🏛️", "나라장터 엽산 관련 공고", len(g2b), "#e67e22", fmt_g2b(g2b))}
    {section("📰", "국내 엽산 최신 뉴스", len(news), "#3498db", fmt_naver(news))}
    {section("🔬", "PubMed 최신 엽산 연구", len(pubmed), "#9b59b6", fmt_pubmed(pubmed))}
    {section("🏥", "질병관리청 관련 지표", len(kdca), "#e74c3c", fmt_kdca(kdca))}
    {section("💊", "식약처 엽산 제제 승인현황", len(mfds), "#1abc9c", fmt_mfds(mfds))}
    </div></body></html>"""

def send_email(subject, html_body):
    if not NAVER_ADDRESS or not NAVER_PASSWORD: return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"], msg["From"], msg["To"] = subject, NAVER_ADDRESS, NAVER_ADDRESS
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        with smtplib.SMTP_SSL("smtp.naver.com", 465) as s:
            s.login(NAVER_ADDRESS, NAVER_PASSWORD)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"이메일 오류: {e}"); return False

def main():
    today_str = datetime.date.today().strftime("%Y년 %m월 %d일")
    print(f"=== 엽산 데이터 브리핑 시작 ({today_str}) ===")
    g2b = collect_g2b_notices()
    news = collect_naver_news()
    pubmed = collect_folate_papers()
    kdca = collect_kdca()
    mfds = collect_mfds()
    total = len(g2b) + len(news) + len(pubmed) + len(kdca) + len(mfds)
    send_email(f"💊 엽산 브리핑 — {today_str} ({total}건)", build_html_email(today_str, g2b, news, pubmed, kdca, mfds))
    print(f"=== 완료 (총 {total}건) ===")

if __name__ == "__main__":
    main()
