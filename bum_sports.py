import requests
import os
from datetime import datetime

# 깃허브 Secret 로드
NL_API_KEY = os.environ.get('NL_API_KEY')
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET')

def get_access_token():
    url = f"https://nid.naver.com/oauth2.0/token?grant_type=client_credentials&client_id={NAVER_CLIENT_ID}&client_secret={NAVER_CLIENT_SECRET}"
    try:
        response = requests.get(url, timeout=15)
        return response.json().get('access_token')
    except: return None

def post_to_naver_blog(title, contents):
    token = get_access_token()
    if not token: 
        print("❌ 토큰 발급 실패")
        return
    url = "https://openapi.naver.com/v1/blog/writePost.json"
    headers = { "Authorization": f"Bearer {token}" }
    data = { "title": title, "contents": contents }
    try:
        res = requests.post(url, headers=headers, data=data, timeout=30)
        if res.status_code == 200:
            print("✅✅ [최종 확인] 네이버 블로그 포스팅 성공!")
        else:
            print(f"❌ 포스팅 실패 에러: {res.text}")
    except Exception as e:
        print(f"❌ 전송 오류: {e}")

def get_tennis_books():
    url = "https://www.nl.go.kr/NL/search/openApi/search.do"
    headers = {'User-Agent': 'Mozilla/5.0'}
    params = {
        'key': NL_API_KEY, 
        'kwd': '테니스', 
        'category': '도서',
        'apiType': 'json', 
        'pageSize': 5
    }

    try:
        print("📡 도서관 서버 응답 대기 중 (최대 30초)...")
        # 이번에는 시간을 짧게 잡고, 안 오면 바로 예비 소식으로 넘어갑니다.
        response = requests.get(url, params=params, headers=headers, timeout=20)
        data = response.json()
        items = data.get('result', [])

        if items:
            blog_title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 테니스 신간"
            blog_body = "<h3>오늘의 테니스 도서 목록입니다.</h3><br>"
            for item in items:
                title = item.get('titleInfo').replace('<span class="searching_txt">', '').replace('</span>', '')
                blog_body += f"<b>- {title}</b><br>"
            return blog_title, blog_body
    except:
        pass # 에러 나면 아래 예비 소식으로 이동
    
    # 도서관 서버가 느릴 때 올리는 예비 포스팅
    return f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 소식 안내", "현재 도서관 서버 응답이 지연되어 테니스 소식을 잠시 후 업데이트 하겠습니다. 로저범서 블로그를 찾아주셔서 감사합니다!"

if __name__ == "__main__":
    title, content = get_tennis_books()
    post_to_naver_blog(title, content)
