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
            print("🚀 [전략] 쿠키 주입 침투 개시...")
            await page.goto("https://www.naver.com", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)

            if "nidlogin" in page.url:
                print("❌ [실패] 쿠키 만료")
                return

            print("✅ [성공] 로그인 유효 확인")

            # [수정] 더 안정적인 글쓰기 주소로 변경
            print("📝 에디터 진입 시도...")
            write_url = f"https://blog.naver.com/{NAVER_ID}/postwrite"
            await page.goto(write_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)

            # [보강] 프레임이 있는지 확인하고, 없으면 본체에서 직접 찾기
            frame = page.frame(name="mainFrame")
            target = frame if frame else page # 프레임이 없으면 페이지 본체를 타겟으로 설정
            
            if frame:
                print("🖼️ PC용 mainFrame 발견!")
            else:
                print("📱 모바일 또는 다이렉트 에디터 모드로 진행")

            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 자동 브리핑"
            content = "사령관님, 마침내 에디터 장벽을 뚫고 성공했습니다!"

            # 제목 입력 (더 넓은 범위의 셀렉터)
            try:
                title_selector = "textarea.se-title-input, input.se-title-input"
                await target.wait_for_selector(title_selector, timeout=20000)
                await target.fill(title_selector, title)
                print("✍️ 제목 입력 성공")
            except:
                print("⚠️ 제목 입력 칸을 못 찾았습니다. 강제 입력을 시도합니다.")
                await page.keyboard.press("Tab")
                await page.keyboard.type(title)

            # 본문 입력
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=50)
            print("✍️ 본문 입력 성공")

            # 발행 버튼 (클래스 이름이 수시로 바뀌므로 텍스트로 찾기)
            print("📤 발행 시도...")
            # '발행'이라는 텍스트가 포함된 버튼 클릭
            await target.click("button:has-text('발행'), .se-publish-button")
            await asyncio.sleep(2)
            await target.click("button:has-text('발행'), .se-confirm-button")

            print("🏁🏁🏁🏁🏁 [미션 클리어] 진짜 성공입니다!")
            await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ 최종 오류 발생: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
