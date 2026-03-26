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
            print("🚀 작전 개시...")
            await page.goto(
                f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}",
                wait_until="networkidle"
            )
            await asyncio.sleep(15)

            # 도움말 제거
            try:
                close_btn = await page.wait_for_selector(
                    ".se-help-panel-close-button, .help_close, button[class*='close']",
                    timeout=5000
                )
                await close_btn.click()
                print("🛡️ 도움말 제거 완료")
            except:
                pass

            # 제목/본문 작성
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 리포트"
            content = "사령관님, 자동 포스팅 시스템 가동 완료입니다!\n테니스 스트링 텐션의 정밀함이 승리를 만듭니다."

            await page.mouse.click(960, 300)
            await asyncio.sleep(1)
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=30)
            print("✅ 내용 작성 완료")

            # 발행 버튼 - 프레임 안팎 모두 시도
            print("📤 발행 시도...")
            published = False

            # 방법 1: 프레임 안에서 찾기
            frame = page.frame(name="mainFrame")
            if frame:
                try:
                    btn = await frame.wait_for_selector(".se-publish-button", timeout=10000)
                    await btn.click()
                    published = True
                    print("✅ 발행 버튼 (iframe)")
                except:
                    pass

            # 방법 2: 페이지 본체에서 찾기
            if not published:
                try:
                    btn = await page.wait_for_selector(".se-publish-button", timeout=10000)
                    await btn.click()
                    published = True
                    print("✅ 발행 버튼 (page)")
                except:
                    pass

            # 방법 3: 좌표 강제 클릭 (우측 상단 발행 버튼 위치)
            if not published:
                print("⚠️ 좌표 강제 클릭 시도...")
                await page.mouse.click(1820, 45)
                published = True

            await asyncio.sleep(3)

            # 최종 확인 버튼
            confirmed = False
            target = frame if frame else page
            try:
                confirm = await page.wait_for_selector(".se-confirm-button", timeout=10000)
                await confirm.click(force=True)
                confirmed = True
                print("✅ 최종 확인 완료")
            except:
                pass

            if not confirmed:
                try:
                    confirm = await page.wait_for_selector(
                        "button:has-text('확인'), button:has-text('발행')",
                        timeout=5000
                    )
                    await confirm.click(force=True)
                    confirmed = True
                except:
                    await page.keyboard.press("Enter")
                    print("⚠️ 엔터로 강제 발행")

            await asyncio.sleep(5)
            print("🏁🏁🏁 미션 완료!")

        except Exception as e:
            print(f"❌ 오류: {e}")
            await page.screenshot(path="error_screenshot.png", full_page=True)
            print("📸 스크린샷 저장됨")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
