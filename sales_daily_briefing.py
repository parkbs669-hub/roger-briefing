"""
영업 통합 데일리 브리핑
- 옵시디언 vault 데이터 (회의록, 방문일지, 마케팅, 미완료 액션)
- 기존 외부 데이터 (네이버 뉴스, G2B, PubMed)
- AI 요약 및 오늘의 액션 플랜 생성
- 이메일 발송
"""
import os
import datetime
import smtplib
import requests
import time
import xml.etree.ElementTree as ET
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sales_collector import (
    collect_sales_reports, collect_meetings, collect_marketing,
    collect_academic, collect_pending_actions, build_summary_text,
)
from ai_processor import generate

# ── 환경 변수 ──────────────────────────────────────────────
NAVER_CLIENT_ID     = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")
PUBLIC_DATA_API_KEY = os.environ.get("PUBLIC_DATA_API_KEY", "")
NAVER_ADDRESS       = os.environ.get("NAVER_ADDRESS", "")
NAVER_PASSWORD      = os.environ.get("NAVER_PASSWORD", "")
REPORT_RECIPIENTS   = os.environ.get("REPORT_RECIPIENTS", NAVER_ADDRESS)


# ═══════════════════════════════════════════════════════════
# 외부 데이터 수집 (기존 로직 간소화)
# ═══════════════════════════════════════════════════════════

def _naver_news(keywords: list[str], display: int = 3) -> list[dict]:
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
    items, seen = [], set()
    for kw in keywords:
        try:
            r = requests.get(url, headers=headers, params={"query": kw, "display": display, "sort": "date"}, timeout=10)
            for i in r.json().get("items", []):
                t = i.get("title", "").replace("<b>", "").replace("</b>", "")
                if t not in seen:
                    seen.add(t)
                    items.append({"title": t, "link": i.get("link", ""), "pubDate": i.get("pubDate", "")[:16], "keyword": kw})
        except Exception:
            continue
    return items


def _g2b_bids(keywords: list[str]) -> list[dict]:
    url = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoThngPPSSrch"
    start = (datetime.datetime.now() - datetime.timedelta(days=3)).strftime("%Y%m%d0000")
    end = datetime.datetime.now().strftime("%Y%m%d2359")
    items, seen = [], set()
    for kw in keywords:
        try:
            r = requests.get(url, params={"ServiceKey": PUBLIC_DATA_API_KEY, "inqryDiv": "1",
                "inqryBgnDt": start, "inqryEndDt": end, "bidNtceNm": kw, "numOfRows": "5", "type": "xml"}, timeout=10)
            root = ET.fromstring(r.text.strip())
            for item in root.findall(".//item"):
                d = {c.tag: (c.text or "") for c in item}
                bid_no = d.get("bidNtceNo", "")
                if bid_no and bid_no not in seen:
                    seen.add(bid_no)
                    items.append(d)
        except Exception:
            continue
    return items


# ═══════════════════════════════════════════════════════════
# AI 섹션 생성
# ═══════════════════════════════════════════════════════════

def _make_ai_section(vault_summary: str, news: list[dict]) -> str:
    news_text = "\n".join([f"- {n['title']} ({n['keyword']})" for n in news[:10]])
    today = datetime.date.today().strftime("%Y-%m-%d (%A)")

    prompt = f"""오늘 날짜: {today}

[나의 최근 영업 활동 데이터]
{vault_summary}

[오늘의 주요 뉴스]
{news_text}

위 데이터를 바탕으로 다음을 한국어로 작성해주세요:

1. **오늘의 영업 핵심 포인트** (3줄 이내)
   - 어제/최근 활동 중 오늘 이어서 할 것
   - 오늘 특별히 집중할 제품/고객

2. **우선 처리 액션 리스트** (미완료 항목 기반, 최대 5개)
   - 긴급도 순으로 정렬

3. **오늘 활용할 뉴스/인사이트** (1-2개)
   - 의사 방문 시 대화에 활용할 수 있는 내용

4. **이번 주 진행 상황 한 줄 요약**
"""
    system = "당신은 제약영업 전문가 어시스턴트입니다. 간결하고 실용적으로 답변하세요."
    return generate(prompt, system)


# ═══════════════════════════════════════════════════════════
# HTML 빌더
# ═══════════════════════════════════════════════════════════

def _css_card(color: str) -> str:
    return f"border:1px solid #ddd; border-radius:8px; overflow:hidden; margin-bottom:24px; background:#fff;"


def _section_header(title: str, color: str, icon: str) -> str:
    return f"<div style='background:{color}; color:#fff; padding:10px 15px; font-size:15px; font-weight:bold;'>{icon} {title}</div>"


def _ai_section_html(ai_text: str) -> str:
    html_lines = []
    for line in ai_text.splitlines():
        line = line.strip()
        if not line:
            html_lines.append("<br>")
        elif line.startswith("**") and line.endswith("**"):
            html_lines.append(f"<h4 style='color:#2c3e50; margin:16px 0 6px 0;'>{line.strip('*')}</h4>")
        elif line.startswith("- ") or line.startswith("• "):
            html_lines.append(f"<li style='margin:4px 0; font-size:13px;'>{line[2:]}</li>")
        elif line.startswith("#"):
            html_lines.append(f"<h4 style='color:#2c3e50; margin:16px 0 6px 0;'>{line.lstrip('#').strip()}</h4>")
        else:
            html_lines.append(f"<p style='font-size:13px; margin:4px 0;'>{line}</p>")
    return "<ul style='padding-left:20px; margin:0;'>" + "".join(html_lines) + "</ul>"


def _docs_html(items: list[dict]) -> str:
    if not items:
        return "<p style='color:#999; font-size:13px;'>최근 기록 없음</p>"
    rows = ""
    for item in items[:8]:
        title = item.get("title", "")
        date  = item.get("date", "")
        # 본문 첫 줄 요약
        first_line = ""
        for line in item.get("body", "").splitlines():
            line = line.strip().lstrip("#").strip()
            if line and not line.startswith("---"):
                first_line = line[:60]
                break
        rows += f"""<tr>
            <td style='padding:7px 8px; border-bottom:1px solid #ecf0f1; font-size:12px; color:#888; white-space:nowrap;'>{date}</td>
            <td style='padding:7px 8px; border-bottom:1px solid #ecf0f1; font-size:13px; font-weight:bold;'>{title}</td>
            <td style='padding:7px 8px; border-bottom:1px solid #ecf0f1; font-size:12px; color:#555;'>{first_line}</td>
        </tr>"""
    return f"""<table width='100%' style='border-collapse:collapse;'>
        <thead><tr>
            <th style='padding:7px 8px; text-align:left; background:#f4f6f7; font-size:12px; border-bottom:2px solid #bdc3c7;'>날짜</th>
            <th style='padding:7px 8px; text-align:left; background:#f4f6f7; font-size:12px; border-bottom:2px solid #bdc3c7;'>제목</th>
            <th style='padding:7px 8px; text-align:left; background:#f4f6f7; font-size:12px; border-bottom:2px solid #bdc3c7;'>내용 요약</th>
        </tr></thead><tbody>{rows}</tbody></table>"""


def _pending_html(pending: list[str]) -> str:
    if not pending:
        return "<p style='color:#27ae60; font-size:13px;'>미완료 항목 없음</p>"
    items = "".join([f"<li style='margin:5px 0; font-size:13px;'>{p}</li>" for p in pending[:15]])
    return f"<ul style='padding-left:18px; margin:0;'>{items}</ul>"


def _news_html(news: list[dict]) -> str:
    if not news:
        return "<p style='color:#999; font-size:13px;'>뉴스 없음</p>"
    rows = ""
    for n in news[:10]:
        rows += f"""<tr>
            <td style='padding:7px 8px; border-bottom:1px solid #ecf0f1; font-size:12px; color:#888;'>{n['pubDate']}</td>
            <td style='padding:7px 8px; border-bottom:1px solid #ecf0f1; font-size:13px;'>
                <a href='{n['link']}' style='color:#3498db; text-decoration:none;'>{n['title']}</a>
            </td>
            <td style='padding:7px 8px; border-bottom:1px solid #ecf0f1; font-size:12px; color:#888;'>{n['keyword']}</td>
        </tr>"""
    return f"<table width='100%' style='border-collapse:collapse;'><tbody>{rows}</tbody></table>"


def _bids_html(bids: list[dict]) -> str:
    if not bids:
        return "<p style='color:#999; font-size:13px;'>최근 3일 내 신규 공고 없음</p>"
    rows = ""
    for b in bids[:8]:
        url = b.get("bidNtceUrl", "#")
        rows += f"""<tr>
            <td style='padding:7px 8px; border-bottom:1px solid #ecf0f1; font-size:13px;'>{b.get('bidNtceNm','')}</td>
            <td style='padding:7px 8px; border-bottom:1px solid #ecf0f1; font-size:12px;'>{b.get('ntceInsttNm','')}</td>
            <td style='padding:7px 8px; border-bottom:1px solid #ecf0f1; font-size:12px;'>{b.get('bidNtceDt','')[:10]}</td>
            <td style='padding:7px 8px; border-bottom:1px solid #ecf0f1; font-size:12px;'>
                <a href='{url}' style='color:#3498db;'>공고보기</a>
            </td>
        </tr>"""
    return f"<table width='100%' style='border-collapse:collapse;'><tbody>{rows}</tbody></table>"


# ═══════════════════════════════════════════════════════════
# 메인
# ═══════════════════════════════════════════════════════════

def main():
    today_str = datetime.date.today().strftime("%Y년 %m월 %d일")
    weekday = ["월", "화", "수", "목", "금", "토", "일"][datetime.date.today().weekday()]
    print(f"🚀 {today_str} ({weekday}) 영업 데일리 브리핑 시작")

    # 1. vault 데이터 수집
    sales     = collect_sales_reports(days=7)
    meetings  = collect_meetings(days=7)
    marketing = collect_marketing(days=14)
    academic  = collect_academic(days=14)
    pending   = collect_pending_actions()
    vault_summary = build_summary_text()
    print(f"  vault: 영업보고{len(sales)}건, 회의{len(meetings)}건, 마케팅{len(marketing)}건, 미완료{len(pending)}건")

    # 2. 외부 데이터 수집
    news_keywords = ["폐렴구균 백신", "대상포진 백신", "싱그릭스", "타파미디스", "빈다맥스", "캡박시브"]
    news = _naver_news(news_keywords)
    bids = _g2b_bids(["폐렴구균", "대상포진", "타파미디스"])
    print(f"  외부: 뉴스{len(news)}건, 입찰{len(bids)}건")

    # 3. AI 요약
    ai_text = _make_ai_section(vault_summary, news)
    print("  AI 요약 완료")

    # 4. HTML 조립
    html = f"""<!DOCTYPE html>
<html><body style='font-family:"Malgun Gothic","Apple SD Gothic Neo",sans-serif; background:#f0f2f5; padding:20px; margin:0;'>
<div style='max-width:820px; margin:0 auto;'>

  <!-- 헤더 -->
  <div style='text-align:center; margin-bottom:28px;'>
    <h1 style='color:#2c3e50; margin:0 0 4px;'>🏃 영업 데일리 브리핑</h1>
    <p style='color:#7f8c8d; margin:0;'>{today_str} ({weekday}요일)</p>
  </div>

  <!-- AI 오늘의 액션 플랜 -->
  <div style='{_css_card("#e8f4fd")}'>
    {_section_header("AI 오늘의 액션 플랜", "#2980b9", "🤖")}
    <div style='padding:15px;'>{_ai_section_html(ai_text)}</div>
  </div>

  <!-- 미완료 후속 조치 -->
  <div style='{_css_card("")}'>
    {_section_header(f"미완료 후속 조치 ({len(pending)}건)", "#e67e22", "⚠️")}
    <div style='padding:15px;'>{_pending_html(pending)}</div>
  </div>

  <!-- 최근 영업 활동 -->
  <div style='{_css_card("")}'>
    {_section_header(f"최근 영업 활동 ({len(sales)}건)", "#27ae60", "📋")}
    <div style='padding:15px;'>{_docs_html(sales)}</div>
  </div>

  <!-- 최근 회의·파트너 협의 -->
  <div style='{_css_card("")}'>
    {_section_header(f"최근 회의·파트너 협의 ({len(meetings)}건)", "#8e44ad", "🤝")}
    <div style='padding:15px;'>{_docs_html(meetings)}</div>
  </div>

  <!-- 시장 뉴스 -->
  <div style='{_css_card("")}'>
    {_section_header(f"오늘의 시장 뉴스 ({len(news)}건)", "#3498db", "📰")}
    <div style='padding:15px;'>{_news_html(news)}</div>
  </div>

  <!-- G2B 입찰 -->
  <div style='{_css_card("")}'>
    {_section_header(f"나라장터 신규 입찰 ({len(bids)}건)", "#e74c3c", "🏛️")}
    <div style='padding:15px;'>{_bids_html(bids)}</div>
  </div>

  <p style='color:#bbb; font-size:11px; text-align:center; margin-top:30px;'>
    자동 생성 | roger-briefing | 옵시디언 vault 데이터 기반
  </p>
</div>
</body></html>"""

    # 5. 이메일 발송
    if not NAVER_ADDRESS or not NAVER_PASSWORD:
        print("⚠️  이메일 계정 정보 없음 → HTML만 출력")
        print(html[:500])
        return

    recipients = [r.strip() for r in REPORT_RECIPIENTS.split(",") if r.strip()] or [NAVER_ADDRESS]
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏃 영업 데일리 브리핑 [{today_str} {weekday}]"
    msg["From"]    = NAVER_ADDRESS
    msg["To"]      = ", ".join(recipients)
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.naver.com", 465) as s:
            s.login(NAVER_ADDRESS, NAVER_PASSWORD)
            s.send_message(msg)
        print(f"✅ 발송 완료 → {', '.join(recipients)}")
    except Exception as e:
        print(f"❌ 발송 실패: {e}")


if __name__ == "__main__":
    main()
