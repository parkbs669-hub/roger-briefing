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
            print("🚀 [진격] 도움말 장벽 제거 및 최종 발행 작전...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(15)

            # 1. [필살] 도움말 창 제거 (사진상의 X 버튼 위치 타격)
            print("🛡️ 도움말 제거 시도 중...")
            try:
                # 클래스로 찾기 시도
                help_close = await page.wait_for_selector(".se-help-panel-close-button, .help_close", timeout=5000)
                await help_close.click()
                print("✅ 도움말 클래스로 제거 성공")
            except:
                # 안되면 사진상 X버튼 위치(우측 상단 끝) 강제 클릭
                print("⚠️ 클래스 실패, 좌표(1885, 35)로 도움말 강제 종료")
                await page.mouse.click(1885, 35)
            
            await asyncio.sleep(2)

            # 2. 내용 작성 (도움말이 사라졌으니 이제 Tab이 제대로 먹힙니다)
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 정밀 리포트"
            content = "사령관님, 도움말 장벽을 허물고 마침내 자동 포스팅에 성공했습니다!\n테니스 스트링 텐션의 정밀함이 승리를 만듭니다."

            print("✍️ 제목 및 본문 작성 중...")
            # 에디터 본체 클릭하여 포커스 잡기
            await page.mouse.click(960, 300) 
            await asyncio.sleep(1)
            await page.keyboard.press("Tab") # 제목 칸 진입
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab") # 본문 칸 진입
            await page.keyboard.type(content, delay=30)
            print("✅ 내용 작성 완료")

            # 3. 발행 버튼 클릭 (이제 가려진 게 없으니 잘 보입니다)
            print("📤 발행 버튼 조준...")
            publish_btn = await page.wait_for_selector(".se-publish-button", state="visible", timeout=10000)
            await publish_btn.click()
            await asyncio.sleep(3)

            # 4. 최종 확인 버튼
            print("📤 최종 발행 확정...")
            confirm_btn = await page.wait_for_selector(".se-confirm-button", state="visible", timeout=10000)
            await confirm_btn.click()
            
            print("🏁🏁🏁 [임무 완수] 이제 진짜 블로그를 확인하세요!")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        finally:
            await page.screenshot(path="error_screenshot.png", full_page=True)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
