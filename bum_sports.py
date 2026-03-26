import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def debug_elements(target):
    """[디버깅] 현재 화면의 구성 요소 수색"""
    print("\n" + "="*60)
    print("🔍 [데이터 판독] 에디터 내부 수색 시작")
    print("="*60)
    textareas = await target.query_selector_all("textarea")
    print(f"📝 Textarea 개수: {len(textareas)}")
    editables = await target.query_selector_all("[contenteditable='true']")
    print(f"✏️ 입력 가능 영역(Editable) 개수: {len(editables)}")
    print("="*60 + "\n")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        # ✅ [핵심] 로그인 대신 쿠키 주입 (CAPTCHA 회피)
        aut_val = str(os.environ.get('NID_AUT') or "").strip()
        ses_val = str(os.environ.get('NID_SES') or "").strip()

        if not aut_val or not ses_val:
            print("❌ Secrets에 NID_AUT/NID_SES가 없습니다.")
            return

        await context.add_cookies([
            {'name': 'NID_AUT', 'value': aut_val, 'domain': '.naver.com', 'path': '/'},
            {'name': 'NID_SES', 'value': ses_val, 'domain': '.naver.com', 'path': '/'}
        ])
        
        page = await context.new_page()

        try:
            print("🚀 Step 1: 에디터 직접 침투 (쿠키 모드)")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="domcontentloaded")
            await asyncio.sleep(10)

            # 로그인 튕김 확인
            if "nidlogin" in page.url:
                print("❌ 쿠키 만료: 브라우저에서 NID_AUT, NID_SES를 새로 복사하세요.")
                await page.screenshot(path="error_screenshot.png")
                return

            # 프레임 확인
            main_frame = page.frame(name="mainFrame")
            target = main_frame if main_frame else page
            print(f"✅ 에디터 접속 성공 ({'iframe 모드' if main_frame else '직접 모드'})")

            # 도움말 팝업 제거
            try:
                close_btn = await target.query_selector(".se-help-panel-close-button, .help_close, button[class*='close']")
                if close_btn:
                    await close_btn.click()
                    print("🛡️ 도움말 창 제거 완료")
                    await asyncio.sleep(2)
            except: pass

            await debug_elements(target)

            # 제목/본문 작성
            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 통합 리포트"
            content = "사령관님, 보안 문자를 회피하고 정밀 디버깅 로직으로 미션을 완수했습니다!"

            print("✍️ 제목/본문 작성 중...")
            title_input = await target.wait_for_selector(".se-title-input", timeout=15000)
            await title_input.click()
            await page.keyboard.type(title)
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=30)

            # 발행
            print("📤 최종 발행 중...")
            await target.click(".se-publish-button")
            await asyncio.sleep(2)
            await target.click(".se-confirm-button")
            
            print("🏁🏁🏁 [미션 클리어] 성공했습니다!")

        except Exception as e:
            print(f"❌ 오류: {e}")
            await page.screenshot(path="error_screenshot.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
