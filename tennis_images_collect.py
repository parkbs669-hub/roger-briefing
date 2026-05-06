import os
import requests
from datetime import date
from pathlib import Path

UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")

TODAY = date.today().strftime("%Y-%m-%d")
UNSPLASH_URL = "https://api.unsplash.com/search/photos"
PIXABAY_URL = "https://pixabay.com/api/"

SEARCH_QUERIES = [
    {"query": "tennis woman", "category": "tennis_woman", "label": "테니스 여성"},
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
    {"query": "shaking hands after tennis match", "category": "sportsmanship", "label": "경기 후 악수"},
]

def main():
    if not UNSPLASH_ACCESS_KEY:
        print("❌ UNSPLASH_ACCESS_KEY 없음")
        return
    if not PIXABAY_API_KEY:
        print("⚠️ PIXABAY_API_KEY 없음 - Unsplash만 사용합니다.")

    save_dir = Path(f"images/{TODAY}")
    save_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🎾 BUM Sports 이미지 수집 시작: {TODAY}")
    day_idx = date.today().timetuple().tm_yday
    saved = 0

    for i, q in enumerate(SEARCH_QUERIES):
        print(f"[{i+1}/{len(SEARCH_QUERIES)}] {q['label']} 처리 중...")

        # 1. Unsplash
        try:
            res = requests.get(
                UNSPLASH_URL,
                params={"query": q["query"], "per_page": 10, "orientation": "landscape"},
                headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
                timeout=15,
            )
            results = res.json().get("results", [])
            if results:
                pick = results[day_idx % len(results)]
                img_data = requests.get(pick["urls"]["regular"], timeout=30).content
                path = save_dir / f"{i+1:02d}_{q['category']}_us.jpg"
                path.write_bytes(img_data)
                print(f"  ✅ 저장: {path}")
                saved += 1
        except Exception as e:
            print(f"  ❌ Unsplash 오류: {e}")

        # 2. Pixabay
        if PIXABAY_API_KEY:
            try:
                res = requests.get(
                    PIXABAY_URL,
                    params={
                        "key": PIXABAY_API_KEY,
                        "q": q["query"],
                        "image_type": "photo",
                        "orientation": "horizontal",
                        "per_page": 10,
                    },
                    timeout=15,
                )
                results = res.json().get("hits", [])
                if results:
                    pick = results[day_idx % len(results)]
                    img_data = requests.get(pick["largeImageURL"], timeout=30).content
                    path = save_dir / f"{i+1:02d}_{q['category']}_pb.jpg"
                    path.write_bytes(img_data)
                    print(f"  ✅ 저장: {path}")
                    saved += 1
            except Exception as e:
                print(f"  ❌ Pixabay 오류: {e}")

    print(f"\n🎾 완료! 총 {saved}개 이미지 저장 → images/{TODAY}/")

if __name__ == "__main__":
    main()
