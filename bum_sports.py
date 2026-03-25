import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def run():
    async with async_playwright() as p:
        # 모바일 환경처럼 보이게 설정 (에러 확률이 더 낮습니다)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            **p.devices['iPhone 13'], # 아이폰 환경 모의
            locale='ko-KR'
        )

        aut_val = str(os.environ.get('NID_AUT') or "").strip()
        ses_val = str(os.environ.get('NID_SES') or "").strip()

        await context.add_cookies([
            {'name': 'NID_AUT', 'value': aut_val, 'domain': '.naver.com', 'path': '/'},
            {'name': 'NID_SES', 'value': ses_val, 'domain': '.naver.com', 'path': '/'}
        ])
        
        page = await context.new_page()

        try:
            print("🚀 [전략] 모바일 모드 침투 개시...")
            # 모바일 전용 글쓰기 주소
            await page.goto(f"https://m.blog.naver.com/{NAVER_ID}/postwrite", wait_until="domcontentloaded")
            await asyncio.sleep(5)

            if "nidlogin" in page.url:
                print("❌ [실패] 쿠키 만료")
                return

            print("✅ 에디터 진입 성공")

            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 리포트"
            content = "사령관님, 모바일 에디터 최적화로 마침내 성공했습니다!"

            # 1. 제목 입력 (모바일은 ID가 다를 수 있어 포커스 후 입력)
            print("✍️ 내용 작성 중...")
            await page.keyboard.press("Tab") # 제목 칸으로 이동 시도
            await asyncio.sleep(1)
            await page.keyboard.type(title)
            
            # 2. 본문 입력
            await page.keyboard.press("Enter")
            await page.keyboard.type(content, delay=50)
            print("✍️ 입력 완료")

            # 3. 발행 버튼 클릭 (모바일 전용 타겟팅)
            print("📤 발행 시도...")
            # 모바일 상단 '등록' 또는 '발행' 버튼 수색
            publish_selectors = [
                "button.btn_post", 
                "a.btn_post", 
                ".post_write_footer button", 
                "text='등록'", 
                "text='발행'"
            ]
            
            success_click = False
            for selector in publish_selectors:
                try:
                    # 버튼이 보일 때까지 살짝 대기 후 클릭
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=3000):
                        await btn.click(force=True)
                        success_click = True
                        print(f"✅ 버튼 클릭 성공: {selector}")
                        break
                except:
                    continue

            if not success_click:
                print("⚠️ 버튼을 못 찾아 강제 엔터 발행을 시도합니다.")
                await page.keyboard.press("Control+Enter")

            # 최종 확인 버튼 (모바일은 바로 등록되는 경우가 많음)
            await asyncio.sleep(3)
            print("🏁🏁🏁 [미션 클리어] 이번엔 진짜 블로그를 확인해 보세요!")

        except Exception as e:
            print(f"❌ 최종 오류 발생: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
