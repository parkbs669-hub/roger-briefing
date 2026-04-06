"""
Tennis Image Collector - Unsplash API
매일 테니스 관련 실제 사진 10장 자동 수집
저장 위치: images/YYYY-MM-DD/
갤러리: gallery.html 자동 갱신
"""

import os
import json
import requests
from datetime import date
from pathlib import Path

# ── 설정 ──────────────────────────────────────────────
UNSPLASH_ACCESS_KEY = os.environ["UNSPLASH_ACCESS_KEY"]
TODAY = date.today().strftime("%Y-%m-%d")
SAVE_DIR = Path(f"images/{TODAY}")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.unsplash.com/search/photos"

# ── 검색 키워드 10개 (카테고리별) ──────────────────────
SEARCH_QUERIES = [
    {"query": "tennis string racket closeup",  "category": "string_closeup",    "label": "스트링 클로즈업"},
    {"query": "tennis racket strings detail",  "category": "string_detail",     "label": "스트링 디테일"},
    {"query": "tennis player forehand action", "category": "player_forehand",   "label": "선수 포핸드"},
    {"query": "tennis player serve action",    "category": "player_serve",      "label": "선수 서브"},
    {"query": "tennis player backhand",        "category": "player_backhand",   "label": "선수 백핸드"},
    {"query": "clay court tennis",             "category": "clay_court",        "label": "클레이 코트"},
    {"query": "tennis court aerial view",      "category": "court_aerial",      "label": "코트 전경"},
    {"query": "tennis stringing machine",      "category": "stringing_machine", "label": "스트링 머신"},
    {"query": "tennis ball court net",         "category": "tennis_net",        "label": "네트 & 공"},
    {"query": "tennis equipment bag racket",   "category": "equipment",         "label": "테니스 장비"},
]

# ── 이미지 검색 및 다운로드 ────────────────────────────
def fetch_image(query_info: dict, index: int) -> dict:
    query    = query_info["query"]
    category = query_info["category"]
    label    = query_info["label"]

    print(f"[{index+1}/10] 검색 중: {label} ({query})")

    try:
        params = {
            "query":          query,
            "per_page":       5,
            "orientation":    "landscape",
            "content_filter": "high",
        }
        headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
        res = requests.get(BASE_URL, params=params, headers=headers, timeout=15)
        res.raise_for_status()
        data = res.json()

        results = data.get("results", [])
        if not results:
            raise ValueError("검색 결과 없음")

        # 날짜 기반으로 매일 다른 이미지 선택
        day_of_year = date.today().timetuple().tm_yday
        pick = results[day_of_year % len(results)]

        img_url      = pick["urls"]["regular"]
        photographer = pick["user"]["name"]
        unsplash_url = pick["links"]["html"]
        description  = pick.get("description") or pick.get("alt_description") or query

        # Unsplash 정책: download 트리거 필요
        dl_url = pick["links"]["download_location"]
        requests.get(dl_url, headers=headers, timeout=10)

        img_data = requests.get(img_url, timeout=30).content
        filename = f"{index+1:02d}_{category}.jpg"
        filepath = SAVE_DIR / filename
        filepath.write_bytes(img_data)

        print(f"  ✅ 저장: {filename} | 📸 {photographer}")

        return {
            "index":        index + 1,
            "category":     category,
            "label":        label,
            "filename":     filename,
            "description":  description[:100],
            "photographer": photographer,
            "unsplash_url": unsplash_url,
            "query":        query,
        }

    except Exception as e:
        print(f"  ❌ 실패: {e}")
        return {
            "index":    index + 1,
            "category": category,
            "label":    label,
            "filename": None,
            "error":    str(e),
        }


# ── gallery.html 생성 ──────────────────────────────────
def build_gallery_html(all_results: dict) -> str:
    dates_sorted  = sorted(all_results.keys(), reverse=True)
    date_tabs     = ""
    date_sections = ""

    for i, d in enumerate(dates_sorted):
        active = "active" if i == 0 else ""
        date_tabs += f'<button class="tab-btn {active}" onclick="showDate(\'{d}\')" id="tab-{d}">{d}</button>\n'

        items = all_results[d]
        cards = ""
        for item in items:
            if item.get("filename"):
                img_path     = f"images/{d}/{item['filename']}"
                photographer = item.get("photographer", "")
                unsplash_url = item.get("unsplash_url", "#")
                desc         = item.get("description", "")
                cards += f"""
                <div class="card">
                    <div class="card-img-wrap">
                        <img src="{img_path}" alt="{item['label']}" loading="lazy">
                        <span class="badge">{item['label']}</span>
                    </div>
                    <div class="card-body">
                        <p class="desc-text">{desc}</p>
                        <p class="photo-credit">📸 <a href="{unsplash_url}" target="_blank">{photographer} / Unsplash</a></p>
                        <a href="{img_path}" download class="dl-btn">⬇ 다운로드</a>
                    </div>
                </div>"""
            else:
                cards += f"""
                <div class="card error-card">
                    <div class="card-body">
                        <span class="badge badge-err">{item['label']}</span>
                        <p>수집 실패: {item.get('error','알 수 없는 오류')}</p>
                    </div>
                </div>"""

        display = "block" if i == 0 else "none"
        date_sections += f"""
        <div class="date-section" id="section-{d}" style="display:{display};">
            <div class="grid">{cards}</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🎾 Tennis Image Gallery</title>
<style>
  :root{{--bg:#0f1117;--surface:#1a1d2e;--card:#222538;--accent:#7cfc00;--accent2:#00e5ff;--text:#e8eaf6;--muted:#7986cb;--radius:12px}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--text);font-family:'Segoe UI',sans-serif;min-height:100vh}}
  header{{background:linear-gradient(135deg,#1a1d2e,#0f1117);padding:32px 24px 20px;border-bottom:2px solid var(--accent)}}
  header h1{{font-size:1.8rem;color:var(--accent);letter-spacing:2px}}
  header p{{color:var(--muted);margin-top:4px;font-size:.9rem}}
  .tab-bar{{display:flex;flex-wrap:wrap;gap:8px;padding:20px 24px;background:var(--surface);border-bottom:1px solid #2a2d3e}}
  .tab-btn{{background:var(--card);color:var(--muted);border:1px solid #2a2d3e;border-radius:20px;padding:6px 16px;cursor:pointer;font-size:.85rem;transition:all .2s}}
  .tab-btn:hover,.tab-btn.active{{background:var(--accent);color:#000;border-color:var(--accent);font-weight:600}}
  .content{{padding:24px;max-width:1400px;margin:0 auto}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px}}
  .card{{background:var(--card);border-radius:var(--radius);overflow:hidden;border:1px solid #2a2d3e;transition:transform .2s,box-shadow .2s}}
  .card:hover{{transform:translateY(-4px);box-shadow:0 12px 32px rgba(124,252,0,.15)}}
  .card-img-wrap{{position:relative;aspect-ratio:16/10;overflow:hidden}}
  .card-img-wrap img{{width:100%;height:100%;object-fit:cover;display:block}}
  .badge{{position:absolute;top:10px;left:10px;background:rgba(0,0,0,.75);color:var(--accent);font-size:.72rem;padding:4px 10px;border-radius:20px;border:1px solid var(--accent);backdrop-filter:blur(4px)}}
  .badge-err{{background:rgba(255,50,50,.2);color:#ff6b6b;border-color:#ff6b6b;position:static;display:inline-block;margin-bottom:8px}}
  .card-body{{padding:14px}}
  .desc-text{{font-size:.78rem;color:var(--muted);line-height:1.5;margin-bottom:6px}}
  .photo-credit{{font-size:.72rem;color:#546e7a;margin-bottom:10px}}
  .photo-credit a{{color:#546e7a;text-decoration:none}}
  .photo-credit a:hover{{color:var(--accent2)}}
  .dl-btn{{display:inline-block;background:var(--accent);color:#000;font-size:.8rem;font-weight:700;padding:6px 14px;border-radius:8px;text-decoration:none;transition:background .2s}}
  .dl-btn:hover{{background:var(--accent2)}}
  .error-card{{padding:20px;color:#ff6b6b}}
  footer{{text-align:center;padding:24px;color:var(--muted);font-size:.8rem;border-top:1px solid #2a2d3e;margin-top:40px}}
</style>
</head>
<body>
<header>
  <h1>🎾 Tennis Image Gallery</h1>
  <p>Unsplash 실제 사진 자동 수집 | 매일 10장 | BUM Sports</p>
</header>
<div class="tab-bar">
{date_tabs}
</div>
<div class="content">
{date_sections}
</div>
<footer>Photos from Unsplash · roger-briefing pipeline · beomsports.tistory.com</footer>
<script>
  function showDate(d){{
    document.querySelectorAll('.date-section').forEach(s=>s.style.display='none');
    document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
    document.getElementById('section-'+d).style.display='block';
    document.getElementById('tab-'+d).classList.add('active');
  }}
</script>
</body>
</html>"""


# ── 메인 ─────────────────────────────────────────────
def main():
    print(f"\n🎾 Tennis Image Collector 시작: {TODAY}")
    print("=" * 50)

    results = []
    for i, query_info in enumerate(SEARCH_QUERIES):
        result = fetch_image(query_info, i)
        results.append(result)

    # 오늘 결과 JSON 저장
    meta_path = SAVE_DIR / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n📋 메타데이터 저장: {meta_path}")

    # 전체 날짜 갤러리 데이터 수집
    all_results = {}
    for date_dir in sorted(Path("images").iterdir(), reverse=True):
        if date_dir.is_dir():
            meta_file = date_dir / "meta.json"
            if meta_file.exists():
                with open(meta_file, "r", encoding="utf-8") as f:
                    all_results[date_dir.name] = json.load(f)

    # gallery.html 생성
    html = build_gallery_html(all_results)
    Path("gallery.html").write_text(html, encoding="utf-8")

    success = sum(1 for r in results if r.get("filename"))
    print(f"\n✅ 완료: {success}/10장 수집 성공")
    print(f"📁 저장: images/{TODAY}/")
    print("🌐 갤러리: gallery.html")


if __name__ == "__main__":
    main()
