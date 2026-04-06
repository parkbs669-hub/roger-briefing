import os
import json
import time
import requests
from datetime import datetime, timedelta
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ─────────────────────────────────────────
# 환경변수 및 설정
# ─────────────────────────────────────────
OPENAI_API_KEY      = os.environ["OPENAI_API_KEY"]
ALADIN_API_KEY      = os.environ["ALADIN_API_KEY"]
GOOGLE_BOOKS_API_KEY = os.environ.get("GOOGLE_BOOKS_API_KEY", "")
NL_API_KEY          = os.environ.get("NL_API_KEY", "")
NAVER_ID            = os.environ["NAVER_ADDRESS"]
NAVER_PW            = os.environ["NAVER_PASSWORD"]

SEEN_FILE = "data/tennis_books_seen.json"
MAX_DOMESTIC = 3
MAX_OVERSEAS = 3

client = OpenAI(api_key=OPENAI_API_KEY)

# ─────────────────────────────────────────
# 유틸리티 함수
# ─────────────────────────────────────────
def load_seen():
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
# 도서 수집 함수들
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
            if isbn in seen: continue
            books.append({
                "isbn": isbn, "title": item.get("title", ""),
                "author": item.get("author", ""), "publisher": item.get("publisher", ""),
                "pubdate": item.get("pubDate", ""), "cover": item.get("cover", ""),
                "description": item.get("description", ""), "link": item.get("link", ""),
                "source": "aladin", "lang": "ko",
            })
            if len(books) >= MAX_DOMESTIC: break
        return books
    except: return []

def fetch_nl_books(seen: set) -> list:
    if not NL_API_KEY: return []
    url = "https://www.nl.go.kr/NL/search/openApi/search.do"
    params = {
        "key": NL_API_KEY, "apiType": "json", "keyword": "테니스",
        "srchTarget": "total", "kwd": "테니스", "pageNum": 1,
        "pageSize": 10, "category": "도서", "sort": "NEWEST",
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        books = []
        for item in data.get("result", []):
            isbn = item.get("isbn", "")
            if not isbn or isbn in seen: continue
            books.append({
                "isbn": isbn, "title": item.get("titleInfo", ""),
                "author": item.get("authorInfo", ""), "publisher": item.get("pubInfo", ""),
                "pubdate": item.get("pubYearInfo", ""), "cover": "",
                "description": "", "link": "", "source": "nl", "lang": "ko",
            })
            if len(books) >= 2: break
        return books
    except: return []

def fetch_google_books(seen: set) -> list:
    if not GOOGLE_BOOKS_API_KEY: return []
    one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y")
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": "tennis", "key": GOOGLE_BOOKS_API_KEY, "maxResults": 15,
        "orderBy": "newest", "printType": "books", "langRestrict": "en",
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        books = []
        for item in data.get("items", []):
            info = item.get("volumeInfo", {})
            isbn = next((id_obj.get("identifier") for id_obj in info.get("industryIdentifiers", []) if id_obj.get("type") == "ISBN_13"), item.get("id", ""))
            if isbn in seen: continue
            pub_year = info.get("publishedDate", "")[:4]
            if pub_year and int(pub_year) < int(one_year_ago) - 1: continue
            img_links = info.get("imageLinks", {})
            cover = img_links.get("thumbnail", "").replace("http://", "https://")
            books.append({
                "isbn": isbn, "title": info.get("title", ""),
                "author": ", ".join(info.get("authors", [])), "publisher": info.get("publisher", ""),
                "pubdate": info.get("publishedDate", ""), "cover": cover,
                "description": info.get("description", "")[:300],
                "link": info.get("infoLink", ""), "source": "google", "lang": "en",
            })
            if len(books) >= MAX_OVERSEAS: break
        return books
    except: return []

# ─────────────────────────────────────────
# 콘텐츠 생성 및 포스팅
# ─────────────────────────────────────────
def generate_intro(book: dict) -> str:
    prompt = f"테니스 도서 소개글 작성: 제목:{book['title']}, 저자:{book['author']}, 내용:{book['description']}. 독자에게 흥미로운 200자 이내 한국어 소개글."
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        return resp.choices[0].message.content.strip()
    except: return book.get("description", "") or "테니스 관련 추천 도서입니다."

def build_post_html(domestic, overseas):
    today = datetime.now().strftime("%Y년 %m월 %d일")
    title = f"테니스 신간 도서 추천 ({today})"
    
    def book_to_html(book, color="#f9f9f9"):
        intro = generate_intro(book)
        cover_img = f'<img src="{book["cover"]}" style="max-width:120px;float:left;margin-right:15px;">' if book['cover'] else ""
        return f"""
        <div style="background:{color}; padding:20px; border-radius:10px; margin-bottom:20px; overflow:hidden;">
            {cover_img}
            <h3 style="margin-top:0;">{book['title']}</h3>
            <p style="font-size:14px; color:#666;">{book['author']} | {book['publisher']}</p>
            <p>{intro}</p>
            <div style="clear:both;"></div>
        </div>"""

    content = "<h2>📚 국내 테니스 신간</h2>" + "".join([book_to_html(b) for b in domestic])
    content += "<h2>🌍 해외 테니스 신간</h2>" + "".join([book_to_html(b, "#f0f4ff") for b in overseas])
    return title, content

def post_to_tistory(title, html):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://www.tistory.com/auth/kakao")
        time.sleep(2)
        # 카카오 로그인 버튼 클릭 (일반적으로 4번째 버튼)
        elems = driver.find_elements(By.CSS_SELECTOR, "a.btn_login")
        if len(elems) >= 4: elems[3].click()
        time.sleep(2)

        wait.until(EC.presence_of_element_located((By.ID, "loginId"))).send_keys(NAVER_ID)
        driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys(NAVER_PW)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(5)

        driver.get("https://beomsports.tistory.com/manage/newpost/")
        time.sleep(3)

        title_field = wait.until(EC.presence_of_element_located((By.ID, "post-title-inp")))
        title_field.send_keys(title)

        driver.switch_to.frame(driver.find_element(By.ID, "editor-tistory_ifr"))
        body = driver.find_element(By.ID, "tinymce")
        driver.execute_script("arguments[0].innerHTML = arguments[1];", body, html)
        driver.switch_to.default_content()
        time.sleep(2)

        driver.find_element(By.CSS_SELECTOR, "a.action").click() # 발행 버튼
        time.sleep(3)
        print(f"포스팅 완료: {title}")
    finally:
        driver.quit()

# ─────────────────────────────────────────
# 메인 실행부
# ─────────────────────────────────────────
def main():
    print(f"[시작] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    seen = load_seen()

    domestic = fetch_aladin_books(seen)
    nl_books = fetch_nl_books(seen)
    
    existing_titles = {b["title"] for b in domestic}
    for b in nl_books:
        if b["title"] not in existing_titles and len(domestic) < MAX_DOMESTIC:
            domestic.append(b)
    
    overseas = fetch_google_books(seen)
    print(f"[수집] 국내 {len(domestic)}권 / 해외 {len(overseas)}권")

    # 수집 결과 유무와 상관없이 파일을 저장 (Git 에러 방지)
    save_seen(seen)

    if not domestic and not overseas:
        print("[종료] 새로운 도서가 없어 작업을 중단합니다.")
        return

    title, html = build_post_html(domestic, overseas)
    try:
        post_to_tistory(title, html)
        # 성공 시에만 ISBN을 업데이트하여 중복 방지
        for b in domestic + overseas:
            seen.add(b["isbn"])
        save_seen(seen)
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()
