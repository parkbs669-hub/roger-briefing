# -*- coding: utf-8 -*-
"""
테니스 신간 도서 + 해외 매거진 → 티스토리 자동 포스팅 (GitHub Actions용)
- 국내 도서: 알라딘 API
- 해외 도서: Google Books API + Open Library API
- 해외 매거진: RSS
- 소개글: GPT-4o-mini
- 로그인: 카카오 계정 (성공한 로컬 코드 방식 그대로)
"""

import re
import time
import json
import os
import requests
import feedparser
from datetime import datetime
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ─────────────────────────────────────────
# 1. 환경변수 (GitHub Secrets)
# ─────────────────────────────────────────
OPENAI_API_KEY       = os.environ.get("OPENAI_API_KEY", "")
ALADIN_API_KEY       = os.environ.get("ALADIN_API_KEY", "")
GOOGLE_BOOKS_API_KEY = os.environ.get("GOOGLE_BOOKS_API_KEY", "")
KAKAO_ID             = os.environ.get("KAKAO_ID", "")       # ← Secret 추가 필요
KAKAO_PW             = os.environ.get("KAKAO_PW", "")       # ← Secret 추가 필요
TISTORY_BLOG         = "beomsports"

SEEN_FILE    = "data/tennis_books_seen.json"
MAX_DOMESTIC = 3
MAX_OVERSEAS = 3
MAX_MAGAZINE = 4

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ─────────────────────────────────────────
# 매거진 RSS
# ─────────────────────────────────────────
MAGAZINE_RSS = [
    {
        "name": "테니스코리아",
        "country": "🇰🇷 한국",
        "desc": "월간 인쇄 발행 | 1989년 창간, 국내 유일 테니스 전문 월간지",
        "url": "https://v.daum.net/rss/channel/321",
        "icon": "🎾",
        "lang": "ko",
    },
]

# ─────────────────────────────────────────
# 2. 유틸리티
# ─────────────────────────────────────────
def load_seen() -> set:
    os.makedirs("data", exist_ok=True)
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_seen(seen: set):
    os.makedirs("data", exist_ok=True)
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────
# 3. 도서 수집
# ─────────────────────────────────────────
def fetch_aladin_books(seen: set) -> list:
    print("알라딘 국내 신간 수집 중...")
    if not ALADIN_API_KEY:
        print("[알라딘] API 키 없음 → 건너뜀")
        return []
    url = "https://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
    params = {
        "TTBKey": ALADIN_API_KEY, "Query": "테니스", "QueryType": "Keyword",
        "MaxResults": 10, "SearchTarget": "Book", "Output": "js",
        "Version": "20131101", "Sort": "PublishTime",
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        data = res.json()
        books = []
        for item in data.get("item", []):
            isbn = item.get("isbn13") or item.get("isbn", "")
            if isbn in seen:
                continue
            books.append({
                "isbn": isbn, "title": item.get("title", ""),
                "author": item.get("author", ""), "publisher": item.get("publisher", ""),
                "pubdate": item.get("pubDate", ""),
                "cover": item.get("cover", "").replace("coversum", "cover200"),
                "description": item.get("description", ""),
                "link": item.get("link", ""), "lang": "ko", "type": "book",
            })
            if len(books) >= MAX_DOMESTIC:
                break
        print(f"알라딘 수집 완료: {len(books)}권")
        return books
    except Exception as e:
        print(f"알라딘 오류: {e}")
        return []

def fetch_google_books(seen: set) -> list:
    print("Google Books 해외 신간 수집 중...")
    if not GOOGLE_BOOKS_API_KEY:
        print("[구글] API 키 없음 → 건너뜀")
        return []
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": "tennis+subject:sports", "key": GOOGLE_BOOKS_API_KEY,
        "maxResults": 20, "orderBy": "newest", "printType": "books",
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        data = res.json()
        books = []
        for item in data.get("items", []):
            info = item.get("volumeInfo", {})
            isbn = next(
                (x.get("identifier") for x in info.get("industryIdentifiers", [])
                 if x.get("type") == "ISBN_13"),
                "gb_" + item.get("id", "")
            )
            if isbn in seen:
                continue
            img = info.get("imageLinks", {})
            cover = img.get("thumbnail", img.get("smallThumbnail", "")).replace("http://", "https://")
            books.append({
                "isbn": isbn, "title": info.get("title", ""),
                "author": ", ".join(info.get("authors", [])),
                "publisher": info.get("publisher", ""),
                "pubdate": info.get("publishedDate", ""), "cover": cover,
                "description": info.get("description", "")[:300],
                "link": info.get("infoLink", ""), "lang": "en", "type": "book",
            })
            if len(books) >= MAX_OVERSEAS:
                break
        print(f"Google Books 수집 완료: {len(books)}권")
        return books
    except Exception as e:
        print(f"Google Books 오류: {e}")
        return []

def fetch_open_library_books(seen: set, existing_count: int) -> list:
    print("Open Library 해외 신간 수집 중...")
    needed = MAX_OVERSEAS - existing_count
    if needed <= 0:
        return []
    url = "https://openlibrary.org/search.json"
    params = {"q": "tennis", "sort": "new", "language": "eng", "limit": 15}
    try:
        res = requests.get(url, params=params, timeout=15, headers=HEADERS)
        data = res.json()
        books = []
        for doc in data.get("docs", []):
            isbn_list = doc.get("isbn", [])
            isbn = isbn_list[0] if isbn_list else "ol_" + str(doc.get("key", "")).replace("/works/", "")
            if isbn in seen:
                continue
            cover_id = doc.get("cover_i", "")
            cover = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else ""
            books.append({
                "isbn": isbn, "title": doc.get("title", ""),
                "author": ", ".join(doc.get("author_name", [])[:2]),
                "publisher": ", ".join(doc.get("publisher", [])[:1]),
                "pubdate": str(doc.get("first_publish_year", "")), "cover": cover,
                "description": "",
                "link": f"https://openlibrary.org{doc.get('key', '')}",
                "lang": "en", "type": "book",
            })
            if len(books) >= needed:
                break
        print(f"Open Library 수집 완료: {len(books)}권")
        return books
    except Exception as e:
        print(f"Open Library 오류: {e}")
        return []

def fetch_magazine_articles(seen: set) -> list:
    print("테니스 매거진 RSS 수집 중...")
    articles = []
    keywords = ["tennis", "string", "racket", "racquet", "serve", "player",
                "tournament", "atp", "wta", "grand slam", "wimbledon", "open", "테니스"]
    for feed in MAGAZINE_RSS:
        if len(articles) >= MAX_MAGAZINE:
            break
        try:
            parsed = feedparser.parse(feed["url"])
            feed_articles = 0
            for entry in parsed.entries:
                if len(articles) >= MAX_MAGAZINE:
                    break
                title = entry.get("title", "").strip()
                link  = entry.get("link", "").strip()
                desc  = entry.get("summary", entry.get("description", "")).strip()
                pub   = (entry.get("published") or entry.get("updated") or "")[:16]
                combined = (title + " " + desc).lower()
                if not any(kw in combined for kw in keywords):
                    continue
                uid = "rss_" + link[:80]
                if uid in seen:
                    continue
                cover = ""
                if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                    cover = entry.media_thumbnail[0].get("url", "")
                elif hasattr(entry, "media_content") and entry.media_content:
                    cover = entry.media_content[0].get("url", "")
                elif entry.get("enclosures"):
                    for enc in entry.enclosures:
                        if "image" in enc.get("type", ""):
                            cover = enc.get("href", "")
                            break
                if not cover:
                    content_val = (entry.content[0].get("value", "") if entry.get("content") else entry.get("summary", ""))
                    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content_val)
                    if img_match:
                        cover = img_match.group(1)
                desc_clean = re.sub(r"<[^>]+>", "", desc)[:200].strip()
                articles.append({
                    "isbn": uid, "title": title, "author": feed["name"],
                    "publisher": feed["name"], "pubdate": pub, "cover": cover,
                    "description": desc_clean, "link": link,
                    "lang": feed.get("lang", "en"), "type": "magazine",
                    "icon": feed["icon"], "country": feed.get("country", ""),
                    "desc": feed.get("desc", ""),
                })
                feed_articles += 1
            print(f"  {feed['name']}: {feed_articles}건")
        except Exception as e:
            print(f"  {feed['name']} RSS 오류: {e}")
    print(f"매거진 수집 완료: {len(articles)}건")
    return articles

# ─────────────────────────────────────────
# 4. GPT 콘텐츠 생성
# ─────────────────────────────────────────
def generate_intro(item: dict) -> str:
    if not OPENAI_API_KEY:
        return item.get("description", "")[:200] or "테니스 관련 추천 콘텐츠입니다."
    if item["type"] == "magazine":
        prompt = (
            f"해외 테니스 매거진 기사를 한국 테니스 독자에게 소개하는 글을 한국어로 작성해주세요.\n"
            f"분량: 100~150자, 톤: 간결하고 흥미 유발\n"
            f"매거진: {item['author']}\n제목: {item['title']}\n내용: {item['description']}"
        )
    else:
        lang_hint = "한국어 도서" if item["lang"] == "ko" else "영어 원서"
        prompt = (
            f"테니스 관련 도서를 테니스 애호가에게 소개하는 글을 한국어로 작성해주세요.\n"
            f"분량: 150~200자, 톤: 친근하고 흥미 유발, 책 제목과 저자 자연스럽게 포함\n"
            f"제목: {item['title']}\n저자: {item['author']}\n출판사: {item['publisher']}\n"
            f"출판일: {item['pubdate']}\n설명: {item['description']}\n언어: {lang_hint}"
        )
    try:
        resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"GPT 소개글 오류: {e}")
        return item.get("description", "") or "테니스 관련 추천 콘텐츠입니다."

def generate_title(domestic: list, overseas: list, magazines: list) -> str:
    today = datetime.now().strftime("%Y년 %m월 %d일")
    d_titles  = ", ".join([b["title"] for b in domestic[:2]])
    mag_titles = ", ".join([m["title"] for m in magazines[:2]])
    if not OPENAI_API_KEY:
        return f"테니스 신간 & 매거진 소식 ({datetime.now().strftime('%Y.%m.%d')})"
    prompt = (
        f"테니스 신간 도서 + 매거진 블로그 포스팅 제목을 1개만 만들어줘.\n"
        f"흥미롭고 검색이 잘 되게. 날짜({today}) 포함. 제목만 출력.\n"
        f"국내 도서: {d_titles}\n매거진 기사: {mag_titles}"
    )
    try:
        resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
        )
        title = resp.choices[0].message.content.strip()
        print(f"제목 생성: {title}")
        return title
    except Exception as e:
        print(f"제목 생성 오류: {e}")
        return f"테니스 신간 & 매거진 소식 ({datetime.now().strftime('%Y.%m.%d')})"

# ─────────────────────────────────────────
# 5. HTML 빌드
# ─────────────────────────────────────────
def book_card_html(book: dict, btn_color: str, btn_label: str) -> str:
    intro = generate_intro(book)
    cover_html = (
        f'<img src="{book["cover"]}" alt="{book["title"]}" '
        f'style="max-width:110px;float:left;margin:0 18px 12px 0;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.15);">'
    ) if book.get("cover") else ""
    btn_html = (
        f'<a href="{book["link"]}" target="_blank" rel="noopener" '
        f'style="display:inline-block;margin-top:10px;padding:7px 18px;background:{btn_color};'
        f'color:#fff;border-radius:20px;text-decoration:none;font-size:13px;font-weight:bold;">'
        f'{btn_label}</a>'
    ) if book.get("link") else ""
    bg = "#f9f9f9" if book.get("lang") == "ko" else "#f0f4ff"
    return f"""
<div style="overflow:hidden;margin-bottom:24px;padding:18px;background:{bg};border-radius:12px;border-left:4px solid {btn_color};">
  {cover_html}
  <h4 style="margin:0 0 5px;color:#222;">{book['title']}</h4>
  <p style="color:#777;font-size:12px;margin:0 0 8px;">
    ✍️ {book['author']} &nbsp;|&nbsp; 📅 {book['pubdate']} &nbsp;|&nbsp; 🏢 {book['publisher']}
  </p>
  <p style="line-height:1.8;margin:0;font-size:14px;">{intro}</p>
  {btn_html}
  <div style="clear:both;"></div>
</div>"""

def magazine_card_html(article: dict) -> str:
    intro = generate_intro(article)
    is_ko = article.get("lang", "en") == "ko"
    border = "#e8534a" if is_ko else "#2d8a4e"
    bg     = "#fff8f0" if is_ko else "#f0fff4"
    cover_html = (
        f'<img src="{article["cover"]}" '
        f'style="max-width:110px;float:left;margin:0 18px 12px 0;border-radius:8px;object-fit:cover;">'
    ) if article.get("cover") else ""
    btn_html = (
        f'<a href="{article["link"]}" target="_blank" rel="noopener" '
        f'style="display:inline-block;margin-top:10px;padding:7px 18px;background:{border};'
        f'color:#fff;border-radius:20px;text-decoration:none;font-size:13px;font-weight:bold;">'
        f'🔗 원문 보기</a>'
    ) if article.get("link") else ""
    return f"""
<div style="overflow:hidden;margin-bottom:24px;padding:18px;background:{bg};border-radius:12px;border-left:4px solid {border};">
  {cover_html}
  <p style="color:{border};font-size:12px;font-weight:bold;margin:0 0 2px;">
    {article.get('icon','📰')} {article['author']} &nbsp;|&nbsp; {article.get('country','')}
  </p>
  <p style="color:#999;font-size:11px;margin:0 0 6px;">{article.get('desc','')}</p>
  <h4 style="margin:0 0 5px;color:#222;">{article['title']}</h4>
  <p style="color:#777;font-size:12px;margin:0 0 8px;">📅 {article['pubdate']}</p>
  <p style="line-height:1.8;margin:0;font-size:14px;">{intro}</p>
  {btn_html}
  <div style="clear:both;"></div>
</div>"""

def build_post_html(domestic: list, overseas: list, magazines: list) -> str:
    today = datetime.now().strftime("%Y년 %m월 %d일")
    sections = [f'<p style="color:#555;line-height:1.8;margin-bottom:28px;">{today} 기준 테니스 신간 도서와 매거진 최신 소식을 한 곳에 모았습니다. 🎾</p>']
    if domestic:
        sections.append("<h3>📚 국내 신간 도서</h3>")
        for b in domestic:
            print(f"  소개글 생성: {b['title']}")
            sections.append(book_card_html(b, "#e8534a", "📖 알라딘에서 보기"))
    if overseas:
        sections.append("<h3>🌍 해외 신간 도서</h3>")
        for b in overseas:
            print(f"  소개글 생성: {b['title']}")
            sections.append(book_card_html(b, "#3a7bd5", "🔗 상세 정보 보기"))
    if magazines:
        ko_mags = [a for a in magazines if a.get("lang") == "ko"]
        en_mags = [a for a in magazines if a.get("lang") != "ko"]
        if ko_mags:
            sections.append("<h3>📰 국내 테니스 매거진 최신 소식</h3>")
            for a in ko_mags:
                print(f"  소개글 생성: {a['title'][:40]}...")
                sections.append(magazine_card_html(a))
        if en_mags:
            sections.append("<h3>🌐 해외 테니스 매거진 최신 소식</h3>")
            for a in en_mags:
                print(f"  소개글 생성: {a['title'][:40]}...")
                sections.append(magazine_card_html(a))
    sections.append('<hr style="margin:36px 0 20px;border:none;border-top:1px solid #eee;"><p style="font-size:12px;color:#bbb;text-align:center;">📌 본 포스팅은 테니스 관련 신간 도서 및 매거진 기사를 자동 수집하여 소개합니다.</p>')
    return "\n".join(sections)

# ─────────────────────────────────────────
# 6. 티스토리 포스팅 (성공한 로컬 코드 방식)
# ─────────────────────────────────────────
def post_to_tistory(title: str, content: str):
    print("브라우저 시작 중...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 25)

    try:
        # ── Step 1: 티스토리 로그인 페이지
        driver.get("https://www.tistory.com/auth/login")
        time.sleep(4)
        print(f"[로그인] 현재 URL: {driver.current_url}")

        # ── Step 2: 카카오 로그인 버튼 (성공한 코드: XPATH + execute_script)
        elems = driver.find_elements(
            By.XPATH,
            "//*[contains(text(),'카카오') or contains(@class,'kakao') or contains(@href,'kakao')]"
        )
        print(f"[로그인] 카카오 관련 요소 수: {len(elems)}")
        # index 3번이 성공했던 버튼 (로컬 성공 코드 그대로)
        driver.execute_script("arguments[0].click();", elems[3])
        time.sleep(4)
        print(f"[로그인] 카카오 클릭 후 URL: {driver.current_url}")

        # ── Step 3: 카카오 로그인 폼 입력
        id_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type=text], input[type=email]")
        ))
        id_input.clear()
        id_input.send_keys(KAKAO_ID)
        time.sleep(1)

        pw_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type=password]")
        ))
        pw_input.clear()
        pw_input.send_keys(KAKAO_PW)
        time.sleep(1)

        login_btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[type=submit]")
        ))
        driver.execute_script("arguments[0].click();", login_btn)
        time.sleep(5)
        print(f"[로그인] 완료. URL: {driver.current_url}")

        # ── Step 4: 글쓰기 페이지
        driver.get(f"https://{TISTORY_BLOG}.tistory.com/manage/newpost/")
        time.sleep(6)
        print(f"[글쓰기] 에디터 URL: {driver.current_url}")

        # ── Step 5: 제목 입력
        title_input = wait.until(EC.element_to_be_clickable((By.ID, "post-title-inp")))
        driver.execute_script("arguments[0].focus();", title_input)
        title_input.send_keys(title)
        time.sleep(1)
        print(f"[글쓰기] 제목 입력: {title}")

        # ── Step 6: 본문 입력 (iframe → tinymce)
        iframe = wait.until(EC.presence_of_element_located((By.ID, "editor-tistory_ifr")))
        driver.switch_to.frame(iframe)
        body_area = wait.until(EC.presence_of_element_located((By.ID, "tinymce")))
        driver.execute_script("arguments[0].innerHTML = arguments[1];", body_area, content)
        driver.execute_script("""
            var body = document.getElementById('tinymce');
            var range = document.createRange();
            range.selectNodeContents(body);
            range.collapse(false);
            var sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
        """)
        time.sleep(1)
        driver.switch_to.default_content()
        time.sleep(5)
        print("[글쓰기] 본문 입력 완료")

        # ── Step 7: 임시저장 (a.action)
        save_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.action")))
        driver.execute_script("arguments[0].click();", save_btn)
        time.sleep(4)
        print("[글쓰기] 임시저장 완료")

        # ── Step 8: 발행 레이어 열기
        complete_btns = driver.find_elements(By.ID, "publish-layer-btn")
        driver.execute_script("arguments[0].click();", complete_btns[0])
        time.sleep(3)
        print("[발행] 발행 레이어 열기 완료")

        # ── Step 9: 발행 버튼 클릭 (비공개)
        private_btn = wait.until(EC.element_to_be_clickable((By.ID, "publish-btn")))
        driver.execute_script("arguments[0].click();", private_btn)
        time.sleep(2)
        print(f"[성공] 포스팅 완료: {title}")

    except Exception as e:
        print(f"[오류] {e}")
        # GitHub Actions 환경에서는 스크린샷을 /tmp에 저장
        try:
            driver.save_screenshot("/tmp/error_tennis_books.png")
            print("[디버그] 스크린샷 저장: /tmp/error_tennis_books.png")
        except:
            pass
        raise

    finally:
        driver.quit()

# ─────────────────────────────────────────
# 7. 메인
# ─────────────────────────────────────────
def main():
    print("=" * 55)
    print("테니스 신간 도서 + 매거진 자동 포스팅 시작")
    print("=" * 55)
    print(f"[시작] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    for name, val in [
        ("OPENAI_API_KEY", OPENAI_API_KEY), ("ALADIN_API_KEY", ALADIN_API_KEY),
        ("GOOGLE_BOOKS_API_KEY", GOOGLE_BOOKS_API_KEY),
        ("KAKAO_ID", KAKAO_ID), ("KAKAO_PW", KAKAO_PW),
    ]:
        print(f"  {name}: {'✅' if val else '❌ 없음'}")

    seen = load_seen()

    domestic  = fetch_aladin_books(seen)
    overseas  = fetch_google_books(seen)
    if len(overseas) < MAX_OVERSEAS:
        overseas.extend(fetch_open_library_books(seen, len(overseas)))
    magazines = fetch_magazine_articles(seen)

    print(f"\n수집 결과: 국내 {len(domestic)}권 / 해외 {len(overseas)}권 / 매거진 {len(magazines)}건\n")

    if not domestic and not overseas and not magazines:
        print("새로운 콘텐츠 없음. 종료합니다.")
        return

    title   = generate_title(domestic, overseas, magazines)
    content = build_post_html(domestic, overseas, magazines)

    post_to_tistory(title, content)

    for item in domestic + overseas + magazines:
        seen.add(item["isbn"])
    save_seen(seen)

    print("=" * 55)
    print("전체 프로세스 완료")
    print("=" * 55)

if __name__ == "__main__":
    main()
