import os
import requests
from datetime import date
from pathlib import Path

UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

TODAY = date.today().strftime("%Y-%m-%d")
UNSPLASH_URL = "https://api.unsplash.com/search/photos"
PIXABAY_URL = "https://pixabay.com/api/"
PEXELS_URL = "https://api.pexels.com/v1/search"

SEARCH_QUERIES = [
    {"query": "tennis woman", "category": "tennis_woman_01", "label": "테니스 여성1"},
    {"query": "female tennis player", "category": "tennis_woman_02", "label": "테니스 여성2"},
    {"query": "women tennis match", "category": "tennis_woman_03", "label": "테니스 여성3"},
    {"query": "tennis girl action", "category": "tennis_woman_04", "label": "테니스 여성4"},
    {"query": "women tennis serve", "category": "tennis_woman_05", "label": "테니스 여성 서브"},
    {"query": "female tennis forehand", "category": "tennis_woman_06", "label": "테니스 여성 포핸드"},
    {"query": "women tennis fashion", "category": "tennis_woman_07", "label": "테니스 여성 패션"},
    {"query": "female tennis court", "category": "tennis_woman_08", "label": "테니스 여성 코트"},
]

def main():
    if not UNSPLASH_ACCESS_KEY:
        print("❌ UNSPLASH_ACCESS_KEY 없음")
        return
    if not PIXABAY_API_KEY:
        print("⚠️ PIXABAY_API_KEY 없음 - 건너뜁니다.")
    if not PEXELS_API_KEY:
        print("⚠️ PEXELS_API_KEY 없음 - 건너뜁니다.")

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
                    img_data = requests.get(pick["webformatURL"], timeout=30).content
                    path = save_dir / f"{i+1:02d}_{q['category']}_pb.jpg"
                    path.write_bytes(img_data)
                    print(f"  ✅ 저장: {path}")
                    saved += 1
            except Exception as e:
                print(f"  ❌ Pixabay 오류: {e}")

        # 3. Pexels
        if PEXELS_API_KEY:
            try:
                res = requests.get(
                    PEXELS_URL,
                    params={"query": q["query"], "per_page": 10, "orientation": "landscape"},
                    headers={"Authorization": PEXELS_API_KEY},
                    timeout=15,
                )
                results = res.json().get("photos", [])
                if results:
                    pick = results[day_idx % len(results)]
                    img_data = requests.get(pick["src"]["large"], timeout=30).content
                    path = save_dir / f"{i+1:02d}_{q['category']}_px.jpg"
                    path.write_bytes(img_data)
                    print(f"  ✅ 저장: {path}")
                    saved += 1
            except Exception as e:
                print(f"  ❌ Pexels 오류: {e}")

    print(f"\n🎾 완료! 총 {saved}개 이미지 저장 → images/{TODAY}/")

if __name__ == "__main__":
    main()
