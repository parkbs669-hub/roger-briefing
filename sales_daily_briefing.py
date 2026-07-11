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
import base64
import json
from urllib.parse import quote
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

from sales_collector import (
    collect_sales_reports, collect_meetings, collect_marketing,
    collect_academic, collect_emails, collect_pcv20_policy,
    collect_local_policy, collect_pending_actions, build_summary_text,
)
from project_tracker import update_all_projects, build_project_context
from pattern_analyzer import build_pattern_context
from ai_processor import generate

# ── 환경 변수 ──────────────────────────────────────────────
NAVER_CLIENT_ID     = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")
PUBLIC_DATA_API_KEY = os.environ.get("PUBLIC_DATA_API_KEY", "")
NAVER_ADDRESS       = os.environ.get("NAVER_ADDRESS", "")
NAVER_PASSWORD      = os.environ.get("NAVER_PASSWORD", "")
REPORT_RECIPIENTS   = os.environ.get("REPORT_RECIPIENTS", NAVER_ADDRESS)
GH_PAT              = os.environ.get("GH_PAT", "")

# ── 비용 제어 ──────────────────────────────────────────────
MAX_DEEPSEEK_CALLS_PER_DAY = 50  # 일일 최대 AI 호출 횟수 (비용 폭주 방지, 2026-07-11)
_deepseek_call_count = 0  # 오늘의 누적 호출 수


# ═══════════════════════════════════════════════════════════
# vault 직접 저장 (GitHub API)
# ═══════════════════════════════════════════════════════════

def commit_to_vault(markdown: str, filename: str, gh_pat: str):
    owner, repo = "parkbs669-hub", "MyVault_Roger"
    path = f"Emails/{filename}"
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{quote(path)}"
    headers = {
        "Authorization": f"token {gh_pat}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    sha = None
    try:
        r = requests.get(api_url, headers=headers, timeout=15)
        if r.status_code == 200:
            sha = r.json().get("sha")
    except Exception:
        pass

    body = {
        "message": f"chore: 영업브리핑 자동 저장 {filename[:10]}",
        "content": base64.b64encode(markdown.encode("utf-8")).decode("ascii"),
    }
    if sha:
        body["sha"] = sha

    try:
        r = requests.put(api_url, headers=headers, data=json.dumps(body), timeout=30)
        if r.status_code in (200, 201):
            print(f"✅ vault 커밋 완료: {path}")
        else:
            print(f"⚠️  vault 커밋 실패 ({r.status_code}): {r.text[:200]}")
    except Exception as e:
        print(f"⚠️  vault 커밋 오류: {e}")


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

def _check_daily_limit() -> bool:
    """AI 호출 일일 한도 체크 (비용 폭주 방지)."""
    global _deepseek_call_count
    if _deepseek_call_count >= MAX_DEEPSEEK_CALLS_PER_DAY:
        print(f"⚠️  일일 AI 호출 한도 도달 ({MAX_DEEPSEEK_CALLS_PER_DAY}회). 생성 스킵.")
        return False
    _deepseek_call_count += 1
    return True


def _make_ai_section(vault_summary: str, news: list[dict],
                     project_context: str, pattern_context: str) -> str:
    # 일일 한도 체크 (2026-07-11 긴급 조치)
    if not _check_daily_limit():
        return "[AI 호출 일일 한도 도달. 생성이 생략되었습니다.]"

    news_text = "\n".join([f"- {n['title']} ({n['keyword']})" for n in news[:10]])
    today = datetime.datetime.now(KST).date().strftime("%Y-%m-%d (%A)")

    prompt = f"""오늘 날짜: {today}

[나의 최근 영업 활동 데이터]
{vault_summary}

[프로젝트 누적 타임라인 — 쌓인 히스토리]
{project_context}

[누적 영업 패턴 — 지금까지 학습된 것]
{pattern_context}

[오늘의 주요 뉴스]
{news_text}

위 데이터(특히 누적 타임라인과 패턴)를 바탕으로 다음을 한국어로 작성하세요:

1. **오늘의 영업 브리핑** — {today}
   오늘 날짜와 함께 한 문장 상황 요약

2. **오늘의 영업 핵심 포인트**
   - 누적 패턴 기반으로 오늘 가장 효과적인 접근법
   - 프로젝트 진행 상황에서 오늘 집중할 것

3. **우선 처리 액션 리스트** | 순위/항목/긴급도
   - 미완료 항목 + 프로젝트 타임라인 기반, 최대 5개
   - 긴급도(오늘/이번주/이번달) 표시

4. **오늘 활용할 뉴스/인사이트**
   - 의사·기관 방문 시 활용할 수 있는 내용과 활용처 명시

5. **이번 주 진행 상황 한 줄 요약**

6. **오늘의 아이스브레이킹 소재** (3개)
   - 현장 방문·통화 시 어색함을 풀 수 있는 가벼운 대화 소재
   - 최근 시사, 날씨, 스포츠, 건강 트렌드 등에서 선택
   - 각 소재는 한두 문장으로 간결하게 작성

7. **오늘의 짧은 이야기** (2개)
   - 의학/건강/비즈니스 관련 흥미롭거나 유익한 짧은 이야기
   - 현장에서 가볍게 꺼낼 수 있는 내용으로, 각 100자 내외로 작성
"""
    system = "당신은 제약영업 전문가 어시스턴트입니다. 누적 데이터와 패턴을 활용해 점점 더 정교한 조언을 제공하세요."
    return generate(prompt, system)


# ═══════════════════════════════════════════════════════════
# HTML 빌더
# ═══════════════════════════════════════════════════════════

def _css_card(color: str) -> str:
    return f"border:1px solid #ddd; border-radius:8px; overflow:hidden; margin-bottom:24px; background:#fff;"


def _section_header(title: str, color: str, icon: str) -> str:
    return f"<div style='background:{color}; color:#fff; padding:10px 15px; font-size:15px; font-weight:bold;'>{icon} {title}</div>"


def _md_to_html(text: str) -> str:
    html_lines = []
    for line in text.splitlines():
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


def _split_ai_sections(ai_text: str) -> tuple[str, str]:
    """AI 응답을 메인 브리핑과 아이스브레이킹·이야기 섹션으로 분리."""
    for marker in ["오늘의 아이스브레이킹 소재", "오늘의 짧은 이야기"]:
        idx = ai_text.find(marker)
        if idx != -1:
            line_start = ai_text.rfind("\n", 0, idx)
            split_at = line_start if line_start != -1 else idx
            return ai_text[:split_at].strip(), ai_text[split_at:].strip()
    return ai_text, ""


def _ai_section_html(ai_text: str) -> str:
    main_text, _ = _split_ai_sections(ai_text)
    return _md_to_html(main_text)


def _icebreaking_html(ai_text: str) -> str:
    _, ice_text = _split_ai_sections(ai_text)
    if not ice_text:
        return "<p style='color:#999; font-size:13px;'>생성 없음</p>"
    return _md_to_html(ice_text)


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


def _policy_html(items: list[dict]) -> str:
    """정책 자료 목록 — 제목 + 첫 두 줄 요약."""
    if not items:
        return "<p style='color:#999; font-size:13px;'>자료 없음</p>"
    cards = ""
    for item in items:
        title = item.get("title", "")
        # 본문에서 의미 있는 첫 줄 추출
        summary = ""
        for line in item.get("body", "").splitlines():
            line = line.strip().lstrip("#").strip()
            if line and not line.startswith("---") and len(line) > 10:
                summary = line[:80]
                break
        cards += f"""
        <div style='padding:8px 10px; border-left:3px solid #bdc3c7;
                    margin-bottom:8px; background:#fafafa; border-radius:0 4px 4px 0;'>
          <div style='font-size:13px; font-weight:bold; color:#2c3e50;'>{title}</div>
          <div style='font-size:12px; color:#7f8c8d; margin-top:2px;'>{summary}</div>
        </div>"""
    return cards


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
    today_kst = datetime.datetime.now(KST).date()
    today_str = today_kst.strftime("%Y년 %m월 %d일")
    weekday = ["월", "화", "수", "목", "금", "토", "일"][today_kst.weekday()]
    print(f"🚀 {today_str} ({weekday}) 영업 데일리 브리핑 시작")

    # 1. vault 데이터 수집
    sales        = collect_sales_reports(days=7)
    meetings     = collect_meetings(days=7)
    marketing    = collect_marketing(days=14)
    academic     = collect_academic(days=14)
    emails       = collect_emails(days=14)
    pcv20        = collect_pcv20_policy()
    local_policy = collect_local_policy()
    pending      = collect_pending_actions()
    vault_summary = build_summary_text()
    print(f"  vault: 영업{len(sales)}, 회의{len(meetings)}, 이메일{len(emails)}, PCV20정책{len(pcv20)}, 지역정책{len(local_policy)}, 미완료{len(pending)}")

    # 1-1. 복리 데이터: 프로젝트 타임라인 업데이트 + 누적 패턴 로드
    update_all_projects()
    project_context = build_project_context()
    pattern_context = build_pattern_context()
    print("  복리 데이터 로드 완료 (프로젝트 타임라인 + 누적 패턴)")

    # 2. 외부 데이터 수집
    news_keywords = ["폐렴구균 백신", "대상포진 백신", "싱그릭스", "타파미디스", "빈다맥스", "캡박시브"]
    news = _naver_news(news_keywords)
    bids = _g2b_bids(["폐렴구균", "대상포진", "타파미디스"])
    print(f"  외부: 뉴스{len(news)}건, 입찰{len(bids)}건")

    # 3. AI 요약 (복리 컨텍스트 포함)
    ai_text = _make_ai_section(vault_summary, news, project_context, pattern_context)
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

  <!-- 아이스브레이킹 & 짧은 이야기 -->
  <div style='{_css_card("#fffbf0")}'>
    {_section_header("오늘의 아이스브레이킹 & 짧은 이야기", "#f39c12", "💬")}
    <div style='padding:15px;'>{_icebreaking_html(ai_text)}</div>
  </div>

  <!-- 미완료 후속 조치·최근 영업 활동·최근 회의 섹션 제거 (사장님 지시 2026-07-07)
       — 데이터 수집은 AI 요약(섹션 1~3) 입력으로 계속 사용, 출력만 생략 -->

  <!-- 수신 이메일·보고서 -->
  <div style='{_css_card("")}'>
    {_section_header(f"최근 수신 이메일·보고서 ({len(emails)}건)", "#16a085", "📧")}
    <div style='padding:15px;'>{_docs_html(emails)}</div>
  </div>

  <!-- PCV20 정책 근거 자료 -->
  <div style='{_css_card("")}'>
    {_section_header(f"PCV20 정책 근거 자료 ({len(pcv20)}건)", "#8e44ad", "💊")}
    <div style='padding:15px;'>{_policy_html(pcv20)}</div>
  </div>

  <!-- 폐렴구균 지역 정책 -->
  <div style='{_css_card("")}'>
    {_section_header(f"폐렴구균 지역 정책 ({len(local_policy)}건)", "#c0392b", "🏛️")}
    <div style='padding:15px;'>{_policy_html(local_policy)}</div>
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

    # 옵시디언 vault용 plain text(마크다운) 버전
    # 미완료 후속 조치·최근 영업 활동·최근 회의 섹션 제거 (사장님 지시 2026-07-07)
    plain = f"""# 🏃 영업 데일리 브리핑 [{today_str} {weekday}]

{ai_text}
"""

    recipients = [r.strip() for r in REPORT_RECIPIENTS.split(",") if r.strip()] or [NAVER_ADDRESS]
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏃 영업 데일리 브리핑 [{today_str} {weekday}]"
    msg["From"]    = NAVER_ADDRESS
    msg["To"]      = ", ".join(recipients)
    msg.attach(MIMEText(plain, "plain", "utf-8"))   # email-to-vault가 plain text 우선 저장
    msg.attach(MIMEText(html,  "html",  "utf-8"))   # 일반 이메일 클라이언트용 HTML

    try:
        with smtplib.SMTP_SSL("smtp.naver.com", 465) as s:
            s.login(NAVER_ADDRESS, NAVER_PASSWORD)
            s.send_message(msg)
        print(f"✅ 발송 완료 → {', '.join(recipients)}")
    except Exception as e:
        print(f"❌ 발송 실패: {e}")

    # 6. vault 직접 저장 (email-to-vault 의존성 제거)
    if GH_PAT:
        date_ymd = today_kst.strftime("%Y-%m-%d")
        now_iso  = datetime.datetime.now(KST).isoformat()
        frontmatter = f"""---
from: "{NAVER_ADDRESS}"
to: "beomseo.park@pfizer.com, {NAVER_ADDRESS}"
cc: ""
subject: "🏃 영업 데일리 브리핑 [{today_str} {weekday}]"
date: {now_iso}
---

"""
        filename = f"{date_ymd} 🏃 영업 데일리 브리핑 [{today_str} {weekday}].md"
        commit_to_vault(frontmatter + plain, filename, GH_PAT)
    else:
        print("⚠️  GH_PAT 없음 — vault 직접 커밋 건너뜀")


if __name__ == "__main__":
    main()
