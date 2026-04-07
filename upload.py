import os
import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 1. GitHub Secrets에서 인증 정보(token.json 내용)와 폴더 ID 가져오기
token_json = os.environ.get('GDRIVE_CREDENTIALS')
folder_id = os.environ.get('GDRIVE_FOLDER_ID')

if not token_json or not folder_id:
    print("❌ 에러: GitHub Secrets가 설정되지 않았습니다.")
    exit(1)

# 2. 토큰 정보로 구글 API 인증 (로봇이 아닌 실제 사용자 인증 방식으로 변경)
token_dict = json.loads(token_json)
creds = Credentials.from_authorized_user_info(token_dict)
service = build('drive', 'v3', credentials=creds)

def upload_file(file_path):
    """파일을 구글 드라이브의 지정된 폴더로 업로드합니다."""
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id] 
    }
    
    # 내 계정의 용량을 그대로 사용하므로 용량 제한 에러가 발생하지 않습니다.
    media = MediaFileUpload(file_path, resumable=True)
    
    try:
        file = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id'
        ).execute()
        print(f"✅ 업로드 성공: {os.path.basename(file_path)}")
    except Exception as e:
        print(f"❌ 업로드 실패 ({os.path.basename(file_path)}): {e}")

if __name__ == "__main__":
    today_date = datetime.now().strftime("%Y-%m-%d")
    target_folder = f"images/{today_date}"
    
    # 오늘 폴더가 없으면 2026-04-06 폴더에서 테스트
    if not os.path.exists(target_folder):
        target_folder = "images/2026-04-06"

    print(f"📂 작업 경로: {target_folder}")

    if os.path.exists(target_folder):
        files = os.listdir(target_folder)
        image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not image_files:
            print("ℹ️ 해당 폴더에 업로드할 이미지 파일이 없습니다.")
        else:
            print(f"🚀 총 {len(image_files)}개의 파일 업로드를 시작합니다.")
            for img in image_files:
                full_path = os.path.join(target_folder, img)
                upload_file(full_path)
    else:
        print(f"❌ 에러: {target_folder} 폴더를 찾을 수 없습니다.")
