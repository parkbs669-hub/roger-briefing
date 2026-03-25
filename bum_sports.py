import os
import time
import pyperclip
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
    
    # ❗ headless 제거 (중요)
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # ❗ webdriver 숨기기
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
        """
    })

    wait = WebDriverWait(driver, 20)

    try:
        title = f"🎾 테스트 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        content = "자동 포스팅 테스트입니다.\n정상 동작 확인 중입니다."

        # ======================
        # 1. 로그인
        # ======================
        print("🔐 로그인 시도")
        driver.get("https://nid.naver.com/nidlogin.login")
        time.sleep(2)

        id_input = wait.until(EC.presence_of_element_located((By.ID, "id")))
        id_input.click()
        pyperclip.copy(NAVER_ID)
        ActionChains(driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()

        time.sleep(1)

        pw_input = driver.find_element(By.ID, "pw")
        pw_input.click()
        pyperclip.copy(NAVER_PW)
        ActionChains(driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()

        time.sleep(1)

        driver.find_element(By.ID, "log.login").click()
        time.sleep(5)

        if "nidlogin" in driver.current_url:
            print("❌ 로그인 실패 (보안 인증 필요 가능)")
            return

        print("✅ 로그인 성공")

        # ======================
        # 2. 글쓰기 진입
        # ======================
        driver.get(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}")

        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))

        # ======================
        # 3. 제목 입력
        # ======================
        title_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.se-title-input")))
        title_box.click()
        title_box.send_keys(title)

        # ======================
        # 4. 본문 입력 (핵심 수정)
        # ======================
        body = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.se-main-container")))
        body.click()
        body.send_keys(content)

        time.sleep(2)

        # ======================
        # 5. 발행
        # ======================
        publish = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.se-publish-button")))
        publish.click()

        time.sleep(2)

        confirm = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.se-confirm-button")))
        confirm.click()

        print("🏁 포스팅 완료")

        time.sleep(5)

    except Exception as e:
        print("❌ 에러:", e)

    finally:
        driver.quit()

if __name__ == "__main__":
    post_to_naver_blog()
