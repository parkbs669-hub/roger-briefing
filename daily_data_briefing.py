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
from pubmed_collector     import collect_pubmed
from kdca_collector       import collect_kdca
from mfds_collector       import collect_mfds
from hira_collector       import collect_hira

# 이메일 설정
NAVER_ADDRESS  = os.environ.get("NAVER_ADDRESS", "")
NAVER_PASSWORD = os.environ.get("NAVER_PASSWORD", "")


# ────────────────────────────────────────────
# 데이터 포맷 함수
# ────────────────────────────────────────────

def fmt_g2b(items):
    """나라장터 입찰공고 포맷"""
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
    """네이버 뉴스 포맷"""
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
    """PubMed 논문 포맷"""
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
    """질병관리청 감염병 발생현황 포맷"""
    if not items:
        return "<p style='color:#888;'>질병관리청 데이터 없음</p>"
    rows = ""
    for i in items:
        year     = i.get("year", "")
        disease  = i.get("icdNm", i.get("diseaseNm", ""))
        group    = i.get("icdGroupNm", "")
        count    = i.get("resultVal", i.get("patntCnt", ""))
        pat_type = i.get("patntType", "")
        rows += f"""
        <tr>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;'><b>{disease}</b></td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{group}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{pat_type}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#e74c3c;text-align:right;'>{count}건</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{year}</td>
        </tr>"""
    return f"""
    <table width='100%' style='border-collapse:collapse;font-size:13px;'>
      <tr style='background:#f8f9fa;'>
        <th style='padding:8px;text-align:left;'>감염병명</th>
        <th style='padding:8px;text-align:left;'>분류</th>
        <th style='padding:8px;text-align:left;'>환자구분</th>
        <th style='padding:8px;text-align:right;'>발생수</th>
        <th style='padding:8px;text-align:left;'>연도</th>
      </tr>
      {rows}
    </table>"""


def fmt_mfds(items):
    """식약처 국가출하승인 포맷"""
    if not items:
        return "<p style='color:#888;'>식약처 데이터 없음</p>"
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
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;'><b>{product}</b></td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{sample}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{company}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{lot}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{date}</td>
        </tr>"""
    return f"""
    <table width='100%' style='border-collapse:collapse;font-size:13px;'>
      <tr style='background:#f8f9fa;'>
        <th style='padding:8px;text-align:left;'>제품명</th>
        <th style='padding:8px;text-align:left;'>백신명</th>
        <th style='padding:8px;text-align:left;'>제조사</th>
        <th style='padding:8px;text-align:left;'>Lot No.</th>
        <th style='padding:8px;text-align:left;'>승인일</th>
      </tr>
      {rows}
    </table>"""


def fmt_hira(items):
    """심평원 약가기준 포맷 - 폐렴구균 백신만 필터링"""
    if not items:
        return "<p style='color:#888;'>심평원 데이터 없음</p>"

    # 폐렴구균 백신 관련 키워드 필터
    vaccine_keywords = ["프리베나", "신플로릭스", "뉴모박스", "캡박시브", "폐렴구균", "pneumo", "Prevnar", "Synflorix"]
    filtered = [i for i in items if any(
        kw.lower() in str(i.get("itmNm","")).lower() for kw in vaccine_keywords
    )]
    # 필터 결과 없으면 전체 표시
    display_items = filtered if filtered else items

    rows = ""
    for i in display_items:
        name      = i.get("itmNm", "")
        company   = i.get("mnfEntpNm", i.get("cpnyNm", ""))
        price     = i.get("mxPatntAmt", i.get("uprcAmt", ""))
        start_dt  = i.get("adtStaDd", i.get("aplYmd", ""))
        # 날짜 포맷
        if len(str(start_dt)) == 8:
            start_dt = f"{start_dt[:4]}-{start_dt[4:6]}-{start_dt[6:8]}"
        price_str = f"{int(price):,}원" if price and str(price).replace('.','').isdigit() else (price or "-")
        rows += f"""
        <tr>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;'><b>{name}</b></td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{company}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#27ae60;text-align:right;'>{price_str}</td>
          <td style='padding:8px;border-bottom:1px solid #f0f0f0;color:#555;'>{start_dt}</td>
        </tr>"""
    return f"""
    <table width='100%' style='border-collapse:collapse;font-size:13px;'>
      <tr style='background:#f8f9fa;'>
        <th style='padding:8px;text-align:left;'>품목명</th>
        <th style='padding:8px;text-align:left;'>제조사</th>
        <th style='padding:8px;text-align:right;'>최대환자부담금</th>
        <th style='padding:8px;text-align:left;'>적용일</th>
      </tr>
      {rows}
    </table>"""


# ────────────────────────────────────────────
# HTML 이메일 생성
# ────────────────────────────────────────────

def build_html_email(today_str, g2b, news, pubmed, kdca, mfds, hira):
    total = len(g2b) + len(news) + len(pubmed) + len(kdca) + len(mfds) + len(hira)

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
        총 {total}건 수집 &nbsp;|&nbsp;
        자동 발송 (GitHub Actions)
      </div>
    </div>

    <!-- 요약 카드 -->
    <div style='display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap;'>
      {"".join([
        f"<div style='flex:1;min-width:90px;background:white;border-radius:8px;"
        f"padding:12px;text-align:center;border-top:3px solid {c};box-shadow:0 1px 3px rgba(0,0,0,0.08);'>"
        f"<div style='font-size:20px;'>{e}</div>"
        f"<div style='font-size:11px;color:#666;margin:2px 0;'>{n}</div>"
        f"<div style='font-size:18px;font-weight:bold;color:{c};'>{v}건</div></div>"
        for e,n,v,c in [
            ("🏛️","나라장터",len(g2b),"#e67e22"),
            ("📰","네이버뉴스",len(news),"#3498db"),
            ("🔬","PubMed",len(pubmed),"#9b59b6"),
            ("🏥","질병관리청",len(kdca),"#e74c3c"),
            ("💊","식약처",len(mfds),"#1abc9c"),
            ("💰","심평원",len(hira),"#27ae60"),
        ]
      ])}
    </div>

    <!-- 각 섹션 -->
    {section("🏛️","나라장터 입찰공고",len(g2b),"#e67e22",fmt_g2b(g2b))}
    {section("📰","국내 최신 뉴스",len(news),"#3498db",fmt_naver(news))}
    {section("🔬","최신 논문",len(pubmed),"#9b59b6",fmt_pubmed(pubmed))}
    {section("🏥","질병관리청 감염병 현황",len(kdca),"#e74c3c",fmt_kdca(kdca))}
    {section("💊","식약처 국가출하승인",len(mfds),"#1abc9c",fmt_mfds(mfds))}
    {section("💰","심평원 약가/급여",len(hira),"#27ae60",fmt_hira(hira))}

    <!-- 푸터 -->
    <div style='text-align:center;color:#aaa;font-size:12px;
                padding:16px;border-top:1px solid #e0e0e0;margin-top:8px;'>
      📊 데이터 출처: 나라장터 · 네이버뉴스 · PubMed · 질병관리청 · 식약처 · 심평원<br>
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

    # 1. 나라장터
    print("\n[1/6] 나라장터 수집 중...")
    g2b = collect_g2b_notices()
    print(f"  → {len(g2b)}건")

    # 2. 네이버 뉴스
    print("\n[2/6] 네이버 뉴스 수집 중...")
    news = collect_naver_news()
    print(f"  → {len(news)}건")

    # 3. PubMed
    print("\n[3/6] PubMed 수집 중...")
    pubmed = collect_pubmed()
    print(f"  → {len(pubmed)}건")

    # 4. 질병관리청
    print("\n[4/6] 질병관리청 수집 중...")
    kdca = collect_kdca()
    print(f"  → {len(kdca)}건")

    # 5. 식약처
    print("\n[5/6] 식약처 수집 중...")
    mfds = collect_mfds()
    print(f"  → {len(mfds)}건")

    # 6. 심평원
    print("\n[6/6] 심평원 수집 중...")
    hira = collect_hira()
    print(f"  → {len(hira)}건")

    total = len(g2b) + len(news) + len(pubmed) + len(kdca) + len(mfds) + len(hira)

    # 이메일 발송
    print("\n[📧] 이메일 발송 중...")
    subject   = f"💉 폐렴구균 백신 브리핑 — {today_str} ({total}건 수집)"
    html_body = build_html_email(today_str, g2b, news, pubmed, kdca, mfds, hira)
    send_email(subject, html_body)

    print("\n" + "=" * 60)
    print(f"  ✅ 완료! 총 {total}건 수집")
    print(f"  💰 비용: 0원")
    print("=" * 60)


if __name__ == "__main__":
    main()
