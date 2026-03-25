import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 실제 브라우저와 똑같이 보이도록 더 정교하게 설정
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="ko-KR"
        )

        aut_val = str(os.environ.get('NID_AUT') or "").strip()
        ses_val = str(os.environ.get('NID_SES') or "").strip()

        await context.add_cookies([
            {'name': 'NID_AUT', 'value': aut_val, 'domain': '.naver.com', 'path': '/'},
            {'name': 'NID_SES', 'value': ses_val, 'domain': '.naver.com', 'path': '/'}
        ])
        
        page = await context.new_page()

        try:
            print("🚀 [전략] 에디터 직접 타격 모드 개시...")
            # 에디터 주소로 바로 접속
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="domcontentloaded")
            
            # 1. 프레임이 나타날 때까지 기다리되, 안 나타나면 현재 페이지에서 수색
            print("🔍 에디터 구성 요소 수색 중...")
            await asyncio.sleep(7) # 페이지 안정화 대기

            # 프레임 내부 혹은 본체에서 제목 칸 찾기
            frame = page.frame(name="mainFrame")
            target = frame if frame else page
            
            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 승전보"
            content = "사령관님, 수많은 시행착오 끝에 드디어 자동 포스팅 미션을 완수했습니다!"

            # 2. 제목 입력 (사진 속 '제목' 글자가 보이는 곳)
            print("✍️ 제목 작성...")
            title_input = await target.wait_for_selector(".se-title-input", timeout=20000)
            await title_input.click()
            await page.keyboard.type(title)
            await asyncio.sleep(1)

            # 3. 본문 입력 (Tab 키로 안전하게 이동)
            print("✍️ 본문 작성...")
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=50)

            # 4. 발행 버튼 클릭 (초록색 [발행] 버튼 정밀 타격)
            print("📤 발행 버튼 탐색...")
            publish_open = await target.wait_for_selector(".se-publish-button", timeout=10000)
            await publish_open.click()
            await asyncio.sleep(2)

            # 5. 최종 [발행] 확정 클릭
            confirm_btn = await target.wait_for_selector(".se-confirm-button", timeout=10000)
            await confirm_btn.click()
            
            print("🏁🏁🏁🏁🏁 [최종 성공] 사령관님, 이제 진짜 블로그를 확인하십시오!")
            await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            # 실패 시 화면 스크린샷 저장 (디버깅용)
            await page.screenshot(path="error_screenshot.png")
            print("📸 오류 화면을 error_screenshot.png로 저장했습니다.")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
