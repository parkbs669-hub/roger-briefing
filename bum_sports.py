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
            print("🚀 [최종 정밀 타격] 작전 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(15)

            # 도움말 제거
            try:
                close_btn = await page.wait_for_selector(".se-help-panel-close-button, .help_close", timeout=5000)
                await close_btn.click()
                print("🛡️ 도움말 제거 완료")
            except: pass

            # 제목/본문 작성
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 리포트"
            content = "사령관님, 수많은 시행착오 끝에 마침내 자동화 미션을 완수했습니다!\n테니스 스트링 텐션의 정밀함이 승리를 만듭니다."

            await page.mouse.click(960, 300)
            await asyncio.sleep(1)
            await page.keyboard.press("Tab")
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab")
            await page.keyboard.type(content, delay=30)
            print("✅ 내용 작성 완료")

            # 발행 시도 (좌표 정밀 수정: 1850)
            print("📤 발행 버튼 정밀 조준...")
            try:
                btn = await page.wait_for_selector(".se-publish-button", timeout=10000)
                await btn.click()
            except:
                print("⚠️ 버튼 못 찾음 -> 좌표(1850, 45) 강제 클릭")
                await page.mouse.click(1850, 45) 

            await asyncio.sleep(3)

            # 최종 확인 버튼 (엔터 대신 클릭 위주)
            print("📤 최종 발행 확정 시도...")
            try:
                confirm = await page.wait_for_selector(".se-confirm-button", timeout=10000)
                await confirm.click(force=True)
                print("✅ 최종 확인 완료")
            except:
                print("⚠️ 확인 버튼 못 찾음 -> 엔터 키 연타")
                await page.keyboard.press("Enter")
                await asyncio.sleep(1)
                await page.keyboard.press("Enter")

            await asyncio.sleep(5)
            print("🏁🏁🏁 작전 종료! (사진을 확인하세요)")

        except Exception as e:
            print(f"❌ 오류: {e}")
        finally:
            # 📸 [핵심 수정] 성공/실패 여부 상관없이 무조건 스크린샷 저장
            await page.screenshot(path="error_screenshot.png", full_page=True)
            print("📸 최종 화면 스크린샷 저장 완료 (error_screenshot.png)")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
