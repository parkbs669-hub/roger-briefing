import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def get_tennis_trends(page):
    print("🔍 테니스 최신 이슈 수집 중...")
    search_url = "https://search.naver.com/search.naver?query=테니스+스트링+추천+후기+교체&nso=so:dd"
    await page.goto(search_url, wait_until="networkidle")
    await asyncio.sleep(3)
    items = await page.locator(".news_tit, .api_txt_lines.total_tit").all_inner_texts()
    unique_items = list(dict.fromkeys([item.strip() for item in items if len(item.strip()) > 5]))
    return "\n".join([f"📍 {i}" for i in unique_items[:5]])

async def post_blog():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        
        # 쿠키 주입
        aut_val = str(os.environ.get('NID_AUT') or "").strip()
        ses_val = str(os.environ.get('NID_SES') or "").strip()
        await context.add_cookies([
            {'name': 'NID_AUT', 'value': aut_val, 'domain': '.naver.com', 'path': '/'},
            {'name': 'NID_SES', 'value': ses_val, 'domain': '.naver.com', 'path': '/'}
        ])

        page = await context.new_page()

        try:
            trends = await get_tennis_trends(page)
            print(f"🚀 [범 스포츠] 리포트 작성 시작 (ID: {NAVER_ID})...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(15)

            # 🛡️ 방해물(도움말/팝업) 제거
            await page.evaluate("() => { document.querySelectorAll('.se-help-panel, .se-popup-guide').forEach(el => el.remove()); }")
            
            # 내용 입력
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 테니스 정밀 리포트"
            content = f"사령관님, 오늘 수집된 테니스 이슈입니다!\n\n{trends}\n\n텍스트 추적 시스템에 의한 자동 포스팅입니다."

            await page.mouse.click(960, 300)
            await page.keyboard.press("Tab")
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab")
            await page.keyboard.type(content, delay=30)
            print("✅ 데이터 입력 완료")

            # 🎯 [1단계] 첫 번째 '발행' 단어 찾아서 클릭
            print("📤 1단계: '발행' 버튼 탐색 및 클릭...")
            # '발행' 텍스트를 포함한 버튼이나 링크를 찾아 클릭합니다.
            publish_first = page.get_by_role("button", name="발행").first
            await publish_first.wait_for(state="visible", timeout=10000)
            await publish_first.click()
            print("🎯 1단계 '발행' 클릭 성공")
            
            await asyncio.sleep(5) # 팝업창 대기

            # 🎯 [2단계] 팝업창에서 다시 '발행' 단어 찾아서 클릭
            print("📤 2단계: 팝업창 내 '발행' 버튼 탐색 및 클릭...")
            # 팝업 내의 발행 버튼은 보통 '발행하기' 또는 '발행'입니다. 
            # 정규표현식을 써서 '발행'이 들어간 모든 버튼 중 가시적인 것을 타격합니다.
            publish_final = page.locator("button").filter(has_text="발행").last
            await publish_final.wait_for(state="visible", timeout=10000)
            await publish_final.click()
            print("🏁 최종 '발행' 클릭 성공! 작전 완수.")

            # 서버 전송 대기 및 결과 보고
            print("⏳ 서버 응답 대기 중 (20초)...")
            await asyncio.sleep(20)
            await page.screenshot(path="final_report.png", full_page=True)
            print("🏁🏁🏁 모든 과정 종료! 블로그를 확인하십시오.")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="final_report.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
