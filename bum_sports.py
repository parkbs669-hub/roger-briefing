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

        aut_val = str(os.environ.get('NID_AUT') or "").strip()
        ses_val = str(os.environ.get('NID_SES') or "").strip()
        await context.add_cookies([
            {'name': 'NID_AUT', 'value': aut_val, 'domain': '.naver.com', 'path': '/'},
            {'name': 'NID_SES', 'value': ses_val, 'domain': '.naver.com', 'path': '/'}
        ])

        page = await context.new_page()

        try:
            print("🚀 [최후의 굳히기] 발행 확정 작전 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(15)

            # 1. 도움말 제거 (이미 검증됨!)
            try:
                help_close = await page.wait_for_selector(".se-help-panel-close-button, .help_close", timeout=5000)
                await help_close.click()
                print("🛡️ 도움말 제거 완료")
            except: pass
            
            await asyncio.sleep(2)

            # 2. 내용 작성 (검증 완료된 로직)
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 최종 승전보"
            content = "사령관님, 도움말 장벽을 완전히 허물고 마침내 자동 포스팅 미션을 완수했습니다!\n테니스 스트링의 정밀함이 승리를 만듭니다."

            print("✍️ 리포트 작성 중...")
            await page.mouse.click(960, 300) 
            await asyncio.sleep(1)
            await page.keyboard.press("Tab")
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab")
            await page.keyboard.type(content, delay=30)
            print("✅ 내용 작성 완료")

            # 3. [보강] 발행 버튼 정밀 추적 (대기 시간 대폭 연장)
            print("📤 발행 버튼 포착 중 (30초 대기)...")
            try:
                # 사진에 보이는 초록색 발행 버튼을 찾습니다.
                publish_btn = await page.wait_for_selector(".se-publish-button, button[class*='publish']", state="visible", timeout=30000)
                await publish_btn.click(force=True)
                print("🔥 발행 메뉴 클릭 성공")
            except:
                print("⚠️ 버튼 탐색 지연 -> 좌표(1850, 45) 강제 정밀 타격")
                await page.mouse.click(1850, 45) 

            await asyncio.sleep(3)

            # 4. 최종 확인 버튼 (팝업 내 '발행' 버튼)
            print("📤 최종 발행 확정 시도...")
            try:
                confirm_btn = await page.wait_for_selector(".se-confirm-button, button[class*='confirm']", state="visible", timeout=15000)
                await confirm_btn.click(force=True)
                print("🏁🏁🏁 [미션 성공] 포스팅 완료!")
            except:
                print("⚠️ 확인 버튼 실패 -> 엔터 키 연타로 마무리")
                await page.keyboard.press("Enter")
                await asyncio.sleep(1)
                await page.keyboard.press("Enter")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        finally:
            # 성공하든 실패하든 증거는 남깁니다.
            await page.screenshot(path="error_screenshot.png", full_page=True)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
