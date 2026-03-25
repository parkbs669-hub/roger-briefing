import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

NAVER_ID = "parkbs669"
NAVER_PW = os.environ.get('NAVER_PASSWORD')

def post_to_naver_blog():
    options = Options()
    # 깃허브 서버에서는 반드시 headless가 필요합니다.
    options.add_argument("--headless") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # navigator.webdriver 탐지 우회
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    wait = WebDriverWait(driver, 30)

    try:
        title = f"🎾 테스트 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        content = "자동 포스팅 테스트입니다.\n정상 동작 확인 중입니다."

        # 1. 로그인
        print("🔐 로그인 시도")
        driver.get("https://nid.naver.com/nidlogin.login")
        time.sleep(2)

        # ❗ [핵심] 깃허브 서버용 복사-붙여넣기 우회법 (JS 이용)
        def clipboard_input(element_id, user_input):
            driver.execute_script("arguments[0].value = arguments[1]", driver.find_element(By.ID, element_id), user_input)
            time.sleep(1)

        clipboard_input("id", NAVER_ID)
        clipboard_input("pw", NAVER_PW)

        driver.find_element(By.ID, "log.login").click()
        time.sleep(5)

        if "nidlogin" in driver.current_url:
            print("❌ 로그인 실패 (보안 인증이나 캡차 발생)")
            return
        print("✅ 로그인 성공")

        # 2. 글쓰기 진입
        print("📝 에디터 진입 중...")
        driver.get(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}")
        
        # mainFrame 로딩 대기 및 전환
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
        print("🖼️ 프레임 전환 완료")

        # 3. 제목 입력
        title_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea.se-title-input")))
        title_box.click()
        # 한글 깨짐 방지를 위해 자바스크립트로 제목 주입
        driver.execute_script("arguments[0].value = arguments[1]", title_box, title)
        title_box.send_keys(Keys.SPACE) # 입력 신호를 주기 위한 살짝의 터치
        print("✍️ 제목 입력 완료")

        # 4. 본문 입력
        content_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".se-main-container")))
        content_box.click()
        # 본문은 ActionChains로 사람처럼 입력
        ActionChains(driver).send_keys(content).perform()
        print("✍️ 본문 입력 완료")

        time.sleep(2)

        # 5. 발행
        print("📤 발행 시도...")
        publish_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.se-publish-button")))
        publish_btn.click()
        time.sleep(2)

        confirm_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.se-confirm-button")))
        confirm_btn.click()
        
        print("🏁🏁🏁 [최종 성공] 사령관님, 포스팅이 완료되었습니다!")
        time.sleep(5)

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    post_to_naver_blog()
