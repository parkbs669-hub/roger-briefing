import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def run():
    async with async_playwright() as p:
        # 이번에는 다시 PC 모드로 확실하게 접근합니다.
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        aut_val = str(os.environ.get('NID_AUT') or "").strip()
        ses_val = str(os.environ.get('NID_SES') or "").strip()

        await context.add_cookies([
            {'name': 'NID_AUT', 'value': aut_val, 'domain': '.naver.com', 'path': '/'},
            {'name': 'NID_SES', 'value': ses_val, 'domain': '.naver.com', 'path': '/'}
        ])
        
        page = await context.new_page()

        try:
            print("🚀 [최종 작전] 스마트에디터 정밀 타격 개시...")
            # 에디터 직접 진입
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="domcontentloaded")
            
            # iframe(mainFrame) 진입 대기
            await page.wait_for_selector("#mainFrame", timeout=30000)
            frame = page.frame(name="mainFrame")
            print("✅ 에디터 프레임 접속 성공")

            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 자동 브리핑"
            content = "사령관님, 마침내 제목과 본문을 분리하여 발행까지 성공했습니다!"

            # 1. 제목 입력 (사진 속 '제목' 칸 정밀 타겟)
            print("✍️ 제목 작성 중...")
            title_area = await frame.wait_for_selector(".se-title-input", timeout=20000)
            await title_area.click()
            await page.keyboard.type(title)
            await asyncio.sleep(1)

            # 2. 본문 입력 (사진 속 본문 영역 클릭)
            print("✍️ 본문 작성 중...")
            await page.keyboard.press("Tab") # 제목에서 본문으로 이동
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=50)
            print("✅ 내용 작성 완료")

            # 3. [발행] 버튼 클릭 (우측 상단 초록색 버튼)
            print("📤 [발행] 버튼 찾는 중...")
            # 프레임 밖(상단바)에 있는 발행 버튼을 타격합니다.
            await frame.click("button.se-publish-button") # 1단계: 발행 메뉴 열기
            await asyncio.sleep(2)
            
            # 4. [발행하기] 최종 확인 버튼
            print("📤 최종 [발행] 확정 중...")
            await frame.click("button.se-confirm-button")
            
            print("🏁🏁🏁🏁🏁 [대성공] 이제 진짜 블로그 목록 맨 위에 떴을 겁니다!")
            await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ 최종 오류 발생: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
