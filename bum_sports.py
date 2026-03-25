import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# ===== 설정 =====
NAVER_ID = "parkbs669"
NL_API_KEY = os.environ.get('NL_API_KEY')
NAVER_PW = os.environ.get('NAVER_PASSWORD')

def get_tennis_books():
    url = "https://www.nl.go.kr/NL/search/openApi/search.do"
    params = {
        'key': NL_API_KEY,
        'kwd': '테니스',
        'category': '도서',
        'apiType': 'json',
        'pageSize': 5
    }
    try:
        res = requests.get(url, params=params, timeout=20)
        items = res.json().get('result', [])
        if items:
            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 테니스 신간"
            body_list = ["오늘의 테니스 도서 목록입니다.", ""]
            for item in items:
                t = item.get('titleInfo', '').replace('<span class="searching_txt">', '').replace('</span>', '')
                body_list.append(f"● {t}")
            return title, body_list
    except Exception as e:
        print("도서 API 오류:", e)

    return f"🎾 [BUM Sports] 안내", ["테니스 소식을 준비 중입니다."]


def post_to_naver_blog(title, body_list):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)

    try:
        # ===== 1. 로그인 =====
        print("🔐 로그인 시도")
        driver.get("https://nid.naver.com/nidlogin.login")
        time.sleep(2)

        driver.find_element(By.ID, "id").send_keys(NAVER_ID)
        time.sleep(1)
        driver.find_element(By.ID, "pw").send_keys(NAVER_PW)
        time.sleep(1)
        driver.find_element(By.ID, "log.login").click()
        time.sleep(5)

        # 로그인 검증
        print("현재 URL:", driver.current_url)
        if "nidlogin" in driver.current_url:
            print("❌ 로그인 실패")
            return
        print("✅ 로그인 성공")

        # ===== 2. 글쓰기 이동 =====
        print("📝 글쓰기 페이지 이동")
        driver.get(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}")
        time.sleep(7)

        print("현재 URL:", driver.current_url)

        # ===== 3. iframe 진입 =====
        iframe = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe"))
        )
        driver.switch_to.frame(iframe)
        print("✅ 에디터 진입 성공")

        # ===== 4. 제목 =====
        title_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.se-title-input"))
        )
        title_box.click()
        title_box.send_keys(title)
        time.sleep(1)

        # ===== 5. 본문 =====
        content_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.se-component-content"))
        )
        content_box.click()
        time.sleep(1)

        for line in body_list:
            content_box.send_keys(line)
            content_box.send_keys(Keys.ENTER)
            time.sleep(0.2)

        print("✍️ 본문 입력 완료")

        # ===== 6. 발행 =====
        publish_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.se-publish-button"))
        )
        publish_btn.click()
        time.sleep(2)

        confirm_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.se-confirm-button"))
        )
        confirm_btn.click()

        time.sleep(5)
        print("✅✅ 포스팅 성공")

    except Exception as e:
        print("❌ 오류 발생:", e)

    finally:
        driver.quit()


if __name__ == "__main__":
    t, b = get_tennis_books()
    post_to_naver_blog(t, b)
