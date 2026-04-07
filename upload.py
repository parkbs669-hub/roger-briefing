import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 1. GitHub Secrets에서 인증 정보와 폴더 ID 가져오기
creds_json = os.environ.get('GDRIVE_CREDENTIALS')
folder_id = os.environ.get('GDRIVE_FOLDER_ID')

if not creds_json or not folder_id:
    print("❌ 에러: GitHub Secrets(GDRIVE_CREDENTIALS 또는 GDRIVE_FOLDER_ID)가 설정되지 않았습니다.")
    exit(1)

# 2. 구글 API 인증 설정
creds_dict = json.loads(creds_json)
creds = service_account.Credentials.from_service_account_info(creds_dict)
service = build('drive', 'v3', credentials=creds)

def upload_file(file_path):
    """파일을 구글 드라이브의 지정된 폴더로 업로드합니다."""
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id] # 2단계에서 만든 폴더 ID로 전송
    }
    
    # 서비스 계정의 용량 제한 에러를 피하기 위해 resumable=False 설정
    media = MediaFileUpload(file_path, resumable=False)
    
    try:
        file = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id'
        ).execute()
        print(f"✅ 업로드 성공: {os.path.basename(file_path)} (ID: {file.get('id')})")
    except Exception as e:
        print(f"❌ 업로드 실패 ({os.path.basename(file_path)}): {e}")

if __name__ == "__main__":
    # 오늘 날짜 폴더 확인 (예: images/2026-04-07)
    today_date = datetime.now().strftime("%Y-%m-%d")
    target_folder = f"images/{today_date}"
    
    # 만약 오늘 날짜 폴더가 없다면, 테스트를 위해 2026-04-06 폴더를 확인
    if not os.path.exists(target_folder):
        print(f"💡 오늘 폴더({target_folder})가 없어 이전 날짜(images/2026-04-06)를 확인합니다.")
        target_folder = "images/2026-04-06"

    print(f"📂 작업 경로: {target_folder}")

    if os.path.exists(target_folder):
        # 폴더 내 모든 파일 리스트업
        files = os.listdir(target_folder)
        # 이미지 파일만 필터링 (.png, .jpg, .jpeg)
        image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not image_files:
            print("ℹ️ 해당 폴더에 업로드할 이미지 파일이 없습니다.")
        else:
            print(f"🚀 총 {len(image_files)}개의 파일을 업로드를 시작합니다.")
            for img in image_files:
                full_path = os.path.join(target_folder, img)
                upload_file(full_path)
    else:
        print(f"❌ 에러: {target_folder} 폴더를 찾을 수 없습니다. 경로를 확인해주세요.")
