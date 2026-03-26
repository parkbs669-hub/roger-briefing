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
            print("🚀 [최후의 일격] 도움말 제거 및 발행 확정 작전...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(15)

            # 1. [핵심] 도움말 창 강제 종료 (사진상의 X 위치 타격)
            print("🛡️ 도움말 제거 시도 중...")
            try:
                # 클래스로 찾기 시도
                help_close = await page.wait_for_selector(".se-help-panel-close-button, .help_close", timeout=5000)
                await help_close.click()
            except:
                # 안되면 좌표(1885, 35)로 강제 클릭
                await page.mouse.click(1885, 35)
            await asyncio.sleep(2)

            # 2. 내용 작성 (검증된 로직)
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 자동화 리포트"
            content = "사령관님, 도움말 장벽을 허물고 마침내 자동 포스팅 미션을 완수했습니다!\n테니스 스트링 텐션의 정밀함이 승리를 만듭니다."

            print("✍️ 리포트 작성 중...")
            await page.mouse.click(960, 300) 
            await asyncio.sleep(1)
            await page.keyboard.press("Tab")
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab")
            await page.keyboard.type(content, delay=30)
            print("✅ 내용 작성 완료")

            # 3. 발행 메뉴 열기
            print("📤 발행 메뉴 진입...")
            publish_btn = await page.wait_for_selector(".se-publish-button", state="visible", timeout=15000)
            await publish_btn.click(force=True)
            await asyncio.sleep(3)

            # 4. 최종 발행 확정 (강제 클릭 및 엔터 연타)
            print("📤 최종 발행 확정 시도...")
            try:
                confirm_btn = await page.wait_for_selector(".se-confirm-button", state="visible", timeout=10000)
                await confirm_btn.click(force=True)
                print("🏁🏁🏁 [미션 성공] 포스팅 완료!")
            except:
                print("⚠️ 확인 버튼 실패 -> 엔터 키 3회 연타")
                for _ in range(3):
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        finally:
            # 성공 여부 확인용 스크린샷 저장
            await page.screenshot(path="error_screenshot.png", full_page=True)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
