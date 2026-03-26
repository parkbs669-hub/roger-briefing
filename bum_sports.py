import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def get_tennis_news(page):
    print("🔍 외부 정보 수집 중...")
    search_url = "https://search.naver.com/search.naver?query=테니스+스트링+리뷰&nso=so:dd"
    await page.goto(search_url, wait_until="networkidle")
    await asyncio.sleep(3)
    news_items = await page.locator(".news_tit, .api_txt_lines.total_tit").all_inner_texts()
    return [item.strip() for item in news_items if len(item.strip()) > 5][:3]

async def post_blog():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        
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

            print("🚀 포스팅 작성 시작...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(15)

            # 도움말 제거 및 내용 입력
            await page.mouse.click(1885, 35) 
            await asyncio.sleep(2)
            
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 테니스 장비 브리핑"
            content = f"오늘의 최신 소식입니다!\n\n{news_section}\n\n범 스포츠에서 전해드렸습니다."

            await page.mouse.click(960, 300)
            await page.keyboard.press("Tab")
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab")
            await page.keyboard.type(content, delay=30)
            
            # 발행 클릭
            await page.mouse.click(1850, 45) 
            await asyncio.sleep(3)
            try:
                confirm_btn = await page.wait_for_selector(".se-confirm-button", timeout=5000)
                await confirm_btn.click()
            except:
                await page.keyboard.press("Enter")

            print("⏳ 서버 전송 및 PNG 생성 대기...")
            await asyncio.sleep(10)
            
            # 📸 PNG 파일 생성
            await page.screenshot(path="final_report.png", full_page=True)
            print("✅ final_report.png 생성 완료")

        except Exception as e:
            print(f"❌ 오류: {e}")
            await page.screenshot(path="final_report.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
