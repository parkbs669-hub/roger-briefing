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
            print("🚀 [최후의 일격] 발행 버튼 정밀 저격 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(15)

            # 1. 도움말 제거
            try:
                await page.click(".se-help-panel-close-button, .help_close", timeout=5000)
                print("🛡️ 도움말 제거 성공")
            except: pass

            # 2. 제목/본문 작성 (Tab 전략 고수)
            print("✍️ 제목 및 본문 작성 중...")
            await page.mouse.click(960, 10) # 포커스 초기화
            await asyncio.sleep(1)
            await page.keyboard.press("Tab")
            
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 스트링 머신 리포트"
            await page.keyboard.type(title, delay=50)
            
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            content = "사령관님, 수많은 장벽을 뚫고 마침내 발행까지 도달했습니다!\n테니스 스트링 텐션 관리는 승리의 핵심입니다."
            await page.keyboard.type(content, delay=30)
            print("✅ 내용 작성 완료")

            # 3. [핵심] 발행 메뉴 버튼 클릭 (여러 경로 수색)
            print("📤 발행 메뉴 수색 및 타격...")
            publish_selectors = [
                ".se-publish-button", 
                "button[class*='publish']", 
                "text='발행'",
                "button.btn_publish"
            ]
            
            publish_btn = None
            for selector in publish_selectors:
                try:
                    publish_btn = await page.wait_for_selector(selector, state="visible", timeout=5000)
                    if publish_btn:
                        await publish_btn.click(force=True)
                        print(f"🔥 발행 메뉴 클릭 성공 ({selector})")
                        break
                except: continue

            if not publish_btn:
                print("⚠️ 버튼을 못 찾아 강제 엔터로 메뉴 열기를 시도합니다.")
                await page.keyboard.press("Enter")

            await asyncio.sleep(3)

            # 4. [핵심] 최종 확인 버튼 클릭
            print("📤 최종 발행 확정 시도...")
            try:
                confirm_btn = await page.wait_for_selector(".se-confirm-button, button[class*='confirm']", state="visible", timeout=5000)
                await confirm_btn.click(force=True)
                print("🏁🏁🏁 [대성공] 미션 완료!")
            except:
                print("⚠️ 최종 확인 버튼 실패, 엔터 키로 마무리를 시도합니다.")
                await page.keyboard.press("Enter")
            
            await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="error_screenshot.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
