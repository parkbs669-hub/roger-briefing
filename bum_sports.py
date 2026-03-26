import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

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
            print("🚀 [최후의 일격] 문법 수정 및 최종 발행 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            
            # 에디터 로딩 대기
            await asyncio.sleep(15)

            # 1. 도움말 제거
            try:
                close_btn = await page.wait_for_selector(".se-help-panel-close-button, .help_close, button[class*='close']", timeout=5000)
                await close_btn.click()
                print("🛡️ 도움말 제거 완료")
            except: pass

            # 2. 제목 및 본문 작성 (이미 검증된 로직!)
            print("✍️ 제목 및 본문 작성 중...")
            await page.mouse.click(960, 300) 
            await asyncio.sleep(1)
            
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 정밀 리포트"
            content = "사령관님, 수많은 시행착오 끝에 마침내 자동화 미션을 완수했습니다!\n테니스 스트링 텐션의 정밀함이 승리를 만듭니다."

            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(title, delay=50)
            
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=30)
            print("✅ 내용 작성 성공")

            # 3. [수정] 발행 버튼 클릭 (Playwright 표준 문법 사용)
            print("📤 발행 및 확정 시도...")
            # '발행'이라는 텍스트를 가진 버튼을 직접 찾거나 클래스로 찾습니다.
            publish_btn = await page.wait_for_selector(".se-publish-button", state="visible", timeout=15000)
            await publish_btn.click()
            await asyncio.sleep(2)

            # 최종 확인 버튼 (팝업 내 '발행' 버튼)
            confirm_btn = await page.wait_for_selector(".se-confirm-button", state="visible", timeout=10000)
            await confirm_btn.click()
            
            print("🏁🏁🏁🏁🏁 [대성공] 이제 블로그에서 확인하십시오!")

        except Exception as e:
            print(f"❌ 오류: {e}")
            await page.screenshot(path="error_screenshot.png", full_page=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
