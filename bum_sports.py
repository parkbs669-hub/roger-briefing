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
            print("🚀 [전략] 아이프레임 침투 및 전문 리포트 작성 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            
            # 1. 아이프레임(mainFrame)이 나타날 때까지 대기
            print("🔍 mainFrame 수색 중...")
            await page.wait_for_selector("#mainFrame", timeout=30000)
            frame = page.frame(name="mainFrame")
            print("✅ mainFrame 침투 성공!")

            # 2. 도움말 닫기 (프레임 안에서 찾기)
            try:
                await frame.click(".se-help-panel-close-button, .help_close", timeout=5000)
                print("🛡️ 도움말 제거 완료")
            except: pass

            # 3. 제목 및 본문 작성 (프레임 내부 요소를 직접 타격)
            print("✍️ 스트링 머신 리포트 작성 중...")
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 스트링 머신 유지보수"
            content = "사령관님, 아이프레임 장벽을 뚫고 마침내 정밀 포스팅에 성공했습니다!\n스트링 클램프와 텐션 헤드를 꼭 점검하세요."

            # 제목 칸 클릭 후 입력
            await frame.click(".se-title-input")
            await page.keyboard.type(title, delay=50)
            
            # 본문 칸으로 이동 후 입력
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=30)
            print("✅ 작성 완료")

            # 4. 발행 버튼 클릭 (상단 메뉴는 page에서, 발행 팝업은 frame에서 처리)
            print("📤 발행 프로세스 시작...")
            await frame.click(".se-publish-button") # 발행 메뉴 열기
            await asyncio.sleep(2)
            
            # 최종 '발행' 버튼 클릭
            await frame.click(".se-confirm-button")
            
            print("🏁🏁🏁🏁🏁 [작전 성공] 이제 블로그 목록 맨 위를 확인하세요!")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="error_screenshot.png", full_page=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
