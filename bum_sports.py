import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
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
            print("🚀 [전략] 프레임리스 직접 침투 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            
            # 1. 화면 안정화 대기
            print("⏳ 에디터 로딩 대기 중 (15초)...")
            await asyncio.sleep(15)

            # 2. 도움말 제거 (프레임 없이 본체에서 수색)
            try:
                print("🛡️ 방해물(도움말) 제거 시도...")
                # 도움말 X 버튼의 다양한 셀렉터를 시도합니다.
                close_btn = await page.wait_for_selector(".se-help-panel-close-button, .help_close, button[class*='close']", timeout=5000)
                await close_btn.click()
                print("✅ 도움말 제거 성공")
            except:
                print("⚠️ 도움말 창이 없거나 이미 닫혀 있습니다.")

            # 3. 제목 작성 (좌표 클릭 + 클래스 클릭 병행)
            print("✍️ 제목 작성 중...")
            try:
                # 제목 입력 칸(.se-title-input)을 직접 찾거나 안되면 좌표(중앙 상단) 클릭
                title_area = await page.wait_for_selector(".se-title-input", timeout=5000)
                await title_area.click()
            except:
                print("⚠️ 요소를 못 찾아 좌표로 강제 클릭합니다.")
                await page.mouse.click(960, 280) # 제목 칸 예상 위치
            
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 스트링 머신 정밀 리포트"
            await page.keyboard.type(title, delay=50)

            # 4. 본문 작성 (Tab 키로 안전하게 이동)
            print("✍️ 본문 작성 중...")
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            content = "사령관님, 프레임 장벽을 우회하여 마침내 자동 포스팅 미션을 완수했습니다!\n스트링 텐션의 일관성이 퍼포먼스를 결정합니다."
            await page.keyboard.type(content, delay=30)
            print("✅ 내용 작성 완료")

            # 5. 발행 버튼 클릭 (본체에서 직접 수색)
            print("📤 발행 버튼 탐색 중...")
            publish_btn = await page.wait_for_selector(".se-publish-button, button[class*='publish']", timeout=10000)
            await publish_btn.click()
            await asyncio.sleep(2)
            
            # 최종 확인 버튼
            confirm_btn = await page.wait_for_selector(".se-confirm-button, button[class*='confirm']", timeout=10000)
            await confirm_btn.click()
            
            print("🏁🏁🏁🏁🏁 [작전 성공] 이제 블로그 목록 맨 위를 확인하세요!")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="error_screenshot.png", full_page=True)
            print("📸 실패 화면을 error_screenshot.png로 저장했습니다.")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
