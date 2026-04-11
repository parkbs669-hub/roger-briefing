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
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")
GDRIVE_CREDENTIALS = os.environ.get("GDRIVE_CREDENTIALS")
GDRIVE_FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID")

TODAY = date.today().strftime("%Y-%m-%d")
UNSPLASH_URL = "https://api.unsplash.com/search/photos"
PIXABAY_URL = "https://pixabay.com/api/"

# --- 검색 키워드 설정: '테니스 여성' 테마로 집중 최적화 ---
SEARCH_QUERIES = [
    {"query": "woman playing tennis", "category": "action_play", "label": "경기 중인 여성"},
    {"query": "female tennis player court", "category": "player_court", "label": "코트 위 선수"},
    {"query": "woman tennis serve", "category": "action_serve", "label": "서브 동작"},
    {"query": "woman tennis backhand", "category": "action_backhand", "label": "백핸드 동작"},
    {"query": "tennis woman smile racket", "category": "portrait_smile", "label": "라켓을 든 미소"},
    {"query": "female tennis fashion style", "category": "fashion_style", "label": "테니스 패션"},
    {"query": "woman sitting on tennis court", "category": "lifestyle_rest", "label": "코트 위 휴식"},
    {"query": "professional female tennis match", "category": "pro_match", "label": "프로 경기 장면"},
    {"query": "woman athlete tennis training", "category": "training_shot", "label": "훈련 장면"},
    {"query": "woman holding tennis ball", "category": "detail_ball", "label": "공을 든 클로즈업"}
]

def get_gdrive_service():
    if not GDRIVE_CREDENTIALS:
        raise ValueError("GDRIVE_CREDENTIALS 환경 변수가 없습니다.")
    token_dict = json.loads(GDRIVE_CREDENTIALS)
    creds = Credentials.from_authorized_user_info(token_dict)
    return build('drive', 'v3', credentials=creds)

def upload_to_drive(service, file_path, filename):
    file_metadata = {'name': filename, 'parents': [GDRIVE_FOLDER_ID]}
    media = MediaFileUpload(file_path, resumable=True)
    try:
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"  ✅ 드라이브 업로드 성공: {filename}")
    except Exception as e:
        print(f"  ❌ 드라이브 업로드 실패: {e}")

def main():
    if not all([UNSPLASH_ACCESS_KEY, PIXABAY_API_KEY, GDRIVE_CREDENTIALS, GDRIVE_FOLDER_ID]):
        print("❌ 설정 오류: GitHub Secrets를 확인하세요.")
        return

    try:
        service = get_gdrive_service()
    except Exception as e:
        print(f"❌ 구글 인증 실패: {e}")
        return

    print(f"\n🎾 BUM Sports 여성 테니스 이미지 수집 시작: {TODAY}")
    day_idx = date.today().timetuple().tm_yday
    
    for i, q in enumerate(SEARCH_QUERIES):
        print(f"[{i+1}/{len(SEARCH_QUERIES)}] {q['label']} 수집 중...")
        
        # --- 1. Unsplash 수집 ---
        try:
            us_params = {"query": q["query"], "per_page": 15, "orientation": "landscape"}
            us_headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
            us_res = requests.get(UNSPLASH_URL, params=us_params, headers=us_headers, timeout=15)
            us_results = us_res.json().get("results", [])
            
            if us_results:
                # 매일 다른 이미지를 가져오기 위해 인덱스 활용
                pick = us_results[day_idx % len(us_results)]
                img_data = requests.get(pick["urls"]["regular"], timeout=30).content
                filename = f"{TODAY}_{i+1:02d}_{q['category']}_us.jpg"
                with open(filename, "wb") as f: f.write(img_data)
                upload_to_drive(service, filename, filename)
                os.remove(filename)
        except Exception as e:
            print(f"  ❌ Unsplash 오류: {e}")

        # --- 2. Pixabay 수집 ---
        try:
            pb_params = {
                "key": PIXABAY_API_KEY,
                "q": q["query"],
                "image_type": "photo",
                "orientation": "horizontal",
                "per_page": 15
            }
            pb_res = requests.get(PIXABAY_URL, params=pb_params, timeout=15)
            pb_results = pb_res.json().get("hits", [])

            if pb_results:
                pick = pb_results[day_idx % len(pb_results)]
                img_data = requests.get(pick["largeImageURL"], timeout=30).content
                filename = f"{TODAY}_{i+1:02d}_{q['category']}_pb.jpg"
                with open(filename, "wb") as f: f.write(img_data)
                upload_to_drive(service, filename, filename)
                os.remove(filename)
        except Exception as e:
            print(f"  ❌ Pixabay 오류: {e}")

if __name__ == "__main__":
    main()
