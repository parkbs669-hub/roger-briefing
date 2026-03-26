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
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale='ko-KR' # 한국어로 설정
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
            print("🚀 [최종 확정] 전체 공개 및 카테고리 강제 설정 작전 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="domcontentloaded")
            await asyncio.sleep(15)

            # 1. 도움말 제거
            try:
                await page.click(".se-help-panel-close-button, .help_close", timeout=5000)
                print("🛡️ 도움말 제거 성공")
            except: pass

            today_date = datetime.now().strftime('%Y-%m-%d')
            title = f"🎾 [범 스포츠] {today_date} 스트링 머신 정밀 리포트"
            content = "사령관님, 이번에는 '전체 공개' 설정을 강제하여 확실히 목록 맨 위에 올리겠습니다!"

            # 2. 내용 작성 (Tab 전략)
            print("✍️ 제목 및 본문 작성 중...")
            await page.mouse.click(960, 10) # 포커스 초기화
            await asyncio.sleep(1)
            await page.keyboard.press("Tab")
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=30)
            print("✅ 내용 작성 완료")

            # 3. [핵심] 발행 메뉴 열기 및 설정 강제
            print("📤 발행 메뉴 진입 및 설정 강제...")
            publish_btn = await page.wait_for_selector(".se-publish-button", state="visible", timeout=15000)
            await publish_btn.click()
            await asyncio.sleep(3)

            # [보강] 카테고리 강제 선택 (첫 번째 카테고리 선택)
            try:
                print("📂 카테고리 설정 중...")
                category_select = await page.wait_for_selector(".se-publish-properties-category-item", timeout=5000)
                await category_select.click()
            except:
                print("⚠️ 카테고리 선택 실패, 기본값으로 진행")

            # [보강] 전체 공개 강제 설정
            try:
                print("🌐 전체 공개 설정 확인 중...")
                public_radio = await page.wait_for_selector("text='전체공개'", timeout=5000)
                await public_radio.click()
            except:
                print("⚠️ 전체공개 버튼 실패, 기본값으로 진행")

            # [보강] 댓글 허용 강제 설정
            try:
                print("💬 댓글 허용 설정 중...")
                comment_check = await page.wait_for_selector("text='댓글허용'", timeout=5000)
                await comment_check.click()
            except:
                print("⚠️ 댓글허용 버튼 실패, 기본값으로 진행")

            await asyncio.sleep(2)

            # 4. 최종 발행 확정 (연타 모드)
            print("📤 최종 발행 확정 시도...")
            for i in range(3): # 3번 반복 클릭 시도
                try:
                    confirm_btn = await page.wait_for_selector(".se-confirm-button, button[class*='confirm']", state="visible", timeout=5000)
                    await confirm_btn.click(force=True)
                    print(f"🏁 최종 확인 클릭 성공 ({i+1}회차)")
                    await asyncio.sleep(2)
                except:
                    print(f"⚠️ {i+1}회차 클릭 실패, 다시 시도...")
                    await page.keyboard.press("Enter") # 엔터 키 백업
            
            print("🏁🏁🏁🏁🏁 [작전 종료] 이제 블로그 목록 맨 위를 확인하세요!")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="error_screenshot.png", full_page=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
