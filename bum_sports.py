import requests
import os
from datetime import datetime

# 깃허브 Secret 로드
NL_API_KEY = os.environ.get('NL_API_KEY')
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET')

def get_access_token():
    """네이버 API 인증 토큰 발급"""
    url = f"https://nid.naver.com/oauth2.0/token?grant_type=client_credentials&client_id={NAVER_CLIENT_ID}&client_secret={NAVER_CLIENT_SECRET}"
    try:
        response = requests.get(url, timeout=15)
        return response.json().get('access_token')
    except: return None

def post_to_naver_blog(title, contents):
    """네이버 블로그 포스팅 실행"""
    token = get_access_token()
    if not token: return
    url = "https://openapi.naver.com/v1/blog/writePost.json"
    headers = { "Authorization": f"Bearer {token}" }
    data = { "title": title, "contents": contents }
    try:
        res = requests.post(url, headers=headers, data=data, timeout=30)
        if res.status_code == 200:
            print("✅ [BUM Sports] 블로그 포스팅 최종 성공!")
        else:
            print(f"❌ 포스팅 실패: {res.text}")
    except: print("❌ 블로그 전송 오류")

def get_tennis_books():
    """사령관님의 성공한 SF 알리미 로직 이식"""
    url = "https://www.nl.go.kr/NL/search/openApi/search.do"
    headers = {'User-Agent': 'Mozilla/5.0'} # 차단 방지를 위한 필수 헤더
    
    # 사령관님의 SF 성공 파라미터와 100% 일치
    params = {
        'key': NL_API_KEY, 
        'kwd': '테니스', 
        'category': '도서',
        'sort': 'date', 
        'apiType': 'json', 
        'pageNum': 1, 
        'pageSize': 5
    }

    try:
        print("📡 사령관님의 성공 로직으로 테니스 정보를 낚아오는 중...")
        response = requests.get(url, params=params, headers=headers, timeout=60)
        data = response.json()
        items = data.get('result', [])

        if not items:
            return None, "📅 새로운 테니스 도서 정보가 없습니다."

        blog_title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 테니스 신간 소식"
        blog_body = f"<h2>사령관님, 오늘의 테니스 관련 신작 리스트입니다.</h2><br><p>BUM Sports가 전해드리는 따끈따끈한 소식입니다.</p><hr>"
        
        for idx, item in enumerate(items, 1):
            # 사령관님의 HTML 태그 제거 로직
            title = item.get('titleInfo').replace('<span class="searching_txt">', '').replace('</span>', '')
            author = item.get('authorInfo', '정보 없음')
            pub = item.get('pubInfo', '정보 없음')
            blog_body += f"<h3>{idx}. {title}</h3> - 저자: {author}<br> - 출판: {pub}<br><br>"
        
        blog_body += "<hr><p>#테니스 #BUMSports #범스포츠 #자동포스팅 #테니스신간</p>"
        return blog_title, blog_body

    except Exception as e:
        return None, f"❗ 데이터 가져오기 오류: {e}"

if __name__ == "__main__":
    print("🚀 BUM Sports 시스템 최종 가동...")
    title, content = get_tennis_books()
    
    if title:
        post_to_naver_blog(title, content)
    else:
        # 도서관 서버가 응답 없을 때를 위한 예비 소식 (블로그 지수 유지)
        post_to_naver_blog(f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 소식 알림", 
                           "현재 국립중앙도서관 데이터 서버 응답이 지연되고 있습니다. 곧 테니스 신작 정보를 들고 오겠습니다!")
        print(f"⚠️ {content}")
