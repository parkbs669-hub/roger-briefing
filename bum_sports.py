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

# ===== [1] 설정 및 환경 변수 =====
NAVER_ID = "parkbs669"
NL_API_KEY = os.environ.get('NL_API_KEY')
NAVER_PW = os.environ.get('NAVER_PASSWORD')

# ===== [2] 도서 API 타임아웃 해결 (재시도 로직) =====
def get_tennis_books():
    url = "https://www.nl.go.kr/NL/search/openApi/search.do"
    params = {'key': NL_API_KEY, 'kwd': '테니스', 'category': '도서', 'apiType': 'json', 'pageSize': 3}
    
    for i in range(3):  # 최대 3번 재시도
        try:
            print(f"📡 [도서 API] 시도 중... ({i+1}/3)")
            res = requests.get(url, params=params, timeout=60) # 타임아웃 60초로 확장
            items = res.json().get('result', [])
            if items:
                title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 테니스 소식"
                body_list = ["오늘의 테니스 도서 리포트입니다.", ""]
                for item in items:
                    t = item.get('titleInfo', '').replace('<span class="searching_txt">', '').replace('</span>', '')
                    body_list.append(f"● {t}")
                return title, body_list
        except Exception as e:
            print(f"⚠️ API 시도 중 오류 발생: {e}")
            time.sleep(2)
            
    # API 실패 시 Fallback (멈추지 않고 진행)
    print("⚠️ API 최종 실패 → 기본 텍스트로 전환")
    return f"🎾 [BUM Sports] 안내", ["오늘의 새로운 테니스 소식을 준비 중입니다.", "잠시 후 블로그에서 확인해주세요!"]

def post_to_naver_blog(title, body_list):
    # ===== [3] 드라이버 옵션 강화 (봇 탐지 회피) =====
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

    # [🚨 해결 1] 크롬드라이버 자동 매칭
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # [🚨 해결 3-2] navigator.webdriver 감지 제거
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    try:
        # ===== [4] 로그인 (클립보드 우회 방식) =====
        print("🔐 [로그인] 네이버 진입...")
        driver.get("https://nid.naver.com/nidlogin.login")
        time.sleep(3)

        # GitHub Actions 환경에서는 pyperclip 대신 스크립트 직접 주입 방식을 사용합니다.
        driver.execute_script("document.getElementsByName('id')[0].value=arguments[0]", NAVER_ID)
        time.sleep(1.5)
        driver.execute_script("document.getElementsByName('pw')[0].value=arguments[0]", NAVER_PW)
        time.sleep(1.5)
        
        driver.find_element(By.ID, "log.login").click()
        time.sleep(5)

        if "nidlogin" in driver.current_url:
            print("❌ [실패] 네이버 봇 탐지에 막혔습니다.")
            return
        print("✅ [성공] 로그인 완료")

        # ===== [5] 글쓰기 진입 및 포스팅 =====
        print("📝 [글쓰기] 에디터 이동 중...")
        driver.get(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}")
        
        # mainFrame 발견 시까지 끈질기게 대기
        WebDriverWait(driver, 30).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
        print("✅ 에디터 프레임 진입 성공")

        # 제목 입력
        title_box = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea.se-title-input")))
        title_box.click()
        title_box.send_keys(title)
        time.sleep(2)

        # 본문 입력 (직접 주입 방식)
        print("✍️ 본문 작성 중...")
        content_box = driver.find_element(By.CSS_SELECTOR, ".se-content-placeholder, .se-component-content")
        content_box.click()
        time.sleep(1)

        for line in body_list:
            driver.switch_to.active_element.send_keys(line)
            driver.switch_to.active_element.send_keys(Keys.ENTER)
            time.sleep(0.4)

        # 발행 버튼
        print("📤 발행 시도...")
        publish_btn = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.se-publish-button")))
        publish_btn.click()
        time.sleep(2)

        confirm_btn = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.se-confirm-button")))
        confirm_btn.click()
        
        time.sleep(10)
        print("🏁🏁🏁 [최종 성공] 사령관님, 포스팅이 완료되었습니다!")

    except Exception as e:
        print(f"❌ [에러 발생]: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    t, b = get_tennis_books()
    post_to_naver_blog(t, b)
