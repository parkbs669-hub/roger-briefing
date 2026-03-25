import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        aut_val = str(os.environ.get('NID_AUT') or "").strip()
        ses_val = str(os.environ.get('NID_SES') or "").strip()

        await context.add_cookies([
            {'name': 'NID_AUT', 'value': aut_val, 'domain': '.naver.com', 'path': '/'},
            {'name': 'NID_SES', 'value': ses_val, 'domain': '.naver.com', 'path': '/'}
        ])
        
        page = await context.new_page()

        try:
            print("🚀 [전략] 프레임리스 직접 침투 개시...")
            # 에디터 접속
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="domcontentloaded")
            
            print("🔍 화면 안정화 대기 (10초)...")
            await asyncio.sleep(10) 

            # 1. 도움말 X 버튼 제거 (프레임 없이 바로 찾기)
            try:
                print("🛡️ 도움말 창 제거 시도...")
                # 사진 우측 상단 X 버튼의 실제 경로 타겟팅
                close_btn = await page.wait_for_selector(".se-help-panel-close-button, .help_close, button[class*='close']", timeout=5000)
                await close_btn.click()
                print("✅ 도움말 창 제거 완료")
            except:
                print("⚠️ 도움말 창이 없거나 클릭할 수 없습니다. 계속 진행.")

            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 최종 승전보"
            content = "사령관님, 프레임 장벽과 도움말 팝업을 모두 뚫고 마침내 미션을 완수했습니다!"

            # 2. 제목 입력 (사진 속 '제목' 위치 직접 타격)
            print("✍️ 제목 작성 중...")
            title_input = await page.wait_for_selector(".se-title-input", timeout=15000)
            await title_input.click()
            await page.keyboard.type(title)
            await asyncio.sleep(1)

            # 3. 본문 입력
            print("✍️ 본문 작성 중...")
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=50)

            # 4. 발행 및 최종 확정
            print("📤 발행 버튼 타격...")
            # 발행 메뉴 버튼
            publish_menu = await page.wait_for_selector(".se-publish-button", timeout=10000)
            await publish_menu.click()
            await asyncio.sleep(2)

            # 진짜 발행 버튼
            confirm_btn = await page.wait_for_selector(".se-confirm-button", timeout=10000)
            await confirm_btn.click()
            
            print("🏁🏁🏁🏁🏁 [대성공] 사령관님, 이제 진짜 블로그를 확인하십시오!")
            await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="error_screenshot.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
