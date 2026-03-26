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
            print("🚀 [전문 리포트] 테니스 스트링 머신 정보 포스팅 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(12)

            # 도움말 팝업 제거
            try:
                await page.click(".se-help-panel-close-button, .help_close", timeout=3000)
            except: pass

            # --- 📝 포스팅 내용 구성 (사령관님의 관심사 반영) ---
            today_date = datetime.now().strftime('%Y-%m-%d')
            title = f"🎾 [범 스포츠] {today_date} 테니스 스트링 머신 유지보수 가이드"
            
            content = f"""안녕하세요, 로저범서입니다.
오늘의 '범 스포츠' 브리핑은 테니스 스트링 머신 관리에 대해 다뤄봅니다.

✅ 스트링 머신 핵심 부품 점검 리스트:
1. 스타팅 클램프: 스프링 텐션이 일정하게 유지되는지 확인이 필요합니다.
2. 사이드 서포트: 라켓 프레임 고정 시 변형을 막기 위해 고무 패딩 상태를 점검하세요.
3. 텐션 헤드: 그리퍼 내부의 이물질을 주기적으로 제거해야 줄 미끄러짐을 방지할 수 있습니다.

정확한 스트링 작업이 코트 위에서의 퍼포먼스를 결정합니다. 
범 스포츠는 여러분의 완벽한 텐션을 응원합니다!

#테니스 #스트링머신 #테니스용품 #범스포츠 #로저범서"""

            # --- ✍️ 블라인드 침투 작성 ---
            await page.mouse.click(500, 500) 
            await asyncio.sleep(1)

            # 제목 입력
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(title, delay=50)

            # 본문 입력
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            # 본문이 길므로 한 줄씩 입력하여 안정성을 높입니다.
            for line in content.split('\n'):
                await page.keyboard.type(line, delay=30)
                await page.keyboard.press("Enter")
            
            print("✅ 전문 콘텐츠 작성 완료")

            # --- 📤 발행 및 확정 ---
            publish_btn = await page.wait_for_selector(".se-publish-button, button[class*='publish']", timeout=10000)
            await publish_btn.click()
            await asyncio.sleep(2)

            confirm_btn = await page.wait_for_selector(".se-confirm-button, button[class*='confirm']", timeout=10000)
            await confirm_btn.click()
            
            print(f"🏁🏁🏁 [미션 완료] '{title}' 포스팅 성공!")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="error_screenshot.png", full_page=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
