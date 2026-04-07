import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 1. GitHub Secret에서 인증 정보 가져오기
creds_json = os.environ.get('GDRIVE_CREDENTIALS')
folder_id = os.environ.get('GDRIVE_FOLDER_ID')

# 2. 구글 API 인증
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
    print(f"업로드 완료! 파일 ID: {file.get('id')}")

# 예시: 생성된 이미지 업로드 (파일명은 상황에 맞게 수정)
if __name__ == "__main__":
    # 여기에 이미지 생성 코드가 들어갈 자리입니다.
    # 테스트용으로 'tennis_sample.png'가 있다고 가정하고 호출합니다.
    if os.path.exists('tennis_sample.png'):
        upload_file('tennis_sample.png')
