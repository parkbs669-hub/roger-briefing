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
            print("🚀 [최후의 돌격] 프레임 장벽 돌파 및 발행 저격 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            
            # 1. [핵심 보강] mainFrame이 나타날 때까지 최대 60초 대기
            print("🔍 mainFrame 수색 중 (최대 60초)...")
            await page.wait_for_selector("#mainFrame", state="attached", timeout=60000)
            frame = page.frame(name="mainFrame")
            print("✅ mainFrame 진입 성공!")

            # 2. 도움말 제거 (프레임 안에서 실행)
            try:
                close_btn = await frame.wait_for_selector(".se-help-panel-close-button, .help_close, button[class*='close']", timeout=10000)
                await close_btn.click()
                print("🛡️ 도움말 창 제거 완료")
                await asyncio.sleep(2)
            except: pass

            today_date = datetime.now().strftime('%Y-%m-%d')
            title = f"🎾 [범 스포츠] {today_date} 테니스 스트링 머신 정밀 리포트"
            content = "사령관님, mainFrame 장벽을 뚫고 마침내 자동 발행에 성공했습니다!\n스트링 텐션의 일관성이 퍼포먼스를 결정합니다."

            # 3. 제목 및 본문 작성 (프레임 내부 요소를 타격)
            print("✍️ 리포트 작성 중...")
            await frame.click(".se-title-input")
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=30)
            print("✅ 작성 완료")

            # 4. [핵심 보강] 발행 버튼 정밀 추적 (여러 경로 수색)
            print("📤 발행 버튼 수색 중...")
            publish_selectors = [
                ".se-publish-button", 
                "button[class*='publish']", 
                "text='발행'",
                "button.btn_publish"
            ]
            
            publish_btn = None
            for selector in publish_selectors:
                try:
                    publish_btn = await frame.wait_for_selector(selector, state="visible", timeout=10000)
                    if publish_btn:
                        await publish_btn.click()
                        print(f"🔥 발행 버튼 클릭 성공 ({selector})")
                        break
                except: continue

            if not publish_btn:
                print("⚠️ 버튼을 못 찾아 강제 엔터로 발행을 시도합니다.")
                await page.keyboard.press("Enter")

            await asyncio.sleep(3)

            # 5. 최종 확인 버튼 클릭
            print("📤 최종 발행 확정 시도...")
            try:
                confirm_btn = await frame.wait_for_selector(".se-confirm-button, button[class*='confirm']", state="visible", timeout=10000)
                await confirm_btn.click()
                print("🏁🏁🏁 [대성공] 미션 클리어!")
            except:
                print("⚠️ 최종 확인 버튼 실패, 엔터 키로 마무리를 시도합니다.")
                await page.keyboard.press("Enter")
            
            await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="error_screenshot.png", full_page=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
