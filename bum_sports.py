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
            print("🚀 [최후 작전] 융합 침투 및 증거 확보 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            
            # 1. 에디터 로딩 대기 (충분히 20초)
            print("⏳ 에디터 로딩 대기 중...")
            await asyncio.sleep(20)

            # 2. 도움말 제거 (이름이 달라도 다 찾아냄)
            try:
                close_btn = await page.wait_for_selector(".se-help-panel-close-button, .help_close, button[class*='close']", timeout=5000)
                await close_btn.click()
                print("🛡️ 도움말 제거 완료")
            except: pass

            # 3. [핵심] Tab 키 전략으로 제목/본문 타격 (태그 이름 무시)
            print("✍️ 제목 및 본문 작성 중...")
            # 에디터 중앙을 찍어 포커스를 잡습니다.
            await page.mouse.click(960, 300) 
            await asyncio.sleep(1)
            
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 정밀 리포트"
            content = "사령관님, 수많은 시행착오 끝에 마침내 자동화 미션을 완수했습니다!\n테니스 스트링 텐션의 정밀함이 승리를 만듭니다."

            # 제목 입력
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(title, delay=50)
            
            # 본문 입력
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=30)
            print("✅ 내용 작성 완료")

            # 4. 발행 버튼 (여러 후보군 수색)
            print("📤 발행 및 확정 시도...")
            publish_btn = await page.wait_for_selector(".se-publish-button, button[class*='publish'], text='발행'", timeout=15000)
            await publish_btn.click()
            await asyncio.sleep(2)

            confirm_btn = await page.wait_for_selector(".se-confirm-button, button[class*='confirm']", timeout=10000)
            await confirm_btn.click()
            
            print("🏁🏁🏁🏁🏁 [대성공] 미션 완료!")

        except Exception as e:
            print(f"❌ 오류: {e}")
            # 💥 중요: 파일명을 깃허브 설정과 맞춤
            await page.screenshot(path="error_screenshot.png", full_page=True)
            print("📸 스크린샷 저장됨: error_screenshot.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
