# -*- coding: utf-8 -*-
"""
Daily Vaccine Image Collection
- Unsplash + Pixabay API로 백신/의료/건강 이미지 수집
- Google Drive 업로드 (GitHub Actions 실행용)
- 파일명에 카테고리 키워드 포함 → vaccine_agents_global.py 자동 인식
"""

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
PIXABAY_API_KEY     = os.environ.get("PIXABAY_API_KEY")
GDRIVE_CREDENTIALS  = os.environ.get("GDRIVE_CREDENTIALS")
VACCINE_FOLDER_NAME = "vaccine_images"  # 드라이브에 자동 생성되는 폴더명

TODAY   = date.today().strftime("%Y-%m-%d")
DAY_IDX = date.today().timetuple().tm_yday  # 매일 다른 이미지 선택용

UNSPLASH_URL = "https://api.unsplash.com/search/photos"
PIXABAY_URL  = "https://pixabay.com/api/"

# ──────────────────────────────────────────────
# 검색 키워드 설정
# 파일명 category → vaccine_agents_global.py IMAGE_CATEGORIES 키워드와 일치
# 백신: 백신/주사/접종 | 병원: 병원/의료/의사/간호 | 건강: 건강/예방/면역 | 어르신: 어르신/노인/고령
# ──────────────────────────────────────────────
SEARCH_QUERIES = [
    # 백신 카테고리
    {
        "query": "vaccine syringe injection medical",
        "category": "백신_주사",
        "label": "백신 주사",
    },
    {
        "query": "vaccination elderly senior person",
        "category": "백신_접종_어르신",
        "label": "어르신 접종",
    },
    {
        "query": "pneumonia vaccine doctor patient",
        "category": "백신_접종",
        "label": "폐렴 백신 접종",
    },
    {
        "query": "vaccine vial bottle medical laboratory",
        "category": "백신_의약품",
        "label": "백신 바이알",
    },

    # 병원/의료 카테고리
    {
        "query": "doctor patient consultation clinic",
        "category": "병원_의사",
        "label": "의사 상담",
    },
    {
        "query": "nurse vaccination healthcare worker",
        "category": "병원_간호",
        "label": "간호사 접종",
    },
    {
        "query": "hospital pharmacy medicine pills",
        "category": "병원_의료",
        "label": "병원 의료",
    },
    {
        "query": "medical clinic health center interior",
        "category": "병원_클리닉",
        "label": "의료 클리닉",
    },

    # 건강/예방 카테고리
    {
        "query": "healthy lifestyle disease prevention",
        "category": "건강_예방",
        "label": "건강 예방",
    },
    {
        "query": "immune system health wellness",
        "category": "건강_면역",
        "label": "면역 건강",
    },

    # 어르신 카테고리
    {
        "query": "senior elderly health checkup doctor",
        "category": "어르신_건강",
        "label": "어르신 건강검진",
    },
    {
        "query": "old person vaccination injection arm",
        "category": "어르신_노인",
        "label": "노인 백신 접종",
    },
    {
        "query": "senior couple healthy lifestyle active",
        "category": "어르신_고령",
        "label": "고령자 건강",
    },
]


def get_gdrive_service():
    if not GDRIVE_CREDENTIALS:
        raise ValueError("GDRIVE_CREDENTIALS 환경 변수가 없습니다.")
    token_dict = json.loads(GDRIVE_CREDENTIALS)
    creds = Credentials.from_authorized_user_info(token_dict)
    return build('drive', 'v3', credentials=creds)


def get_or_create_folder(service, folder_name: str) -> str:
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        folder_id = files[0]["id"]
        print(f"📁 기존 폴더 사용: {folder_name} ({folder_id[:8]}...)")
        return folder_id
    folder_meta = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    folder = service.files().create(body=folder_meta, fields="id").execute()
    folder_id = folder["id"]
    print(f"📁 새 폴더 생성: {folder_name} ({folder_id[:8]}...)")
    return folder_id


def upload_to_drive(service, file_path: str, filename: str, folder_id: str):
    file_metadata = {'name': filename, 'parents': [folder_id]}
    media = MediaFileUpload(file_path, resumable=True)
    try:
        service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        print(f"  ✅ 드라이브 업로드 성공: {filename}")
    except Exception as e:
        print(f"  ❌ 드라이브 업로드 실패: {e}")


def fetch_unsplash(query: str) -> bytes | None:
    try:
        res = requests.get(
            UNSPLASH_URL,
            params={"query": query, "per_page": 15, "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
            timeout=15
        )
        results = res.json().get("results", [])
        if not results:
            return None
        pick = results[DAY_IDX % len(results)]
        return requests.get(pick["urls"]["regular"], timeout=30).content
    except Exception as e:
        print(f"  ❌ Unsplash 오류: {e}")
        return None


def fetch_pixabay(query: str) -> bytes | None:
    try:
        res = requests.get(
            PIXABAY_URL,
            params={
                "key": PIXABAY_API_KEY,
                "q": query,
                "image_type": "photo",
                "orientation": "horizontal",
                "per_page": 15,
                "safesearch": "true",
            },
            timeout=15
        )
        results = res.json().get("hits", [])
        if not results:
            return None
        pick = results[DAY_IDX % len(results)]
        return requests.get(pick["largeImageURL"], timeout=30).content
    except Exception as e:
        print(f"  ❌ Pixabay 오류: {e}")
        return None


def main():
    if not all([UNSPLASH_ACCESS_KEY, PIXABAY_API_KEY, GDRIVE_CREDENTIALS]):
        print("❌ 설정 오류: GitHub Secrets를 확인하세요.")
        print("   필요한 Secrets: UNSPLASH_ACCESS_KEY, PIXABAY_API_KEY, GDRIVE_CREDENTIALS")
        return

    try:
        service = get_gdrive_service()
    except Exception as e:
        print(f"❌ 구글 인증 실패: {e}")
        return

    try:
        folder_id = get_or_create_folder(service, VACCINE_FOLDER_NAME)
    except Exception as e:
        print(f"❌ 폴더 생성 실패: {e}")
        return

    print(f"\n💉 Vaccine Blog 이미지 수집 시작: {TODAY}")
    print(f"총 {len(SEARCH_QUERIES)}개 카테고리 수집 예정\n")

    saved = 0

    for i, q in enumerate(SEARCH_QUERIES):
        print(f"[{i+1}/{len(SEARCH_QUERIES)}] {q['label']} 수집 중...")

        # Unsplash 수집
        img_data = fetch_unsplash(q["query"])
        if img_data:
            filename = f"{TODAY}_{i+1:02d}_{q['category']}_us.jpg"
            with open(filename, "wb") as f:
                f.write(img_data)
            upload_to_drive(service, filename, filename, folder_id)
            os.remove(filename)
            saved += 1

        # Pixabay 수집
        img_data = fetch_pixabay(q["query"])
        if img_data:
            filename = f"{TODAY}_{i+1:02d}_{q['category']}_pb.jpg"
            with open(filename, "wb") as f:
                f.write(img_data)
            upload_to_drive(service, filename, filename, folder_id)
            os.remove(filename)
            saved += 1

    print(f"\n✅ 수집 완료! 총 {saved}장 Google Drive 업로드")


if __name__ == "__main__":
    main()
