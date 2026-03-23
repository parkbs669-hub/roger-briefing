"""
테니스 스트링 블로그/카페 알림 메인 스크립트
- 네이버 블로그/카페 API로 테니스 스트링 관련 최신 글 수집
- 이전에 본 링크와 비교해서 새 글만 필터링
- 새 글이 있으면 HTML 이메일 발송
"""

import json
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from naver_tennis_collector import collect_tennis_posts

# ── 환경변수 ─────────────────────────────────
NAVER_ADDRESS  = os.environ.get("NAVER_ADDRESS", "")
NAVER_PASSWORD = os.environ.get("NAVER_PASSWORD", "")
RECIPIENT      = os.environ.get("NAVER_ADDRESS", "")

# seen 링크 저장 파일
SEEN_FILE = Path("data/tennis_seen_links.json")


# ── 유틸 ─────────────────────────────────────
def load_seen_links() -> set[str]:
    if SEEN_FILE.exists():
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen_links(links: set[str]) -> None:
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(links), f, ensure_ascii=False, indent=2)


def filter_new_posts(posts: list[dict], seen: set[str]) -> list[dict]:
    return [p for p in posts if p["link"] not in seen]


def fmt_date(raw: str) -> str:
    """YYYYMMDD → YYYY.MM.DD"""
    if len(raw) == 8:
        return f"{raw[:4]}.{raw[4:6]}.{raw[6:]}"
    return raw


# ── HTML 이메일 생성 ──────────────────────────
def build_html_email(posts: list[dict]) -> str:
    today_str = datetime.now().strftime("%Y년 %m월 %d일")

    # 블로그 / 카페 분리
    blogs = [p for p in posts if p["source_type"] == "블로그"]
    cafes = [p for p in posts if p["source_type"] == "카페"]

    def render_section(items: list[dict], icon: str, label: str, color: str) -> str:
        if not items:
            return ""
        cards = ""
        for p in items:
            author_line = f'<span style="color:#6b7280;font-size:12px;">✍️ {p["author"]}</span>' if p["author"] else ""
            cafe_line   = f'<span style="color:#6b7280;font-size:12px;">☕ {p["cafe_name"]}</span>' if p["cafe_name"] else ""
            desc        = p["description"][:120] + "..." if len(p["description"]) > 120 else p["description"]
            date_str    = fmt_date(p["date"])

            cards += f"""
            <div style="padding:14px;background:#f8fafc;border-radius:8px;margin-bottom:10px;border-left:4px solid {color};">
                <a href="{p['link']}" style="font-size:15px;font-weight:700;color:#1e293b;text-decoration:none;">
                    {p['title']}
                </a>
                <div style="margin:6px 0 4px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
                    {author_line}{cafe_line}
                    <span style="color:#9ca3af;font-size:11px;">{date_str}</span>
                    <span style="background:{color}22;color:{color};font-size:11px;padding:1px 7px;border-radius:10px;">{p['keyword']}</span>
                </div>
                <div style="font-size:13px;color:#475569;line-height:1.5;">{desc}</div>
                <a href="{p['link']}" style="display:inline-block;margin-top:8px;font-size:12px;color:{color};text-decoration:none;">자세히 보기 →</a>
            </div>
            """

        return f"""
        <div style="background:#fff;border-radius:12px;padding:20px;margin-bottom:16px;">
            <h2 style="margin:0 0 14px;font-size:15px;color:#374151;border-bottom:2px solid #e5e7eb;padding-bottom:8px;">
                {icon} 네이버 {label} ({len(items)}건)
            </h2>
            {cards}
        </div>
        """

    blog_section = render_section(blogs, "📝", "블로그", "#059669")
    cafe_section = render_section(cafes, "☕", "카페",   "#f59e0b")

    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:'Apple SD Gothic Neo',Malgun Gothic,sans-serif;">
<div style="max-width:660px;margin:0 auto;padding:24px 16px;">

  <!-- 헤더 -->
  <div style="background:linear-gradient(135deg,#16a34a,#15803d);border-radius:12px;padding:24px;text-align:center;color:#fff;margin-bottom:20px;">
    <div style="font-size:36px;margin-bottom:8px;">🎾</div>
    <h1 style="margin:0;font-size:20px;font-weight:700;">테니스 스트링 최신 글 알림</h1>
    <p style="margin:6px 0 0;font-size:13px;opacity:0.85;">
      {today_str} · 블로그 {len(blogs)}건 + 카페 {len(cafes)}건
    </p>
  </div>

  {blog_section}
  {cafe_section}

  <!-- 키워드 안내 -->
  <div style="background:#fff;border-radius:12px;padding:16px;margin-bottom:16px;">
    <p style="margin:0;font-size:12px;color:#9ca3af;text-align:center;">
      🔍 검색 키워드: 테니스 스트링 추천 · 후기 · 거트 교체 · 폴리 스트링 · 장력 · 줄 추천
    </p>
  </div>

  <!-- 푸터 -->
  <div style="text-align:center;color:#9ca3af;font-size:11px;padding:12px;">
    네이버 오픈 API · GitHub Actions 자동 발송
  </div>

</div>
</body>
</html>
"""
    return html


# ── 이메일 발송 ───────────────────────────────
def send_email(html_body: str, blog_cnt: int, cafe_cnt: int) -> bool:
    if not NAVER_ADDRESS or not NAVER_PASSWORD:
        print("[메일] 환경변수 없음. 발송 건너뜀.")
        return False

    total = blog_cnt + cafe_cnt
    subject = f"🎾 테니스 스트링 새 글 {total}건 (블로그 {blog_cnt} + 카페 {cafe_cnt}) [{datetime.now().strftime('%m/%d')}]"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = NAVER_ADDRESS
    msg["To"]      = RECIPIENT
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.naver.com", 465) as server:
            server.login(NAVER_ADDRESS, NAVER_PASSWORD)
            server.sendmail(NAVER_ADDRESS, RECIPIENT, msg.as_string())
        print(f"[메일] 발송 완료 → {RECIPIENT}")
        return True
    except Exception as e:
        print(f"[메일] 발송 실패: {e}")
        return False


# ── 메인 ─────────────────────────────────────
def main():
    print("=" * 50)
    print(f"테니스 스트링 알림 시작: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    # 1. 수집
    posts = collect_tennis_posts(display_per_keyword=5)
    if not posts:
        print("[알림] 수집된 글 없음. 종료.")
        return

    # 2. 새 글만 필터링
    seen = load_seen_links()
    new_posts = filter_new_posts(posts, seen)
    print(f"[필터] 전체 {len(posts)}건 → 신규 {len(new_posts)}건")

    if not new_posts:
        print("[알림] 새 글 없음. 이메일 발송 안 함.")
        return

    # 3. 이메일 발송
    blogs = [p for p in new_posts if p["source_type"] == "블로그"]
    cafes = [p for p in new_posts if p["source_type"] == "카페"]
    html  = build_html_email(new_posts)
    sent  = send_email(html, len(blogs), len(cafes))

    # 4. seen 업데이트
    if sent:
        for p in new_posts:
            seen.add(p["link"])
        save_seen_links(seen)
        print(f"[저장] {SEEN_FILE} 업데이트 (총 {len(seen)}건)")

    print("=" * 50)
    print("완료!")


if __name__ == "__main__":
    main()
