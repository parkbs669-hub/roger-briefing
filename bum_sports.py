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
            print("🚀 [최종 격파] 발행 버튼 무제한 추적 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            
            # 1. 넉넉한 대기 시간 (서버 지연 대응)
            await asyncio.sleep(20)

            # 2. 도움말 제거
            try:
                close_btn = await page.wait_for_selector(".se-help-panel-close-button, .help_close, button[class*='close']", timeout=5000)
                await close_btn.click()
                print("🛡️ 도움말 제거 완료")
            except: pass

            # 3. 제목 및 본문 작성 (이미 검증됨!)
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 최종 승전보"
            content = "사령관님, 마지막 관문인 발행 버튼까지 도달했습니다!\n이 글이 보인다면 자동화 전쟁의 완승입니다."

            await page.mouse.click(960, 300) 
            await asyncio.sleep(1)
            await page.keyboard.press("Tab")
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab")
            await page.keyboard.type(content, delay=30)
            print("✅ 내용 작성 성공")

            # 4. [보강] 발행 버튼 정밀 추적 (30초 대기)
            print("📤 발행 메뉴 탐색 (30초 인내)...")
            try:
                publish_btn = await page.wait_for_selector(".se-publish-button", state="visible", timeout=30000)
                await publish_btn.click(force=True)
                print("🔥 발행 메뉴 클릭 성공")
            except:
                print("⚠️ 버튼 탐색 실패, 우측 상단 좌표(1820, 45) 강제 타격!")
                await page.mouse.click(1820, 45) # 일반적인 발행 버튼 위치

            await asyncio.sleep(3)

            # 5. 최종 확인 버튼 (팝업 내 '발행' 버튼)
            print("📤 최종 발행 확정 시도...")
            try:
                confirm_btn = await page.wait_for_selector(".se-confirm-button", state="visible", timeout=15000)
                await confirm_btn.click(force=True)
                print("🏁🏁🏁 [대성공] 미션 완료!")
            except:
                print("⚠️ 최종 버튼 실패, 강제 엔터 발행 시도")
                await page.keyboard.press("Enter")
            
            await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ 오류: {e}")
            await page.screenshot(path="error_screenshot.png", full_page=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
