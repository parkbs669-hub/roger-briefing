import os
import json
import requests
from datetime import date
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- 설정 (GitHub Secrets) ---
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")
GDRIVE_CREDENTIALS = os.environ.get("GDRIVE_CREDENTIALS")
GDRIVE_FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID")

TODAY = date.today().strftime("%Y-%m-%d")
BASE_URL = "https://api.unsplash.com/search/photos"

# --- 검색 키워드 설정 (문법 오류 수정 완료) ---
SEARCH_QUERIES = [
    {"query": "tennis string racket closeup", "category": "string_closeup", "label": "스트링 클로즈업"},
    {"query": "tennis racket strings detail", "category": "string_detail", "label": "스트링 디테일"},
    {"query": "tennis player forehand action", "category": "player_forehand", "label": "선수 포핸드"},
    {"query": "tennis player serve action", "category": "player_serve", "label": "선수 서브"},
    {"query": "tennis stringing machine", "category": "stringing_machine", "label": "스트링 머신"},
    {"query": "tennis stringing tools awl pliers", "category": "stringing_tools", "label": "스트링 도구"},
    {"query": "tennis racket tension calibration", "category": "tension_check", "label": "텐션 측정"},
    {"query": "tennis grip tape wrap texture", "category": "grip_detail", "label": "그립 테이프"},
    {"query": "tennis racket stencil logo", "category": "racket_stencil", "label": "라켓 스텐실"},
    {"query": "tennis player sliding clay court", "category": "player_slide", "label": "클레이 슬라이딩"},
    {"query": "tennis ball hitting racket strings", "category": "impact_moment", "label": "임팩트 순간"},
    {"query": "professional tennis stadium night", "category": "stadium_night", "label": "야간 경기장"},
    {"query": "tennis balls in a basket hopper", "category": "ball_basket", "label": "볼 카트"},
    {"query": "vintage tennis racket wooden", "category": "vintage_tennis", "label": "빈티지 라켓"},
    {"query": "shaking hands after tennis match", "category": "sportsmanship", "label": "경기 후 악수"}
]

def get_gdrive_service():
    if not GDRIVE_CREDENTIALS:
        raise ValueError("GDRIVE_CREDENTIALS 환경 변수가 없습니다.")
    token_dict = json.loads(GDRIVE_CREDENTIALS)
    creds = Credentials.from_authorized_user_info(token_dict)
    return build('drive', 'v3', credentials=creds)

def upload_to_drive(service, file_path, filename):
    file_metadata = {
        'name': filename,
        'parents': [GDRIVE_FOLDER_ID]
    }
    media = MediaFileUpload(file_path, resumable=True)
    try:
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"  ✅ 드라이브 업로드 성공: {filename}")
    except Exception as e:
        print(f"  ❌ 드라이브 업로드 실패: {e}")

def main():
    if not all([UNSPLASH_ACCESS_KEY, GDRIVE_CREDENTIALS, GDRIVE_FOLDER_ID]):
        print("❌ 설정 오류: GitHub Secrets를 확인하세요.")
        return

    try:
        service = get_gdrive_service()
    except Exception as e:
        print(f"❌ 구글 인증 실패: {e}")
        return

    print(f"\n🎾 BUM Sports 이미지 수집 및 업로드 시작: {TODAY}")
    
    for i, q in enumerate(SEARCH_QUERIES):
        print(f"[{i+1}/{len(SEARCH_QUERIES)}] {q['label']} 처리 중...")
        try:
            headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
            params = {"query": q["query"], "per_page": 10, "orientation": "landscape"}
            
            res = requests.get(BASE_URL, params=params, headers=headers, timeout=15)
            res.raise_for_status()
            results = res.json().get("results", [])

            if not results:
                continue

            # 날짜별 이미지 선택
            day_idx = date.today().timetuple().tm_yday
            pick = results[day_idx % len(results)]
            
            # 다운로드 실행
            img_data = requests.get(pick["urls"]["regular"], timeout=30).content
            filename = f"{TODAY}_{i+1:02d}_{q['category']}.jpg"
            
            with open(filename, "wb") as f:
                f.write(img_data)

            upload_to_drive(service, filename, filename)
            os.remove(filename) # 임시 파일 삭제

        except Exception as e:
            print(f"  ❌ 오류 발생 ({q['label']}): {e}")

if __name__ == "__main__":
    main()
