import requests
import os
import time
from datetime import datetime

# 깃허브 Secret 로드
NL_API_KEY = os.environ.get('NL_API_KEY')
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET')

def get_access_token():
    url = f"https://nid.naver.com/oauth2.0/token?grant_type=client_credentials&client_id={NAVER_CLIENT_ID}&client_secret={NAVER_CLIENT_SECRET}"
    try:
        response = requests.get(url, timeout=20)
        return response.json().get('access_token')
    except: return None

def post_to_naver_blog(title, contents):
    token = get_access_token()
    if not token: return
    url = "https://openapi.naver.com/v1/blog/writePost.json"
    headers = { "Authorization": f"Bearer {token}" }
    data = { "title": title, "contents": contents }
    try:
        requests.post(url, headers=headers, data=data, timeout=30)
        print("✅ [BUM Sports] 블로그 포스팅 성공!")
    except: print("❌ 블로그 전송 실패")

def get_tennis_books():
    # 주소를 살짝 변경하고, pageSize를 3개로 줄여 서버 부담을 최소화했습니다.
    url = "https://www.nl.go.kr/NL/search/openApi/search.do"
    params = {
        'key': NL_API_KEY,
        'kwd': '테니스',
        'apiType': 'json',
        'sort': 'date',
        'pageSize': 3  # 정보를 3개만 가져오도록 축소 (성공률 높임)
    }

    print("📡 도서관 서버에 다시 접속 시도 중...")
    try:
        # 타임아웃을 90초로 더 늘렸습니다.
        response = requests.get(url, params=params, timeout=90) 
        data = response.json()
        items = data.get('result', [])

        if not items:
            return None, "📅 새로운 정보가 없습니다."

        blog_title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 테니스 소식"
        blog_body = "<h2>오늘의 테니스 신간 리스트</h2><br>"
        for idx, item in enumerate(items, 1):
            title = item.get('titleInfo').replace('<span class="searching_txt">', '').replace('</span>', '')
            blog_body += f"<b>{idx}. {title}</b><br> - 저자: {item.get('authorInfo')}<br><hr>"
        
        return blog_title, blog_body
    except Exception as e:
        return None, f"⏳ 서버가 여전히 바쁩니다: {e}"

if __name__ == "__main__":
    title, content = get_tennis_books()
    if title:
        post_to_naver_blog(title, content)
    else:
        # 만약 도서관이 죽었다면, '준비된 멘트'로라도 블로그를 채우는 전략!
        print("💡 도서관 대신 예비 소식으로 포스팅합니다.")
        post_to_naver_blog(f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 소식 알림", 
                           "오늘은 도서관 서버 점검 중입니다. 내일 더 알찬 테니스 소식으로 돌아오겠습니다!")
