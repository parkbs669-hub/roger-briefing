import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import requests
from datetime import datetime

def get_tennis_books():
    # 도서관 API 부분 (기존과 동일)
    url = "https://www.nl.go.kr/NL/search/openApi/search.do"
    params = {'key': os.environ.get('NL_API_KEY'), 'kwd': '테니스', 'category': '도서', 'apiType': 'json', 'pageSize': 5}
    try:
        res = requests.get(url, params=params, timeout=20)
        items = res.json().get('result', [])
        if items:
            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 테니스 신간"
            body = "오늘의 테니스 도서 목록입니다.\n\n"
            for item in items:
                body += f"- {item.get('titleInfo')}\n"
            return title, body
    except: pass
    return f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 소식", "도서관 서버 점검 중입니다."

def naver_blog_post(title, content):
    chrome_options = Options()
    chrome_options.add_argument('--headless') # 화면 없이 실행
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 1. 로그인 페이지 이동
        driver.get("https://nid.naver.com/nidlogin.login")
        
        # 2. 아이디/비번 입력 (캡차 피하기 위해 자바스크립트 사용)
        driver.execute_script(f"document.getElementsByName('id')[0].value='{os.environ.get('NAVER_ID')}'")
        driver.execute_script(f"document.getElementsByName('pw')[0].value='{os.environ.get('NAVER_PW')}'")
        driver.find_element(By.ID, "log.login").click()
        time.sleep(3)
        
        # 3. 글쓰기 페이지 이동
        driver.get(f"https://blog.naver.com/{os.environ.get('NAVER_ID')}?Redirect=Write")
        time.sleep(3)
        
        # 4. 제목 및 내용 입력
        driver.find_element(By.CSS_SELECTOR, ".se-ff-nanumgothic").send_keys(title)
        driver.find_element(By.CSS_SELECTOR, ".se-content-placeholder").send_keys(content)
        
        # 5. 발행 버튼 클릭
        driver.find_element(By.CSS_SELECTOR, ".publish_btn").click()
        time.sleep(2)
        driver.find_element(By.CSS_SELECTOR, ".confirm_btn").click()
        
        print("✅✅ 셀레늄으로 포스팅 성공!")
    except Exception as e:
        print(f"❌ 실패: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    t, c = get_tennis_books()
    naver_blog_post(t, c)
