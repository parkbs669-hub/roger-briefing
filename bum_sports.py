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

# ===== 사령관님 설정 정보 =====
NAVER_ID = "parkbs669"
NL_API_KEY = os.environ.get('NL_API_KEY')
NAVER_PW = os.environ.get('NAVER_PASSWORD')

def get_tennis_books():
    """국립중앙도서관 API에서 테니스 신간 정보를 가져옵니다."""
    url = "https://www.nl.go.kr/NL/search/openApi/search.do"
    params = {
        'key': NL_API_KEY,
        'kwd': '테니스',
        'category': '도서',
        'apiType': 'json',
        'pageSize': 5
    }
    try:
        print("📡 도서관 서버에서 신간 검색 중...")
        res = requests.get(url, params=params, timeout=20)
        items = res.json().get('result', [])
        if items:
            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 테니스 신간 소식"
            body = "오늘의 테니스 관련 신간 도서 목록입니다.<br><br>"
            for item in items:
                t_info = item.get('titleInfo').replace('<span class="searching_txt">', '').replace('</span>', '')
                body += f"<b>- {t_info}</b><br>"
            return title, body
    except Exception as e:
        print(f"⚠️ 도서관 API 오류: {e}")
    
    return f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 안내", "현재 도서관 서버 응답이 지연되어 테니스 소식을 잠시 후 업데이트 하겠습니다."

def post_to_naver(title, content):
    """셀레늄을 사용하여 네이버 블로그에 강제로 글을 작성합니다."""
    chrome_options = Options()
    chrome_options.add_argument('--headless') # 깃허브 액션 필수 설정
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # 1. 로그인 단계 (이미 성공 확인됨)
        print("🔐 네이버 로그인 시도...")
        driver.get("https://nid.naver.com/nidlogin.login")
        time.sleep(2)
        driver.execute_script(f"document.getElementsByName('id')[0].value='{NAVER_ID}'")
        driver.execute_script(f"document.getElementsByName('pw')[0].value='{NAVER_PW}'")
        driver.find_element(By.ID, "log.login").click()
        time.sleep(3)

        # 2. 글쓰기 페이지 진입
        print("📝 글쓰기 페이지 진입 중...")
        driver.get(f"https://blog.naver.com/{NAVER_ID}?Redirect=Write")
        time.sleep(5) # 에디터 로딩 대기

        # 3. 핵심: 네이버 에디터 'mainFrame'으로 전환 (이게 없으면 요소를 못 찾음)
        driver.switch_to.frame("mainFrame")
        print("🖼️ 에디터 프레임 전환 성공!")

        # 4. 제목 입력 (자바스크립트 주입 방식 - 가장 안전)
        print("✍️ 제목 입력 중...")
        title_area = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".se-ff-nanumgothic, .se-placeholder__text"))
        )
        driver.execute_script(f"document.querySelector('.se-ff-nanumgothic, .se-placeholder__text').innerText = '{title}';")
        time.sleep(1)

        # 5. 본문 입력
        print("✍️ 본문 내용 작성 중...")
        content_area = driver.find_element(By.CSS_SELECTOR, ".se-content-placeholder, .se-component-content")
        content_area.click()
        # 실제 키보드 입력을 흉내내어 본문 작성
        webdriver.ActionChains(driver).send_keys(content).perform()
        time.sleep(2)

        # 6. 최종 발행 버튼 클릭
        print("📤 발행 시작...")
        driver.find_element(By.CSS_SELECTOR, ".publish_btn, .se-publish-button").click()
        time.sleep(2)
        
        # 확인 버튼 클릭
        confirm_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".confirm_btn, .se-confirm-button"))
        )
        confirm_btn.click()
        time.sleep(5)

        print("✅✅ [미션 완료] 블로그 포스팅이 성공적으로 완료되었습니다!")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    blog_title, blog_content = get_tennis_books()
    post_to_naver(blog_title, blog_content)
