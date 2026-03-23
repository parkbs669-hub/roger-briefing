"""
폐렴구균 백신 일일 데이터 브리핑 (무료 버전)
매일 오전 8시 자동 실행 - 6개 소스 수집 후 이메일 발송
"""

import os
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# 수집기 임포트
from g2b_collector        import collect_g2b_notices
from naver_news_collector import collect_naver_news
from pubmed_collector     import collect_pneumo_papers
from kdca_collector       import collect_kdca
from mfds_collector       import collect_mfds

# 이메일 설정
NAVER_ADDRESS  = os.environ.get("NAVER_ADDRESS", "")
NAVER_PASSWORD = os.environ.get("NAVER_PASSWORD", "")


# ────────────────────────────────────────────
# 데이터 포맷 함수
# ────────────────────────────────────────────

def fmt_g2b(items):
    if not items:
        return "<p style='color:#888;'>최근 7일 신규 공고 없음</p>"
    rows = ""
    for i in items:
        title  = i.get("bidNtceNm", i.get("prdctClsfcNoNm", "제목 없음"))
        org    = i.get("ntceInsttNm", i.get("dminsttNm", ""))
        date   = i.get("bidNtceDt", i.get("rgstDt", ""))[:10] if i.get("bidNtceDt") or i.get("rgstDt") else ""
        price  = i.get("asignBdgtAmt", i.get("presmptPrce", ""))
        url    = i.get("bidNtceUrl", "")
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
    return f"""
    <table width='100%' style='border-collapse:collapse;font-size:13px;'>
      <tr style='background:#f8f9fa;'>
        <th style='padding:8px;text-align:left;'>공고명</th>
        <th style='padding:8px;text-align:left;'>기관</th>
        <th style='padding:8px;text-align:left;'>날짜</th>
        <th style='padding:8px;text-align:left;'>금액</th>
        <th style='padding:8px;text-align:left;'>링크</th>
      </tr>
      {rows}
    </table>"""


def fmt_naver(items):
    if not items:
        return "<p style='color:#888;'>오늘 관련 뉴스 없음</p>"
    rows = ""
    for i in items:
        title = i.get("title", "제목 없음")
        desc  = i.get("description", "")[:80] + "..." if len(i.get("description","")) > 80 else i.get("description","")
        date  = i.get("pubDate", "")[:16] if i.get("pubDate") else ""
        link  = i.get("link", "")
        link_str = f"<a href='{link}' style='color:#1a73e8;'>기사보기</a>" if link else ""
        rows += f"""
        <tr>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;'>
            <b>{title}</b><br>
            <span style='color:#777;font-size:12px;'>{desc}</span>
          </td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;white-space:nowrap;'>{date}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;'>{link_str}</td>
        </tr>"""
    return f"""
    <table width='100%' style='border-collapse:collapse;font-size:13px;'>
      <tr style='background:#f8f9fa;'>
        <th style='padding:8px;text-align:left;'>제목 / 요약</th>
        <th style='padding:8px;text-align:left;'>날짜</th>
        <th style='padding:8px;text-align:left;'>링크</th>
      </tr>
      {rows}
    </table>"""


def fmt_pubmed(items):
    if not items:
        return "<p style='color:#888;'>최근 논문 없음</p>"
    rows = ""
    for i in items:
        title   = i.get("title", i.get("Title", "제목 없음"))
        authors = i.get("authors", i.get("Authors", ""))
        journal = i.get("journal", i.get("Journal", ""))
        year    = i.get("year", i.get("Year", ""))
        pmid    = i.get("pmid", i.get("PMID", ""))
        link    = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""
        link_str = f"<a href='{link}' style='color:#1a73e8;'>PubMed</a>" if link else ""
        rows += f"""
        <tr>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;'>
            <b>{title}</b><br>
            <span style='color:#777;font-size:12px;'>{authors}</span>
          </td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{journal}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{year}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;'>{link_str}</td>
        </tr>"""
    return f"""
    <table width='100%' style='border-collapse:collapse;font-size:13px;'>
      <tr style='background:#f8f9fa;'>
        <th style='padding:8px;text-align:left;'>제목 / 저자</th>
        <th style='padding:8px;text-align:left;'>저널</th>
        <th style='padding:8px;text-align:left;'>연도</th>
        <th style='padding:8px;text-align:left;'>링크</th>
      </tr>
      {rows}
    </table>"""


def fmt_kdca(items):
    if not items:
        return "<p style='color:#888;'>질병관리청 데이터 없음</p>"
    cards = ""
    for i in items:
        year    = i.get("year", "").replace("년", "")
        disease = i.get("icdNm", i.get("diseaseNm", ""))
        group   = i.get("icdGroupNm", "")
        count   = i.get("resultVal", i.get("patntCnt", ""))
        url     = "https://dportal.kdca.go.kr/pot/is/inftnsdsEDW.do"
        cards += f"""
        <div style='display:inline-block;background:#fff5f5;border:1px solid #fcc;
                    border-left:4px solid #e74c3c;border-radius:6px;padding:12px 16px;
                    margin:4px;min-width:200px;vertical-align:top;'>
          <div style='font-size:15px;font-weight:bold;color:#c0392b;'>{disease}</div>
          <div style='font-size:12px;color:#888;margin:4px 0;'>{group} &nbsp;|&nbsp; {year}년 누계</div>
          <div style='font-size:22px;font-weight:bold;color:#e74c3c;'>{count}<span style='font-size:13px;color:#888;'>건</span></div>
          <div style='margin-top:6px;'>
            <a href='{url}' style='font-size:11px;color:#1a73e8;'>질병관리청 상세보기 →</a>
          </div>
        </div>"""
    return f"""
    <div style='padding:4px;'>{cards}</div>
    <p style='color:#aaa;font-size:11px;margin-top:8px;'>
      ※ 출처: 질병관리청 감염병포털 (방역통합정보시스템 전수신고 기준)
    </p>"""


def fmt_mfds(items):
    if not items:
        return "<p style='color:#888;'>최근 국가출하승인 내역 없음 (신규 출하 시 표시됩니다)</p>"
    rows = ""
    for i in items:
        product  = i.get("GOODS_NAME", i.get("goodsName", ""))
        sample   = i.get("SAMPLE_TYPE", i.get("sampleType", ""))
        company  = i.get("MANUF_ENTP_NAME", i.get("manufEntpName", ""))
        lot      = i.get("MAKE_NO", i.get("makeNo", ""))
        date_raw = i.get("RESULT_TIME", i.get("resultTime", ""))
        date     = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:8]}" if len(str(date_raw)) == 8 else date_raw
        rows += f"""
        <tr>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;'><b>{sample}</b></td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{product}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{company}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{lot}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{date}</td>
        </tr>"""
    return f"""
    <table width='100%' style='border-collapse:collapse;font-size:13px;'>
      <tr style='background:#f8f9fa;'>
        <th style='padding:8px;text-align:left;'>제품명</th>
        <th style='padding:8px;text-align:left;'>성분명</th>
        <th style='padding:8px;text-align:left;'>제조사</th>
        <th style='padding:8px;text-align:left;'>Lot No.</th>
        <th style='padding:8px;text-align:left;'>승인일</th>
      </tr>
      {rows}
    </table>"""



# ────────────────────────────────────────────
# HTML 이메일 생성
# ────────────────────────────────────────────

def build_html_email(today_str, g2b, news, pubmed, kdca, mfds):
    total = len(g2b) + len(news) + len(pubmed) + len(kdca) + len(mfds)

    # ── KDCA 배지: 질병 항목 수(1건) 대신 실제 감염 누계 건수 표시 ──
    kdca_total = sum(
        int(i.get("resultVal", i.get("patntCnt", 0)) or 0)
        for i in kdca
    )
    kdca_badge = f"{kdca_total}건" if kdca_total else "0건"

    # ── 요약 카드 1개 생성 헬퍼 ──
    def card(emoji, name, badge, color):
        return (
            f"<td style='padding:4px;'>"
            f"<div style='background:white;border-radius:8px;padding:12px 6px;"
            f"text-align:center;border-top:3px solid {color};"
            f"box-shadow:0 1px 3px rgba(0,0,0,0.08);'>"
            f"<div style='font-size:20px;'>{emoji}</div>"
            f"<div style='font-size:11px;color:#666;margin:2px 0;'>{name}</div>"
            f"<div style='font-size:18px;font-weight:bold;color:{color};'>{badge}</div>"
            f"</div></td>"
        )

    def section(emoji, title, count, color, content):
        return f"""
        <div style='margin-bottom:28px;'>
          <div style='background:{color};color:white;padding:10px 16px;border-radius:6px 6px 0 0;'>
            <b>{emoji} {title}</b>
            <span style='float:right;background:rgba(255,255,255,0.3);
                         padding:2px 10px;border-radius:12px;font-size:12px;'>{count}건</span>
          </div>
          <div style='border:1px solid #e0e0e0;border-top:none;padding:12px;
                      border-radius:0 0 6px 6px;background:#fff;'>
            {content}
          </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset='utf-8'></head>
<body style='font-family:Apple SD Gothic Neo,Malgun Gothic,sans-serif;
             background:#f5f5f5;margin:0;padding:20px;'>
  <div style='max-width:720px;margin:0 auto;'>

    <!-- 헤더 -->
    <div style='background:linear-gradient(135deg,#1a237e,#1565c0);
                color:white;padding:24px;border-radius:10px;margin-bottom:20px;
                text-align:center;'>
      <div style='font-size:22px;font-weight:bold;margin-bottom:4px;'>
        💉 폐렴구균 백신 일일 인텔리전스 브리핑
      </div>
      <div style='opacity:0.85;font-size:14px;'>{today_str} &nbsp;|&nbsp;
        총 {total}건 수집 &nbsp;|&nbsp; 자동 발송 (GitHub Actions)
      </div>
    </div>

    <!-- 요약 카드 (table 레이아웃 - 이메일 클라이언트 완벽 호환, 6개 한 줄) -->
    <table width='100%' cellspacing='0' cellpadding='0'
           style='margin-bottom:20px;table-layout:fixed;'>
      <tr>
        {card("🏛️", "나라장터",   f"{len(g2b)}건",    "#e67e22")}
        {card("📰",  "네이버뉴스", f"{len(news)}건",   "#3498db")}
        {card("🔬",  "PubMed",     f"{len(pubmed)}건", "#9b59b6")}
        {card("🏥",  "질병관리청", kdca_badge,         "#e74c3c")}
        {card("💊",  "식약처",     f"{len(mfds)}건",   "#1abc9c")}
      </tr>
    </table>

    <!-- 각 섹션 -->
    {section("🏛️","나라장터 입찰공고",   len(g2b),    "#e67e22", fmt_g2b(g2b))}
    {section("📰","국내 최신 뉴스",      len(news),   "#3498db", fmt_naver(news))}
    {section("🔬","최신 논문",           len(pubmed), "#9b59b6", fmt_pubmed(pubmed))}
    {section("🏥","질병관리청 감염병 현황", kdca_total, "#e74c3c", fmt_kdca(kdca))}
    {section("💊","식약처 국가출하승인",  len(mfds),  "#1abc9c", fmt_mfds(mfds))}

    <!-- 푸터 -->
    <div style='text-align:center;color:#aaa;font-size:12px;
                padding:16px;border-top:1px solid #e0e0e0;margin-top:8px;'>
      📊 데이터 출처: 나라장터 · 네이버뉴스 · PubMed · 질병관리청 · 식약처<br>
      🤖 자동 발송: GitHub Actions (매일 오전 8시) &nbsp;|&nbsp; 💰 비용: 0원<br>
      🧠 AI 분석 브리핑은 매주 월요일 오전 7시 별도 발송
    </div>

  </div>
</body>
</html>"""


# ────────────────────────────────────────────
# 이메일 발송
# ────────────────────────────────────────────

def send_email(subject, html_body):
    if not NAVER_ADDRESS or not NAVER_PASSWORD:
        print("  ⚠️ 이메일 설정 없음")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = NAVER_ADDRESS
        msg["To"]      = NAVER_ADDRESS
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        with smtplib.SMTP_SSL("smtp.naver.com", 465) as s:
            s.login(NAVER_ADDRESS, NAVER_PASSWORD)
            s.send_message(msg)
        print("  ✅ 이메일 발송 완료 →", NAVER_ADDRESS.split("@")[0] + "@***")
        return True
    except Exception as e:
        print(f"  ❌ 이메일 오류: {e}")
        return False


# ────────────────────────────────────────────
# 메인
# ────────────────────────────────────────────

def main():
    today     = datetime.date.today()
    today_str = today.strftime("%Y년 %m월 %d일")

    print("=" * 60)
    print(f"  💉 폐렴구균 백신 일일 데이터 브리핑 (무료 버전)")
    print(f"  {today_str}")
    print("=" * 60)

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

    print("\n[5/5] 식약처 수집 중...")
    mfds = collect_mfds()
    print(f"  → {len(mfds)}건")

    total = len(g2b) + len(news) + len(pubmed) + len(kdca) + len(mfds)

    print("\n[📧] 이메일 발송 중...")
    subject   = f"💉 폐렴구균 백신 브리핑 — {today_str} ({total}건 수집)"
    html_body = build_html_email(today_str, g2b, news, pubmed, kdca, mfds)
    send_email(subject, html_body)

    print("\n" + "=" * 60)
    print(f"  ✅ 완료! 총 {total}건 수집")
    print(f"  💰 비용: 0원")
    print("=" * 60)


if __name__ == "__main__":
    main()
