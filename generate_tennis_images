"""
Tennis Image Generator - DALL-E 3
매일 테니스 관련 이미지 10개 자동 생성
저장 위치: images/YYYY-MM-DD/
갤러리: gallery.html 자동 갱신
"""

import os
import json
import base64
import requests
from datetime import datetime, date
from pathlib import Path
from openai import OpenAI

# ── 설정 ──────────────────────────────────────────────
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
TODAY = date.today().strftime("%Y-%m-%d")
SAVE_DIR = Path(f"images/{TODAY}")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# ── 이미지 프롬프트 10개 (매일 동일 카테고리, 세부 내용은 날짜 seed로 변화) ──
import random
random.seed(int(datetime.now().strftime("%Y%m%d")))  # 날짜마다 다른 조합

PROMPT_POOLS = {
    "string_closeup": [
        "Extreme close-up of tennis string bed, silver polyester monofilament strings, shallow depth of field, studio lighting, product photography",
        "Macro shot of tennis racket strings, natural gut string texture, warm golden tones, bokeh background, professional photography",
        "Close-up of tennis string pattern, black polyester strings, geometric grid, high contrast, minimalist product photo",
        "Detailed shot of tennis strings being woven into racket frame, cross strings intersecting, vibrant colors, overhead view",
        "Tennis string close-up showing tension notching, white multifilament strings, water droplets, dramatic lighting",
    ],
    "player_action": [
        "Professional tennis player executing a powerful forehand drive, clay court, dramatic side lighting, motion blur on racket",
        "Female tennis player mid-serve at peak toss, Wimbledon grass court, white outfit, sunlight, dynamic action shot",
        "Tennis player sliding on clay court for a backhand, red clay dust, intense expression, wide angle perspective",
        "Tennis player at net for a volley, indoor hard court, stadium lights, spectators blurred in background",
        "Two tennis players in intense rally, baseline exchange, color contrast between players, bird's eye view",
    ],
    "court_scenery": [
        "Empty red clay tennis court at golden hour, long shadows, net in center, no people, peaceful atmosphere",
        "Wimbledon grass court aerial view, perfectly manicured green surface, white lines, morning dew",
        "Night tennis on blue hard court, stadium floodlights, dramatic shadows, empty court after match",
        "Roland Garros clay court panorama, terracotta red surface, ochre tones, French Open atmosphere",
        "Indoor tennis court with skylight, warm natural light streaming in, pristine surface, minimalist architecture",
    ],
    "stringing_machine": [
        "Professional tennis stringing machine with racket mounted, close-up of clamp holding string, workshop background",
        "Stringer hands working on racket, pulling polyester string through grommets, workbench setting, focused detail shot",
        "Tennis stringing machine turntable detail, drop weight tensioner, metallic finish, workshop atmosphere",
        "Collection of tennis strings in packages on workshop shelf, various colors and brands, organized display",
        "Racket clamped in stringing machine, freshly strung with red strings, professional workshop, top-down view",
    ],
    "racket_detail": [
        "Tennis racket head close-up on clay court surface, string grid reflection, red clay dust, dramatic angle",
        "Modern tennis racket leaning against net post, sunset backlight, silhouette effect, golden hour",
        "Multiple tennis rackets lined up, different brand colors, overhead flat lay, studio white background",
        "Tennis racket handle grip detail, black overgrip wrapping, worn texture, macro photography",
        "Tennis racket vibration dampener close-up, small silicone accessory between strings, colorful, detailed",
    ],
    "equipment_lifestyle": [
        "Tennis bag open showing rackets, strings, grips, and accessories organized inside, flat lay, clean aesthetic",
        "Tennis shoes on clay court, red dust on white soles, action blur, dynamic shot from low angle",
        "Can of tennis balls with racket on court, Wilson or Dunlop style, lifestyle photography, soft natural light",
        "Tennis player's bag on courtside bench, water bottle and towel, authentic match-day atmosphere",
        "Tennis wristband and grip tape on white background, minimalist product photography, soft shadows",
    ],
    "aesthetic_mood": [
        "Tennis court at dawn, morning mist, lone player silhouette, serene and atmospheric, wide landscape",
        "Rain on empty tennis court, puddles reflecting sky, melancholic mood, cinematic composition",
        "Vintage style tennis illustration, 1970s aesthetic, warm sepia tones, retro court scene",
        "Tennis net close-up with bokeh court background, minimalist composition, afternoon light",
        "Aerial view of tennis complex with multiple courts, green and blue surfaces, geometric pattern",
    ],
}

# 10개 프롬프트 선택 (카테고리별 균형)
DAILY_PROMPTS = [
    ("string_closeup",    random.choice(PROMPT_POOLS["string_closeup"])),
    ("string_closeup",    random.choice(PROMPT_POOLS["string_closeup"])),
    ("player_action",     random.choice(PROMPT_POOLS["player_action"])),
    ("player_action",     random.choice(PROMPT_POOLS["player_action"])),
    ("court_scenery",     random.choice(PROMPT_POOLS["court_scenery"])),
    ("court_scenery",     random.choice(PROMPT_POOLS["court_scenery"])),
    ("stringing_machine", random.choice(PROMPT_POOLS["stringing_machine"])),
    ("racket_detail",     random.choice(PROMPT_POOLS["racket_detail"])),
    ("equipment_lifestyle",random.choice(PROMPT_POOLS["equipment_lifestyle"])),
    ("aesthetic_mood",    random.choice(PROMPT_POOLS["aesthetic_mood"])),
]

CATEGORY_LABELS = {
    "string_closeup": "스트링 클로즈업",
    "player_action": "선수 액션",
    "court_scenery": "코트 풍경",
    "stringing_machine": "스트링 머신",
    "racket_detail": "라켓 디테일",
    "equipment_lifestyle": "장비 라이프스타일",
    "aesthetic_mood": "감성 테니스",
}

# ── 이미지 생성 ────────────────────────────────────────
def generate_image(prompt: str, index: int, category: str) -> dict:
    print(f"[{index+1}/10] 생성 중: {category} ...")
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        revised_prompt = response.data[0].revised_prompt

        # URL에서 이미지 다운로드
        img_data = requests.get(image_url, timeout=30).content
        filename = f"{index+1:02d}_{category}.png"
        filepath = SAVE_DIR / filename
        filepath.write_bytes(img_data)

        print(f"  ✅ 저장 완료: {filepath}")
        return {
            "index": index + 1,
            "category": category,
            "category_label": CATEGORY_LABELS.get(category, category),
            "filename": filename,
            "prompt": prompt,
            "revised_prompt": revised_prompt,
        }
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        return {
            "index": index + 1,
            "category": category,
            "category_label": CATEGORY_LABELS.get(category, category),
            "filename": None,
            "error": str(e),
        }

# ── 갤러리 HTML 생성 ──────────────────────────────────
def build_gallery_html(all_results: dict) -> str:
    """모든 날짜의 결과를 모아서 gallery.html 생성"""

    # 날짜 목록 (최신순)
    dates_sorted = sorted(all_results.keys(), reverse=True)

    date_tabs = ""
    date_sections = ""

    for i, d in enumerate(dates_sorted):
        active = "active" if i == 0 else ""
        date_tabs += f'<button class="tab-btn {active}" onclick="showDate(\'{d}\')" id="tab-{d}">{d}</button>\n'

        items = all_results[d]
        cards = ""
        for item in items:
            if item.get("filename"):
                img_path = f"images/{d}/{item['filename']}"
                prompt_text = item.get("prompt", "")[:120] + "..."
                cards += f"""
                <div class="card">
                    <div class="card-img-wrap">
                        <img src="{img_path}" alt="{item['category_label']}" loading="lazy">
                        <span class="badge">{item['category_label']}</span>
                    </div>
                    <div class="card-body">
                        <p class="prompt-text">{prompt_text}</p>
                        <a href="{img_path}" download class="dl-btn">⬇ 다운로드</a>
                    </div>
                </div>"""
            else:
                cards += f"""
                <div class="card error-card">
                    <div class="card-body">
                        <span class="badge badge-err">{item['category_label']}</span>
                        <p>생성 실패: {item.get('error','알 수 없는 오류')}</p>
                    </div>
                </div>"""

        display = "block" if i == 0 else "none"
        date_sections += f"""
        <div class="date-section" id="section-{d}" style="display:{display};">
            <div class="grid">{cards}</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🎾 Tennis Image Gallery</title>
<style>
  :root {{
    --bg: #0f1117;
    --surface: #1a1d2e;
    --card: #222538;
    --accent: #7cfc00;
    --accent2: #00e5ff;
    --text: #e8eaf6;
    --muted: #7986cb;
    --radius: 12px;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; min-height: 100vh; }}
  header {{ background: linear-gradient(135deg, #1a1d2e 0%, #0f1117 100%); padding: 32px 24px 20px; border-bottom: 2px solid var(--accent); }}
  header h1 {{ font-size: 1.8rem; color: var(--accent); letter-spacing: 2px; }}
  header p {{ color: var(--muted); margin-top: 4px; font-size: 0.9rem; }}
  .tab-bar {{ display: flex; flex-wrap: wrap; gap: 8px; padding: 20px 24px; background: var(--surface); border-bottom: 1px solid #2a2d3e; }}
  .tab-btn {{ background: var(--card); color: var(--muted); border: 1px solid #2a2d3e; border-radius: 20px; padding: 6px 16px; cursor: pointer; font-size: 0.85rem; transition: all 0.2s; }}
  .tab-btn:hover, .tab-btn.active {{ background: var(--accent); color: #000; border-color: var(--accent); font-weight: 600; }}
  .content {{ padding: 24px; max-width: 1400px; margin: 0 auto; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }}
  .card {{ background: var(--card); border-radius: var(--radius); overflow: hidden; border: 1px solid #2a2d3e; transition: transform 0.2s, box-shadow 0.2s; }}
  .card:hover {{ transform: translateY(-4px); box-shadow: 0 12px 32px rgba(124,252,0,0.15); }}
  .card-img-wrap {{ position: relative; aspect-ratio: 1; overflow: hidden; }}
  .card-img-wrap img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
  .badge {{ position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.75); color: var(--accent); font-size: 0.72rem; padding: 4px 10px; border-radius: 20px; border: 1px solid var(--accent); backdrop-filter: blur(4px); }}
  .badge-err {{ background: rgba(255,50,50,0.2); color: #ff6b6b; border-color: #ff6b6b; position: static; display: inline-block; margin-bottom: 8px; }}
  .card-body {{ padding: 14px; }}
  .prompt-text {{ font-size: 0.78rem; color: var(--muted); line-height: 1.5; margin-bottom: 10px; }}
  .dl-btn {{ display: inline-block; background: var(--accent); color: #000; font-size: 0.8rem; font-weight: 700; padding: 6px 14px; border-radius: 8px; text-decoration: none; transition: background 0.2s; }}
  .dl-btn:hover {{ background: var(--accent2); }}
  .error-card {{ padding: 20px; color: #ff6b6b; }}
  footer {{ text-align: center; padding: 24px; color: var(--muted); font-size: 0.8rem; border-top: 1px solid #2a2d3e; margin-top: 40px; }}
</style>
</head>
<body>
<header>
  <h1>🎾 Tennis Image Gallery</h1>
  <p>DALL-E 3 자동 생성 | 매일 10장 | BUM Sports</p>
</header>
<div class="tab-bar">
{date_tabs}
</div>
<div class="content">
{date_sections}
</div>
<footer>Generated by DALL-E 3 · roger-briefing pipeline · beomsports.tistory.com</footer>
<script>
  function showDate(d) {{
    document.querySelectorAll('.date-section').forEach(s => s.style.display = 'none');
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('section-' + d).style.display = 'block';
    document.getElementById('tab-' + d).classList.add('active');
  }}
</script>
</body>
</html>"""
    return html

# ── 메인 ─────────────────────────────────────────────
def main():
    print(f"\n🎾 Tennis Image Generator 시작: {TODAY}")
    print("=" * 50)

    # 이미지 생성
    results = []
    for i, (category, prompt) in enumerate(DAILY_PROMPTS):
        result = generate_image(prompt, i, category)
        results.append(result)

    # 오늘 결과 JSON 저장
    meta_path = SAVE_DIR / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n📋 메타데이터 저장: {meta_path}")

    # 전체 날짜 데이터 수집 (갤러리용)
    all_results = {}
    for date_dir in sorted(Path("images").iterdir(), reverse=True):
        if date_dir.is_dir():
            meta_file = date_dir / "meta.json"
            if meta_file.exists():
                with open(meta_file, "r", encoding="utf-8") as f:
                    all_results[date_dir.name] = json.load(f)

    # gallery.html 생성
    html = build_gallery_html(all_results)
    gallery_path = Path("gallery.html")
    gallery_path.write_text(html, encoding="utf-8")
    print(f"🖼️  갤러리 생성: {gallery_path}")

    success = sum(1 for r in results if r.get("filename"))
    print(f"\n✅ 완료: {success}/10개 생성 성공")
    print(f"📁 저장 폴더: images/{TODAY}/")
    print("🌐 갤러리: gallery.html (브라우저로 열기)")

if __name__ == "__main__":
    main()
