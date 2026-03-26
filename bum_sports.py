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

        aut_val = str(os.environ.get('NID_AUT') or "").strip()
        ses_val = str(os.environ.get('NID_SES') or "").strip()

        await context.add_cookies([
            {'name': 'NID_AUT', 'value': aut_val, 'domain': '.naver.com', 'path': '/'},
            {'name': 'NID_SES', 'value': ses_val, 'domain': '.naver.com', 'path': '/'}
        ])
        
        page = await context.new_page()

        try:
            print("🚀 [최종 돌격] 임시저장 탈출 및 강제 발행 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(12)

            # 1. 도움말 팝업 제거 (발행 버튼을 가릴 수 있음)
            try:
                await page.click(".se-help-panel-close-button, .help_close", timeout=5000)
                print("🛡️ 방해물(도움말) 제거 완료")
            except: pass

            today_date = datetime.now().strftime('%Y-%m-%d')
            title = f"🎾 [범 스포츠] {today_date} 테니스 스트링 리포트 1호"
            content = "사령관님, 이번에는 발행 버튼을 끝까지 추적해 성공시키겠습니다!"

            # 2. 내용 작성 (Tab 전략)
            await page.mouse.click(500, 500) 
            await asyncio.sleep(1)
            await page.keyboard.press("Tab")
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab")
            await page.keyboard.type(content, delay=30)
            print("✅ 포스팅 내용 작성 완료")

            # 3. [핵심] 발행 버튼 1단계 클릭
            print("📤 발행 메뉴 여는 중...")
            publish_btn = await page.wait_for_selector(".se-publish-button", state="visible", timeout=15000)
            await publish_btn.click(force=True)
            await asyncio.sleep(3)

            # 4. [핵심] 최종 '발행하기' 버튼 정밀 타격
            print("📤 최종 발행 확정 시도...")
            # 확인 버튼이 나타날 때까지 기다린 후 엔터 키와 클릭을 병행
            try:
                # '발행' 글자가 들어간 버튼을 찾습니다.
                final_btn = await page.wait_for_selector("button:has-text('발행'), .se-confirm-button", state="visible", timeout=10000)
                await final_btn.click(force=True)
                print("🔥 최종 확인 버튼 클릭 성공!")
            except:
                print("⚠️ 버튼 클릭 실패, 강제 엔터 발행을 시도합니다.")
                await page.keyboard.press("Enter")
            
            await asyncio.sleep(5)
            print(f"🏁🏁🏁🏁🏁 [작전 성공] 이제 진짜 블로그 '목록보기'를 확인하세요!")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="error_screenshot.png", full_page=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
