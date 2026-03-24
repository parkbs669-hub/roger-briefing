import requests
import os
from datetime import datetime

# 깃허브 Secret에서 API 키를 가져옵니다.
API_KEY = os.environ.get('NL_API_KEY')

def get_new_sf_books():
    url = "https://www.nl.go.kr/NL/search/openApi/search.do"
    
    # 서버 차단을 방지하기 위한 '사람 브라우저' 정보 추가
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    params = {
        'key': API_KEY,
        'kwd': 'SF 소설',
        'category': '도서',
        'sort': 'date',
        'apiType': 'json',
        'pageNum': 1,
        'pageSize': 10
    }

    print(f"🚀 {datetime.now().strftime('%Y-%m-%d %H:%M')} - '범 SF 알리미' 재기동")

    try:
        # headers를 추가하여 호출합니다.
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        # 만약 JSON 응답이 아니면 오류 메시지 출력
        if response.status_code != 200:
            print(f"❌ 서버 응답 에러: {response.status_code}")
            return

        data = response.json()
        items = data.get('result', [])

        if not items:
            print("📅 현재 등록된 새로운 SF 소설 정보가 없습니다.")
            return

        print(f"\n📚 범 SF 신간 리스트 ({len(items)}건)\n" + "="*60)
        for idx, item in enumerate(items, 1):
            print(f"{idx}. {item.get('titleInfo')}")
            print(f"   👤 저자: {item.get('authorInfo')} | 🏢 {item.get('pubInfo')}")
            print("-" * 60)

    except Exception as e:
        print(f"❗ 연결 오류 발생: {e}")
        print("💡 팁: API 서버가 일시적으로 바쁠 수 있으니 잠시 후 다시 시도해 보세요.")

if __name__ == "__main__":
    get_new_sf_books()
