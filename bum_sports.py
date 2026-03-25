import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import requests
from datetime import datetime

# ===== 설정 (사령관님 맞춤) =====
NAVER_ID = "parkbs669" # 사령관님 아이디 직접 입력
# 깃허브 Secrets에서 가져오기
NL_API_KEY = os.environ.get('NL_API_KEY')
NAVER_PW = os.environ.get('NAVER_PASSWORD') # 사령관님 Secret 이름과 똑같이 맞췄습니다!

def get_tennis_books():
    # 도서관 API 부분 (기존과 동일)
    url = "https://www.nl.go.kr/NL/search/openApi/search.do"
    params = {'key': NL_API_KEY, 'kwd': '테니스', 'category': '도서', 'apiType': 'json', 'pageSize': 5}
    try:
        print("📡 도서관 서버 응답 대기 중...")
        res = requests.get(url, params=params, timeout=20)
        items = res.json().get('result', [])
        if items:
            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 테니스 신간"
            body = "<h3>오늘의 테니스 도서 목록입니다.</h3><br>"
            for item in items:
                title_info = item.get('titleInfo').replace('<span class="searching_txt">', '').replace('</span>', '')
                body += f"<b>- {title_info}</b><br>"
            return title, body
    except: pass
    return f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 소식 안내", "현재 도서관 서버 응답이 지연되어 테니스 소식을 잠시 후 업데이트 하겠습니다. 로저범서 블로그를 찾아주셔서 감사합니다!"

def naver_blog_post(title, content):
    chrome_options = Options()
    # 깃허브 액션 환경에서는 반드시 화면 없이(headless) 실행해야 합니다.
    chrome_options.add_argument('--headless') 
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # 캡차 피하기 위해 사용자 에이전트 추가
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36')

    # 크롬 드라이버 자동 설치 및 실행
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        print("🚀 네이버 로그인 시도 중...")
        # 1. 로그인 페이지 이동
        driver.get("https://nid.naver.com/nidlogin.login")
        time.sleep(2)
        
        # 2. 아이디/비번 입력 (캡차를 피하기 위해 자바스크립트로 강제 입력)
        driver.execute_script(f"document.getElementsByName('id')[0].value='{NAVER_ID}'")
        driver.execute_script(f"document.getElementsByName('pw')[0].value='{NAVER_PW}'")
        time.sleep(1)
        driver.find_element(By.ID, "log.login").click()
        time.sleep(3)
        
        # 로그인 성공 여부 간단 확인
        if "My 영역" in driver.page_source or NAVER_ID in driver.page_source:
            print("✅ 로그인 성공!")
        else:
            print("❌ 로그인 실패... 비밀번호를 다시 확인해 주세요.")
            return

        print("📝 글쓰기 페이지 이동 중...")
        # 3. 글쓰기 페이지 이동 (아이디 직접 사용)
        driver.get(f"https://blog.naver.com/{NAVER_ID}?Redirect=Write")
        time.sleep(3)
        
        # 기본 에디터 설정 때문에 iframe 처리가 필요할 수 있지만, 스마트에디터 ONE은 직접 입력이 가능합니다.
        print("✍️ 제목 및 내용 입력 중...")
        
        # 제목 입력 (클래스 이름은 네이버 업데이트에 따라 바뀔 수 있습니다.)
        title_element = driver.find_element(By.CSS_SELECTOR, ".se-ff-nanumgothic, .se-placeholder__text")
        title_element.click()
        title_element.send_keys(title)
        time.sleep(1)
        
        # 내용 입력
        content_element = driver.find_element(By.CSS_SELECTOR, ".se-content-placeholder, .se-component-content")
        content_element.click()
        content_element.send_keys(content)
        time.sleep(1)
        
        print("📤 발행 버튼 클릭 중...")
        # 4. 발행 버튼 클릭
        publish_btn = driver.find_element(By.CSS_SELECTOR, ".publish_btn, .se-publish-button")
        publish_btn.click()
        time.sleep(2)
        
        # 최종 확인 버튼 클릭
        confirm_btn = driver.find_element(By.CSS_SELECTOR, ".confirm_btn, .se-confirm-button")
        confirm_btn.click()
        time.sleep(3)
        
        print("✅✅ [최종 확인] 셀레늄으로 네이버 블로그 포스팅 성공!")
    except Exception as e:
        print(f"❌ 실패: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    t, c = get_tennis_books()
    naver_blog_post(t, c)
