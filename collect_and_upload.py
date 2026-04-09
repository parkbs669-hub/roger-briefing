import os
import json
import requests
from datetime import date
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- 설정 (Secrets 환경변수) ---
UNSPLASH_ACCESS_KEY = os.environ["UNSPLASH_ACCESS_KEY"]
GDRIVE_CREDENTIALS = os.environ["GDRIVE_CREDENTIALS"]
GDRIVE_FOLDER_ID = os.environ["GDRIVE_FOLDER_ID"]

TODAY = date.today().strftime("%Y-%m-%d")
BASE_URL = "https://api.unsplash.com/search/photos"

# 검색 키워드 설정
SEARCH_QUERIES = [
    {"query": "tennis string racket closeup", "category": "string_closeup", "label": "스트링 클로즈업"},
    {"query": "tennis racket strings detail", "category": "string_detail", "label": "스트링 디테일"},
    {"query": "tennis player forehand action", "category": "player_forehand", "label": "선수 포핸드"},
    {"query": "tennis player serve action", "category": "player_serve", "label": "선수 서브"},
    {"query": "tennis stringing machine", "category": "stringing_machine", "label": "스트링 머신"},
    # 필요한 만큼 추가하세요...
]

def get_gdrive_service():
    token_dict = json.loads(GDRIVE_CREDENTIALS)
    creds = Credentials.from_authorized_user_info(token_dict)
    return build('drive', 'v3', credentials=creds)

def upload_to_drive(service, file_path, filename):
    file_metadata = {'name': filename, 'parents': [GDRIVE_FOLDER_ID]}
    media = MediaFileUpload(file_path, resumable=True)
    try:
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"  ✅ 구글 드라이브 업로드 성공: {filename}")
    except Exception as e:
        print(f"  ❌ 업로드 실패: {e}")

def main():
    service = get_gdrive_service()
    print(f"🎾 테니스 이미지 수집 및 드라이브 업로드 시작: {TODAY}")

    for i, q in enumerate(SEARCH_QUERIES):
        print(f"[{i+1}/{len(SEARCH_QUERIES)}] {q['label']} 수집 중...")
        try:
            # 1. Unsplash 검색
            headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
            params = {"query": q["query"], "per_page": 5, "orientation": "landscape"}
            res = requests.get(BASE_URL, params=params, headers=headers)
            res.raise_for_status()
            
            data = res.json()["results"]
            if not data: continue
            
            # 날짜별로 다른 이미지 선택
            pick = data[date.today().timetuple().tm_yday % len(data)]
            img_url = pick["urls"]["regular"]
            
            # 2. 이미지 다운로드 (임시 저장)
            img_data = requests.get(img_url).content
            temp_filename = f"{TODAY}_{q['category']}.jpg"
            with open(temp_filename, "wb") as f:
                f.write(img_data)
            
            # 3. 구글 드라이브 업로드
            upload_to_drive(service, temp_filename, temp_filename)
            
            # 4. 임시 파일 삭제 (용량 관리)
            os.remove(temp_filename)
            
        except Exception as e:
            print(f"  ❌ 실패: {e}")

if __name__ == "__main__":
    main()
