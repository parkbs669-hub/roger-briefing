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

        # 쿠키 주입 (Secrets 설정 확인 필요)
        aut_val = str(os.environ.get('NID_AUT') or "").strip()
        ses_val = str(os.environ.get('NID_SES') or "").strip()
        await context.add_cookies([
            {'name': 'NID_AUT', 'value': aut_val, 'domain': '.naver.com', 'path': '/'},
            {'name': 'NID_SES', 'value': ses_val, 'domain': '.naver.com', 'path': '/'}
        ])

        page = await context.new_page()

        try:
            print("🚀 [범 스포츠] 1안 정식 리포트 발행 작전 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(15)

            # 1. 도움말 제거 (검증된 로직)
            try:
                close_btn = await page.wait_for_selector(".se-help-panel-close-button, .help_close, button[class*='close']", timeout=5000)
                await close_btn.click()
                print("🛡️ 도움말 제거 완료")
            except: 
                await page.mouse.click(1885, 35) # 좌표로 강제 클릭
            
            await asyncio.sleep(2)

            # 2. [1안] 내용 작성
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 스트링 교체 주기의 '골든 타임'은?"
            content = (
                "사령관님, 테니스 승리의 핵심은 장비의 일관성입니다!\n\n"
                "많은 분이 스트링이 끊어질 때까지 사용하시지만, 실제 스트링의 탄성은 "
                "작업 직후부터 서서히 감소하기 시작합니다.\n\n"
                "탄성을 잃은 스트링은 컨트롤력을 떨어뜨리고 팔꿈치 부상(엘보)의 원인이 되기도 합니다. "
                "끊어지지 않더라도 3개월이 지났다면, 승리를 위해 새로운 텐션으로 교체하는 '골든 타임'을 놓치지 마세요!\n\n"
                "오늘도 범 스포츠와 함께 활기찬 테니스 생활 되시길 바랍니다."
            )

            print("✍️ 리포트 작성 중...")
            await page.mouse.click(960, 300) 
            await asyncio.sleep(1)
            await page.keyboard.press("Tab") # 제목 칸 진입
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab") # 본문 칸 진입
            await page.keyboard.type(content, delay=30)
            print("✅ 내용 작성 완료")

            # 3. 발행 버튼 클릭
            print("📤 발행 메뉴 진입...")
            try:
                publish_btn = await page.wait_for_selector(".se-publish-button", state="visible", timeout=15000)
                await publish_btn.click(force=True)
            except:
                await page.mouse.click(1850, 45) # 좌표 정밀 타격

            await asyncio.sleep(3)

            # 4. 최종 발행 확정
            print("📤 최종 발행 확정 시도...")
            try:
                confirm_btn = await page.wait_for_selector(".se-confirm-button", state="visible", timeout=10000)
                await confirm_btn.click(force=True)
                print("🏁🏁🏁 [미션 성공] 1안 리포트 포스팅 완료!")
            except:
                for _ in range(3):
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(1)
            
            await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        finally:
            # 결과 확인용 스크린샷 저장
            await page.screenshot(path="error_screenshot.png", full_page=True)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
