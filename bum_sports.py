import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def main():
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
            print("🚀 [정밀 타격] 제목/본문 분리 작전 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(15)

            # 1. 도움말 제거
            try:
                await page.click(".se-help-panel-close-button, .help_close", timeout=5000)
                print("🛡️ 도움말 제거 성공")
            except: pass

            # 2. [중요] 초기 포커스 잡기
            # 화면 맨 위를 한번 클릭해서 포커스를 초기화합니다.
            await page.mouse.click(960, 10)
            await asyncio.sleep(1)

            # 3. 제목 작성 (Tab을 1~2번 눌러 제목 칸으로 진입)
            print("✍️ 제목 작성 중...")
            await page.keyboard.press("Tab")
            await asyncio.sleep(0.5)
            
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 스트링 머신 리포트"
            await page.keyboard.type(title, delay=50)

            # 4. 본문 작성 (Tab을 한 번 더 눌러 본문 칸으로 진입)
            print("✍️ 본문 작성 중...")
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            
            content = "사령관님, 제목과 본문을 완전히 분리하는 데 성공했습니다!\n이제 진짜 테니스 전문 블로그의 모습이 갖춰졌습니다."
            await page.keyboard.type(content, delay=30)
            print("✅ 분리 작성 완료")

            # 5. 발행
            print("📤 발행 및 확정 시도...")
            publish_btn = await page.wait_for_selector(".se-publish-button", timeout=10000)
            await publish_btn.click()
            await asyncio.sleep(2)
            
            confirm_btn = await page.wait_for_selector(".se-confirm-button", timeout=10000)
            await confirm_btn.click()
            
            print("🏁🏁🏁🏁🏁 [대성공] 이제 제목이 따로 들어갔을 겁니다!")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="error_screenshot.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
