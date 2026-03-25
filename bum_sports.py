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
            print("🚀 [최종 작전] 도움말 창 제거 및 정밀 타격 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            
            # 1. 프레임 진입 대기
            await page.wait_for_selector("#mainFrame", timeout=30000)
            frame = page.frame(name="mainFrame")
            print("✅ 에디터 프레임 접속")

            # 2. [중요] 도움말 창 닫기 (사진 우측 상단의 X 버튼 타격)
            try:
                print("🛡️ 도움말 창 제거 시도...")
                # 여러 방식의 X 버튼 셀렉터를 시도합니다.
                close_btn = await frame.wait_for_selector("button.help_close, .se-help-close-button", timeout=5000)
                await close_btn.click()
                print("✅ 도움말 창 제거 완료")
            except:
                print("⚠️ 도움말 창이 없거나 이미 닫혀 있습니다. 계속 진행합니다.")

            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 완벽 성공 리포트"
            content = "사령관님, 도움말 장벽을 뚫고 마침내 자동 포스팅에 성공했습니다!"

            # 3. 제목 입력 (강제 클릭 후 입력)
            print("✍️ 제목 작성 중...")
            await frame.click(".se-title-input")
            await page.keyboard.type(title)
            await asyncio.sleep(1)

            # 4. 본문 입력
            print("✍️ 본문 작성 중...")
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=50)

            # 5. 발행 (강제 연타 모드)
            print("📤 발행 버튼 정밀 타격...")
            publish_btn = await frame.wait_for_selector(".se-publish-button")
            await publish_btn.click()
            await asyncio.sleep(2)

            confirm_btn = await frame.wait_for_selector(".se-confirm-button")
            await confirm_btn.click()
            
            print("🏁🏁🏁🏁🏁 [대성공] 이제 진짜 블로그 맨 위를 확인하세요!")
            await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="error_screenshot.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
