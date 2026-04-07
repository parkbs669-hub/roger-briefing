import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 1. 인증 정보 및 폴더 ID 가져오기
creds_json = os.environ.get('GDRIVE_CREDENTIALS')
folder_id = os.environ.get('GDRIVE_FOLDER_ID')

creds_dict = json.loads(creds_json)
creds = service_account.Credentials.from_service_account_info(creds_dict)
service = build('drive', 'v3', credentials=creds)

def upload_file(file_path):
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"✅ 업로드 완료: {os.path.basename(file_path)} (ID: {file.get('id')})")

if __name__ == "__main__":
    # 오늘 날짜 폴더 경로 생성 (예: images/2026-04-07)
    today_folder = datetime.now().strftime("images/%Y-%m-%d")
    
    # 만약 오늘 폴더가 없으면, 가장 최근인 2026-04-06 폴더를 강제로 확인 (테스트용)
    if not os.path.exists(today_folder):
        today_folder = "images/2026-04-06"

    print(f"📂 {today_folder} 폴더에서 파일을 찾는 중...")

    if os.path.exists(today_folder):
        files = os.listdir(today_folder)
        image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not image_files:
            print("❌ 폴더에 이미지 파일이 없습니다.")
        
        for img in image_files:
            full_path = os.path.join(today_folder, img)
            upload_file(full_path)
    else:
        print(f"❌ {today_folder} 폴den가 존재하지 않습니다.")
