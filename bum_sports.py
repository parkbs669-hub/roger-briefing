import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def get_tennis_news(page):
    """네이버 통합검색에서 최신 소식을 수집합니다."""
    print("🔍 외부 정보 수집 중 (키워드: 테니스 스트링)...")
    search_url = "https://search.naver.com/search.naver?query=테니스+스트링+리뷰&nso=so:dd"
    await page.goto(search_url, wait_until="networkidle")
    await asyncio.sleep(3)
    news_items = await page.locator(".news_tit, .api_txt_lines.total_tit").all_inner_texts()
    return [item.strip() for item in news_items if len(item.strip()) > 5][:3]

async def post_blog():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        
        # 쿠키 주입
        aut_val = str(os.environ.get('NID_AUT') or "").strip()
        ses_val = str(os.environ.get('NID_SES') or "").strip()
        await context.add_cookies([
            {'name': 'NID_AUT', 'value': aut_val, 'domain': '.naver.com', 'path': '/'},
            {'name': 'NID_SES', 'value': ses_val, 'domain': '.naver.com', 'path': '/'}
        ])

        page = await context.new_page()

        try:
            news = await get_tennis_news(page)
            news_section = "\n".join([f"📍 {n}" for n in news]) if news else "📍 최신 장비 소식을 분석 중입니다."

            print("🚀 수집 정보 포함 정밀 리포트 발행 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(15)

            # 도움말 제거
            await page.mouse.click(1885, 35) 
            await asyncio.sleep(2)

            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 테니스 장비 & 이슈 브리핑"
            content = (
                f"사령관님, 오늘 수집된 최신 테니스 장비 소식과 범 스포츠의 정밀 팁입니다!\n\n"
                f"[오늘의 장비 관리 Tip]\n"
                f"스트링이 끊어지지 않더라도 3개월이 지나면 탄성을 잃습니다. 승리를 위해 정기적으로 텐션을 점검하세요!\n\n"
                f"[실시간 테니스 이슈 브리핑]\n"
                f"{news_section}\n\n"
                f"위 정보들을 바탕으로 최적의 장비 세팅을 찾아보시기 바랍니다."
            )

            await page.mouse.click(960, 300)
            await page.keyboard.press("Tab")
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab")
            await page.keyboard.type(content, delay=30)
            
            # 발행 및 확정
            print("📤 발행 버튼 타격 및 확정 대기...")
            await page.mouse.click(1850, 45) 
            await asyncio.sleep(3)
            
            try:
                confirm_btn = await page.wait_for_selector(".se-confirm-button, button:has-text('발행')", timeout=10000)
                await confirm_btn.click()
            except:
                await page.keyboard.press("Enter")

            # 🏁 서버 전송 완료를 위해 충분히 대기 후 스크린샷
            print("⏳ 최종 전송 확인 중 (10초)...")
            await asyncio.sleep(10)
            
            # 파일명을 고정하여 png로 저장
            await page.screenshot(path="final_report.png", full_page=True)
            print("🏁🏁🏁 작전 성공! png 결과물 생성 완료.")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="final_report.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
