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
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="ko-KR"
        )

        # 쿠키 주입
        aut_val = str(os.environ.get('NID_AUT') or "").strip()
        ses_val = str(os.environ.get('NID_SES') or "").strip()

        await context.add_cookies([
            {'name': 'NID_AUT', 'value': aut_val, 'domain': '.naver.com', 'path': '/'},
            {'name': 'NID_SES', 'value': ses_val, 'domain': '.naver.com', 'path': '/'}
        ])
        
        page = await context.new_page()

        try:
            print("🚀 [전략] 에디터 정밀 수색 모드 개시...")
            # 에디터 주소 접속
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="domcontentloaded")
            
            # 페이지 안정화를 위해 충분히 대기 (해외 서버 특성 고려)
            print("🔍 화면 로딩 대기 중 (10초)...")
            await asyncio.sleep(10) 

            # 쿠키 만료 여부 최종 확인
            if "nidlogin" in page.url:
                print("❌ [실패] 쿠키가 만료되어 로그인 페이지로 튕겼습니다.")
                await page.screenshot(path="error_screenshot.png")
                return

            # 프레임 및 요소 수색
            frame = page.frame(name="mainFrame")
            target = frame if frame else page
            
            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 승전보"
            content = "사령관님, 집념의 끝에 도달했습니다! 자동 포스팅 성공 리포트입니다."

            print("✍️ 제목 입력 시도...")
            # 여러 개의 셀렉터를 후보로 둡니다 (네이버의 변화에 대응)
            try:
                title_input = await target.wait_for_selector(".se-title-input, textarea.se-title-input", timeout=20000)
                await title_input.click()
                await page.keyboard.type(title)
                print("✅ 제목 작성 완료")
            except Exception as e:
                print(f"⚠️ 제목 칸 발견 실패: {e}")
                await page.screenshot(path="error_screenshot.png")
                raise e

            print("✍️ 본문 작성 시도...")
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=50)
            print("✅ 본문 작성 완료")

            print("📤 발행 프로세스 시작...")
            publish_btn = await target.wait_for_selector(".se-publish-button", timeout=10000)
            await publish_btn.click()
            await asyncio.sleep(2)

            confirm_btn = await target.wait_for_selector(".se-confirm-button", timeout=10000)
            await confirm_btn.click()
            
            print("🏁🏁🏁🏁🏁 [미션 클리어] 사령관님, 성공입니다!")
            await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            # 실패 시 무조건 사진을 찍습니다.
            await page.screenshot(path="error_screenshot.png", full_page=True)
            print("📸 [보고] 오류 화면을 스크린샷으로 저장했습니다.")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
