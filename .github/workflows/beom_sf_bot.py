import requests
import os
from datetime import datetime, timedelta

# 깃허브 Secret에서 API 키를 가져옵니다.
API_KEY = os.environ.get('NL_API_KEY')

def get_new_sf_books():
    # 국립중앙도서관 검색 API 엔드포인트
    url = "https://www.nl.go.kr/NL/search/openApi/search.do"
    
    # 검색 파라미터 설정: 'SF 소설' 키워드, 최신순(date), JSON 형식
    params = {
        'key': API_KEY,
        'kwd': 'SF 소설',
        'category': '도서',
        'sort': 'date',
        'apiType': 'json',
        'pageNum': 1,
        'pageSize': 10
    }

    print(f"🚀 {datetime.now().strftime('%Y-%m-%d %H:%M')} - '범 SF 알리미' 가동 시작")

    try:
        response = requests.get(url, params=params)
        data = response.json()
        items = data.get('result', [])

        if not items:
            print("📅 오늘 새로 등록된 SF 소설 정보가 없습니다.")
            return

        print(f"\n📚 최근 등록된 SF 신간 리스트 ({len(items)}건)\n")
        print("="*60)
        for idx, item in enumerate(items, 1):
            title = item.get('titleInfo', '제목 정보 없음')
            author = item.get('authorInfo', '저자 정보 없음')
            pub = item.get('pubInfo', '출판사 정보 없음')
            date = item.get('pubDateInfo', '날짜 정보 없음')
            
            print(f"{idx}. {title}")
            print(f"   👤 저자: {author}")
            print(f"   🏢 출판: {pub} ({date})")
            print("-" * 60)

    except Exception as e:
        print(f"❗ API 호출 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    get_new_sf_books()
