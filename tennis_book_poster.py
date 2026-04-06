import os
import json
import time
import requests
from datetime import datetime
from openai import OpenAI
from selenium import webdriver
# ... (필요한 라이브러리 import 생략 없이 유지)

# [설정 및 환경변수 부분 기존과 동일]
SEEN_FILE = "data/tennis_books_seen.json"

def load_seen():
    os.makedirs("data", exist_ok=True)
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except: return set()
    return set()

def save_seen(seen: set):
    os.makedirs("data", exist_ok=True)
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False, indent=2)

# ... [fetch_aladin_books, fetch_nl_books 등 수집 함수 기존과 동일] ...

def main():
    print(f"[시작] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    seen = load_seen()

    # 데이터 수집 실행
    domestic = fetch_aladin_books(seen)
    overseas = fetch_google_books(seen)
    # (국립중앙도서관 보완 로직 포함)
    
    # ---------------------------------------------------------
    # 사고 모델 1단계: 수집 결과와 무관하게 파일 존재 보장
    # ---------------------------------------------------------
    save_seen(seen) 

    if not domestic and not overseas:
        print("[종료] 새로운 도서 없음")
        return # 여기서 종료되어도 위에서 save_seen을 했으므로 파일은 존재함
    # ---------------------------------------------------------

    # 블로그 포스팅 로직
    try:
        title, html = build_post_html(domestic, overseas)
        post_to_tistory(title, html)
        
        # 포스팅 성공 시 ISBN 업데이트 후 최종 저장
        for b in domestic + overseas:
            seen.add(b["isbn"])
        save_seen(seen)
        print("[완료] 포스팅 및 기록 업데이트 성공")
    except Exception as e:
        print(f"[오류] 과정 중 문제 발생: {e}")

if __name__ == "__main__":
    main()
