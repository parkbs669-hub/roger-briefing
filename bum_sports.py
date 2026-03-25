import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# ===== 설정 (사령관님 정보) =====
NAVER_ID = "parkbs669"
NL_API_KEY = os.environ.get('NL_API_KEY')
NAVER_PW = os.environ.get('NAVER_PASSWORD')

def get_tennis_books():
    url = "https://www.nl.go.kr/NL/search/openApi/search.do"
    params = {'key': NL_API_KEY, 'kwd': '테니스', 'category': '도서', 'apiType': 'json', 'pageSize': 5}
    try:
        res = requests.get(url, params=params, timeout=20)
        items = res.json().get('result', [])
        if items:
            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 테니스 소식"
            body_list = ["오늘의 테니스 도서 목록입니다.", ""]
            for item in items:
                t = item.get('titleInfo').replace('<span class="searching_txt">', '').replace('</span>', '')
                body_list.append(f"● {t}")
            return title, body_list
    except: pass
    return f"🎾 [BUM Sports] 안내", ["테니스 소식을 준비 중입니다."]

def post_to_naver_blog(title, body_list):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # 사령관님이 추가하신 화면 크기 설정 (성공률 향상의 핵심!)
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # 1. 로그인
        print("🔐 네이버 로그인 중...")
        driver.get("https://nid.naver.com/nidlogin.login")
        time.sleep(2)
        driver.find_element(By.ID, "id").send_keys(NAVER_ID)
        time.sleep(1)
        driver.find_element(By.ID, "pw").send_keys(NAVER_PW)
        time.sleep(1)
        driver.find_element(By.ID, "log.login").click()
        time.sleep(3)

        # 사령관님의 로그인 검증 로직
        if NAVER_ID not in driver.page_source:
            print("❌ 로그인 실패")
            return
        else:
            print("✅ 로그인 성공")

        # 2. 글쓰기 직접 이동
        print("📝 글쓰기 페이지 진입...")
        driver.get(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}")
        time.sleep(5)

        # 3. 에디터 프레임 전환
        WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
        print("✅ 에디터 프레임 전환 성공")

        # 4. 제목 입력 (안정적인 textarea 셀렉터)
        print("✍️ 제목 입력 중...")
        title_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.se-title-input"))
        )
        title_element.click()
        title_element.send_keys(title)
        time.sleep(1)

        # 5. 본문 입력 (챗GPT 제안: content_element 직접 주입)
        print("✍️ 본문 입력 중...")
        content_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.se-component-content, .se-content-placeholder"))
        )
        content_area = content_element # 변수명 안전하게 한 번 더 지정
        content_area.click()
        time.sleep(1)
        
        # 한 줄씩 직접 주입하여 포커스 튐 방지
        for line in body_list:
            content_area.send_keys(line)
            content_area.send_keys(Keys.ENTER)
            time.sleep(0.3)
        print("✍️ 본문 작성 완료")

        # 6. 발행 및 최종 확인
        print("📤 발행 및 최종 확인...")
        publish_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.publish_btn__Y5mLP, button.se-publish-button"))
        )
        publish_btn.click()
        time.sleep(2)

        confirm_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.confirm_btn__Dv9du, button.se-confirm-button"))
        )
        confirm_btn.click()
        time.sleep(5)

        print("✅✅ [최종 확인] 네이버 블로그 포스팅 성공!")

    except Exception as e:
        print(f"❌ 실패 원인: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    t, b_list = get_tennis_books()
    post_to_naver_blog(t, b_list)
