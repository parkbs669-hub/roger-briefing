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

        # 쿠키 주입 (통행증)
        aut_val = str(os.environ.get('NID_AUT') or "").strip()
        ses_val = str(os.environ.get('NID_SES') or "").strip()

        await context.add_cookies([
            {'name': 'NID_AUT', 'value': aut_val, 'domain': '.naver.com', 'path': '/'},
            {'name': 'NID_SES', 'value': ses_val, 'domain': '.naver.com', 'path': '/'}
        ])
        
        page = await context.new_page()

        try:
            print("🚀 [최종 병기] 블라인드 침투 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            
            # 1. 에디터 로딩 대기
            print("⏳ 에디터 로딩 대기 중 (12초)...")
            await asyncio.sleep(12)

            # 2. 도움말 팝업 강제 제거 (보이든 안 보이든 시도)
            try:
                await page.click(".se-help-panel-close-button, .help_close", timeout=3000)
                print("🛡️ 도움말 창 제거 완료")
            except: pass

            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 자동 브리핑"
            content = "사령관님, 수많은 장벽을 뚫고 마침내 자동 포스팅 시스템 구축에 성공했습니다!"

            # 3. [핵심] Tab 키를 이용한 제목/본문 강제 점유
            print("✍️ 제목/본문 무차별 작성 중...")
            
            # 에디터 아무 데나 한 번 클릭해서 포커스 잡기
            await page.mouse.click(500, 500) 
            await asyncio.sleep(1)

            # 제목 칸으로 이동 (대부분 첫 번째 Tab은 제목입니다)
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(title, delay=50)
            print("✅ 제목 입력 시도 완료")

            # 본문 칸으로 이동
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=50)
            print("✅ 본문 입력 시도 완료")

            # 4. 발행 버튼 직접 타격 (이름 대신 위치와 클래스 혼합)
            print("📤 발행 및 확정 시도...")
            publish_btn = await page.wait_for_selector(".se-publish-button, button[class*='publish']", timeout=10000)
            await publish_btn.click()
            await asyncio.sleep(2)

            confirm_btn = await page.wait_for_selector(".se-confirm-button, button[class*='confirm']", timeout=10000)
            await confirm_btn.click()
            
            print("🏁🏁🏁🏁🏁 [대성공] 사령관님, 이제 진짜 샴페인을 터뜨리십시오!")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="error_screenshot.png", full_page=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
