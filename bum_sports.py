import requests
import os
from datetime import datetime

# 1. 환경 변수 로드 (GitHub Secrets에 등록된 이름과 일치해야 합니다)
NL_API_KEY = os.environ.get('NL_API_KEY')
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET')

def get_access_token():
    """네이버 아이디로 로그인 API를 통해 Access Token을 받아오는 함수"""
    # 주의: 최초 1회는 브라우저 인증이 필요할 수 있으나, 
    # 검색 API 권한만으로 글쓰기가 가능한 '연결형 서비스' 설정을 마쳤다면 작동합니다.
    url = f"https://nid.naver.com/oauth2.0/token?grant_type=client_credentials&client_id={NAVER_CLIENT_ID}&client_secret={NAVER_CLIENT_SECRET}"
    
    try:
        response = requests.get(url)
        token = response.json().get('access_token')
        return token
    except Exception as e:
        print(f"❌ 토큰 발급 실패: {e}")
        return None

def post_to_naver_blog(title, contents):
    """실제로 네이버 블로그에 포스팅을 실행하는 함수"""
    token = get_access_token()
    if not token:
        return

    url = "https://openapi.naver.com/v1/blog/writePost.json"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    data = {
        "title": title,
        "contents": contents
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            print(f"✅ [BUM Sports] 블로그 포스팅 성공!")
        else:
            print(f"❌ 포스팅 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 네트워크 오류: {e}")

def get_tennis_books():
    """국립중앙도서관에서 테니스 신간 정보를 가져오는 함수"""
    url = "https://www.nl.go.kr/NL/search/openApi/search.do"
    params = {
        'key': NL_API_KEY, 
        'kwd': '테니스', 
        'apiType': 'json', 
        'sort': 'date', 
        'pageSize': 5
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        items = data.get('result', [])

        if not items:
            return None, "📅 오늘 신규 등록된 테니스 도서가 없습니다."

        blog_title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 테니스 신간 소식"
        
        # 블로그 본문 디자인 (HTML 적용)
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

    except Exception as e:
        return None, f"❗ 도서 데이터 가져오기 오류: {e}"

if __name__ == "__main__":
    print("🚀 BUM Sports 자동화 시스템 가동...")
    title, content = get_tennis_books()
    
    if title:
        post_to_naver_blog(title, content)
    else:
        print(content)
