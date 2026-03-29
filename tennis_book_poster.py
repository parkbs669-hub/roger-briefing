import os
import json
import time
import base64
import requests
from datetime import datetime, timedelta
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ─────────────────────────────────────────
# 환경변수
# ─────────────────────────────────────────
OPENAI_API_KEY      = os.environ["OPENAI_API_KEY"]
ALADIN_API_KEY      = os.environ["ALADIN_API_KEY"]
GOOGLE_BOOKS_API_KEY = os.environ.get("GOOGLE_BOOKS_API_KEY", "")
NL_API_KEY          = os.environ.get("NL_API_KEY", "")       # 국립중앙도서관
NAVER_ID            = os.environ["NAVER_ADDRESS"]
NAVER_PW            = os.environ["NAVER_PASSWORD"]

SEEN_FILE = "data/tennis_books_seen.json"
MAX_DOMESTIC = 3   # 국내 도서 최대 수집 권수
MAX_OVERSEAS = 3   # 해외 도서 최대 수집 권수

client = OpenAI(api_key=OPENAI_API_KEY)


# ─────────────────────────────────────────
# 중복 체크
# ─────────────────────────────────────────
def load_seen():
    os.makedirs("data", exist_ok=True)
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_seen(seen: set):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────
# 1. 알라딘 API — 국내 신간
# ─────────────────────────────────────────
def fetch_aladin_books(seen: set) -> list:
    url = "https://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
    params = {
        "TTBKey": ALADIN_API_KEY,
        "Query": "테니스",
        "QueryType": "Keyword",
        "MaxResults": 10,
        "SearchTarget": "Book",
        "Output": "js",
        "Version": "20131101",
        "Sort": "PublishTime",
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        books = []
        for item in data.get("item", []):
            isbn = item.get("isbn13") or item.get("isbn", "")
            if isbn in seen:
                continue
            books.append({
                "isbn": isbn,
                "title": item.get("title", ""),
                "author": item.get("author", ""),
                "publisher": item.get("publisher", ""),
                "pubdate": item.get("pubDate", ""),
                "cover": item.get("cover", ""),
                "description": item.get("description", ""),
                "link": item.get("link", ""),
                "source": "aladin",
                "lang": "ko",
            })
            if len(books) >= MAX_DOMESTIC:
                break
        return books
    except Exception as e:
        print(f"[알라딘 오류] {e}")
        return []


# ─────────────────────────────────────────
# 2. 국립중앙도서관 API — 국내 신간 보완
# ─────────────────────────────────────────
def fetch_nl_books(seen: set) -> list:
    if not NL_API_KEY:
        return []
    url = "https://www.nl.go.kr/NL/search/openApi/search.do"
    params = {
        "key": NL_API_KEY,
        "apiType": "json",
        "keyword": "테니스",
        "srchTarget": "total",
        "kwd": "테니스",
        "pageNum": 1,
        "pageSize": 10,
        "category": "도서",
        "sort": "NEWEST",
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        books = []
        for item in data.get("result", []):
            isbn = item.get("isbn", "")
            if not isbn or isbn in seen:
                continue
            books.append({
                "isbn": isbn,
                "title": item.get("titleInfo", ""),
                "author": item.get("authorInfo", ""),
                "publisher": item.get("pubInfo", ""),
                "pubdate": item.get("pubYearInfo", ""),
                "cover": "",
                "description": "",
                "link": "",
                "source": "nl",
                "lang": "ko",
            })
            if len(books) >= 2:
                break
        return books
    except Exception as e:
        print(f"[국립중앙도서관 오류] {e}")
        return []


# ─────────────────────────────────────────
# 3. Google Books API — 해외 신간
# ─────────────────────────────────────────
def fetch_google_books(seen: set) -> list:
    if not GOOGLE_BOOKS_API_KEY:
        return []
    # 최근 1년 이내 출판 필터
    one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y")
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": "tennis",
        "key": GOOGLE_BOOKS_API_KEY,
        "maxResults": 15,
        "orderBy": "newest",
        "printType": "books",
        "langRestrict": "en",
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        books = []
        for item in data.get("items", []):
            info = item.get("volumeInfo", {})
            isbn = ""
            for id_obj in info.get("industryIdentifiers", []):
                if id_obj.get("type") == "ISBN_13":
                    isbn = id_obj.get("identifier", "")
                    break
            if not isbn:
                isbn = item.get("id", "")
            if isbn in seen:
                continue
            # 출판연도 필터 (최근 2년)
            pub_year = info.get("publishedDate", "")[:4]
            if pub_year and int(pub_year) < int(one_year_ago) - 1:
                continue
            cover = ""
            img_links = info.get("imageLinks", {})
            cover = img_links.get("thumbnail", img_links.get("smallThumbnail", ""))
            # https 강제
            if cover.startswith("http://"):
                cover = cover.replace("http://", "https://")
            books.append({
                "isbn": isbn,
                "title": info.get("title", ""),
                "author": ", ".join(info.get("authors", [])),
                "publisher": info.get("publisher", ""),
                "pubdate": info.get("publishedDate", ""),
                "cover": cover,
                "description": info.get("description", "")[:300],
                "link": info.get("infoLink", ""),
                "source": "google",
                "lang": "en",
            })
            if len(books) >= MAX_OVERSEAS:
                break
        return books
    except Exception as e:
        print(f"[Google Books 오류] {e}")
        return []


# ─────────────────────────────────────────
# 4. GPT 소개글 생성
# ─────────────────────────────────────────
def generate_intro(book: dict) -> str:
    lang_hint = "한국어 책" if book["lang"] == "ko" else "영어 원서"
    prompt = f"""
다음 테니스 관련 도서를 테니스 애호가 독자에게 소개하는 글을 한국어로 작성해주세요.
- 분량: 150~200자
- 톤: 친근하고 흥미 유발
- 책 제목과 저자를 자연스럽게 포함
- 책의 핵심 내용이나 매력 포인트를 중심으로

제목: {book['title']}
저자: {book['author']}
출판사: {book['publisher']}
출판일: {book['pubdate']}
설명: {book['description']}
언어: {lang_hint}
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[GPT 오류] {e}")
        return book.get("description", "") or "테니스 관련 추천 도서입니다."


# ─────────────────────────────────────────
# 5. HTML 포스트 생성
# ─────────────────────────────────────────
def build_post_html(domestic: list, overseas: list) -> tuple[str, str]:
    today = datetime.now().strftime("%Y년 %m월 %d일")
    title = f"테니스 신간 도서 추천 ({today})"

    sections = []

    if domestic:
        sections.append("<h2>📚 국내 신간</h2>")
        for book in domestic:
            intro = generate_intro(book)
            cover_html = f'<img src="{book["cover"]}" alt="{book["title"]}" style="max-width:120px;float:left;margin:0 16px 16px 0;border-radius:6px;">' if book.get("cover") else ""
            buy_btn = f'<a href="{book["link"]}" target="_blank" style="display:inline-block;margin-top:10px;padding:8px 18px;background:#e8534a;color:#fff;border-radius:20px;text-decoration:none;font-size:14px;">📖 알라딘에서 보기</a>' if book.get("link") else ""
            sections.append(f"""
<div style="overflow:hidden;margin-bottom:32px;padding:20px;background:#f9f9f9;border-radius:12px;">
  {cover_html}
  <h3 style="margin:0 0 6px;">{book['title']}</h3>
  <p style="color:#666;font-size:14px;margin:0 0 10px;">✍️ {book['author']} | 📅 {book['pubdate']} | 🏢 {book['publisher']}</p>
  <p style="line-height:1.7;">{intro}</p>
  {buy_btn}
  <div style="clear:both;"></div>
</div>""")

    if overseas:
        sections.append("<h2>🌍 해외 신간</h2>")
        for book in overseas:
            intro = generate_intro(book)
            cover_html = f'<img src="{book["cover"]}" alt="{book["title"]}" style="max-width:120px;float:left;margin:0 16px 16px 0;border-radius:6px;">' if book.get("cover") else ""
            buy_btn = f'<a href="{book["link"]}" target="_blank" style="display:inline-block;margin-top:10px;padding:8px 18px;background:#3a7bd5;color:#fff;border-radius:20px;text-decoration:none;font-size:14px;">🔗 상세 정보 보기</a>' if book.get("link") else ""
            sections.append(f"""
<div style="overflow:hidden;margin-bottom:32px;padding:20px;background:#f0f4ff;border-radius:12px;">
  {cover_html}
  <h3 style="margin:0 0 6px;">{book['title']}</h3>
  <p style="color:#666;font-size:14px;margin:0 0 10px;">✍️ {book['author']} | 📅 {book['pubdate']} | 🏢 {book['publisher']}</p>
  <p style="line-height:1.7;">{intro}</p>
  {buy_btn}
  <div style="clear:both;"></div>
</div>""")

    footer = """
<hr style="margin:40px 0 20px;">
<p style="font-size:13px;color:#999;text-align:center;">
  📌 이 포스팅은 테니스 관련 신간 도서를 자동으로 수집하여 소개합니다.<br>
  구매 링크는 알라딘 제휴 링크를 포함할 수 있습니다.
</p>"""

    html = f"""
<div style="max-width:720px;margin:0 auto;font-family:'Noto Sans KR',sans-serif;line-height:1.8;">
  <p style="color:#555;margin-bottom:30px;">
    이번 주 테니스 관련 신간 도서를 국내·해외로 나눠 소개합니다. 
    코트 밖에서도 테니스 실력을 키워보세요! 🎾
  </p>
  {''.join(sections)}
  {footer}
</div>"""

    return title, html


# ─────────────────────────────────────────
# 6. Tistory Selenium 업로드
# ─────────────────────────────────────────
def post_to_tistory(title: str, html: str):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        # 카카오 로그인
        driver.get("https://www.tistory.com/auth/kakao")
        time.sleep(2)

        elems = driver.find_elements(By.CSS_SELECTOR, "a.btn_login")
        if len(elems) > 3:
            elems[3].click()
        time.sleep(2)

        wait.until(EC.presence_of_element_located((By.ID, "loginId"))).send_keys(NAVER_ID)
        driver.find_element(By.ID, "loginId").send_keys("")
        driver.find_element(By.CSS_SELECTOR, "input#loginId").clear()
        driver.find_element(By.CSS_SELECTOR, "input#loginId").send_keys(NAVER_ID)
        driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys(NAVER_PW)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)

        # 글쓰기 이동
        driver.get("https://beomsports.tistory.com/manage/newpost/")
        time.sleep(3)

        # 제목 입력
        title_field = wait.until(EC.presence_of_element_located((By.ID, "post-title-inp")))
        title_field.clear()
        title_field.send_keys(title)
        time.sleep(1)

        # HTML 모드 전환
        try:
            html_btn = driver.find_element(By.CSS_SELECTOR, "button.btn_setting, button[data-type='html']")
            html_btn.click()
            time.sleep(1)
        except:
            pass

        # TinyMCE iframe 본문 입력
        driver.switch_to.frame(driver.find_element(By.ID, "editor-tistory_ifr"))
        body = driver.find_element(By.ID, "tinymce")
        body.clear()
        driver.execute_script("arguments[0].innerHTML = arguments[1];", body, html)
        driver.execute_script("""
            var body = document.getElementById('tinymce');
            var range = document.createRange();
            range.selectNodeContents(body);
            range.collapse(false);
            var sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
        """)
        driver.switch_to.default_content()
        time.sleep(5)

        # 임시저장 후 발행
        driver.find_element(By.CSS_SELECTOR, "a.action").click()
        time.sleep(2)

        print(f"[완료] 포스팅 업로드 성공: {title}")

    except Exception as e:
        print(f"[Selenium 오류] {e}")
        raise
    finally:
        driver.quit()


# ─────────────────────────────────────────
# 메인
# ─────────────────────────────────────────
def main():
    print(f"[시작] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    seen = load_seen()

    # 도서 수집
    domestic = fetch_aladin_books(seen)
    nl_books = fetch_nl_books(seen)

    # 알라딘에서 못 채운 경우 국립중앙도서관으로 보완
    existing_titles = {b["title"] for b in domestic}
    for b in nl_books:
        if b["title"] not in existing_titles and len(domestic) < MAX_DOMESTIC:
            domestic.append(b)

    overseas = fetch_google_books(seen)

    print(f"[수집] 국내 {len(domestic)}권 / 해외 {len(overseas)}권")

    if not domestic and not overseas:
        print("[종료] 새로운 도서 없음")
        return

    # 포스트 생성
    title, html = build_post_html(domestic, overseas)

    # Tistory 업로드
    post_to_tistory(title, html)

    # seen 업데이트
    for b in domestic + overseas:
        seen.add(b["isbn"])
    save_seen(seen)

    print("[완료] 모든 작업 완료")


if __name__ == "__main__":
    main()
