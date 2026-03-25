import requests
import os
import time
from datetime import datetime

# 1. 깃허브 Secret 환경 변수 로드
NL_API_KEY = os.environ.get('NL_API_KEY')
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET')

def get_access_token():
    """네이버 Access Token 발급 (인증용)"""
    url = f"https://nid.naver.com/oauth2.0/token?grant_type=client_credentials&client_id={NAVER_CLIENT_ID}&client_secret={NAVER_CLIENT_SECRET}"
    try:
        response = requests.get(url, timeout=20)
        token = response.json().get('access_token')
        return token
    except Exception as e:
        print(f"❌ 토큰 발급 실패: {e}")
        return None

def post_to_naver_blog(title, contents):
    """네이버 블로그 포스팅 실행"""
    token = get_access_token()
    if not token:
        print("❌ 토큰이 없어 포스팅을 중단합니다.")
        return

    url = "https://openapi.naver.com/v1/blog/writePost.json"
    headers = { "Authorization": f"Bearer {token}" }
    data = { "title": title, "contents": contents }
    
    try:
        response = requests.post(url, headers=headers, data=data, timeout=30)
        if response.status_code == 200:
            print(f"✅ [BUM Sports] 블로그 포스팅 성공!")
        else:
            print(f"❌ 포스팅 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 블로그 전송 중 오류: {e}")

def get_tennis_books():
    """국립중앙도서관 API에서 테니스 신간 가져오기 (타임아웃 보강)"""
    url = "https://www.nl.go.kr/NL/search/openApi/search.do"
    params = {
        'key': NL_API_KEY, 
        'kwd': '테니스', 
        'apiType': 'json', 
        'sort': 'date', 
        'pageSize': 5
    }

    # 도서관 서버 응답이 늦을 경우를 대비해 3번까지 재시도합니다.
    for attempt in range(3):
        try:
            print(f"📡 도서관 서버 연결 시도 중... ({attempt + 1}/3)")
            # 대기 시간을 60초로 넉넉하게 잡았습니다.
            response = requests.get(url, params=params, timeout=60) 
            data = response.json()
            items = data.get('result', [])

            if not items:
                return None, "📅 오늘 신규 등록된 테니스 도서가 없습니다."

            blog_title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 테니스 신간 소식"
            blog_body = f"<h2>사령관님, 오늘의 테니스 관련 신작 리스트입니다.</h2><br>"
            blog_body += "<p>범 스포츠(BUM Sports)가 전해드리는 따끈따끈한 도서 정보입니다.</p><br><hr>"
            
            for idx, item in enumerate(items, 1):
                title = item.get('titleInfo').replace('<span class="searching_txt">', '').replace('</span>', '')
                author = item.get('authorInfo', '저자 미상')
                pub = item.get('pubInfo', '출판사 정보 없음')
                blog_body += f"<h3>{idx}. {title}</h3>"
                blog_body += f"<p><b>저자:</b> {author}<br><b>출판:</b> {pub}</p><br>"
            
            blog_body += "<hr><p>#테니스 #BUMSports #범스포츠 #테니스신간 #자동화포스팅</p>"
            return blog_title, blog_body

        except requests.exceptions.Timeout:
            print(f"⏳ {attempt + 1}회차 시도 타임아웃! 5초 후 다시 시도합니다...")
            time.sleep(5)
        except Exception as e:
            return None, f"❗ 데이터 가져오기 중 예상치 못한 오류: {e}"
    
    return None, "❌ 도서관 서버 응답 지연으로 데이터를 가져오지 못했습니다."

if __name__ == "__main__":
    print("🚀 BUM Sports 자동화 로봇 가동 시작...")
    title, content = get_tennis_books()
    
    if title:
        post_to_naver_blog(title, content)
    else:
        print(f"⚠️ 결과: {content}")
