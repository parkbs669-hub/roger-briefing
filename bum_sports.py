import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def get_tennis_news(page):
    """네이버에서 '테니스 스트링' 최신 소식 3개를 수집합니다."""
    print("🔍 외부 정보 수집 중 (키워드: 테니스 스트링)...")
    search_url = "https://search.naver.com/search.naver?query=테니스+스트링+리뷰&nso=so:dd"
    await page.goto(search_url)
    await asyncio.sleep(3)
    
    # 제목과 링크 수집 시도
    news_items = await page.locator(".api_txt_lines.total_tit").all_inner_texts()
    return news_items[:3]

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
            # 1단계: 외부 정보 수집
            news = await get_tennis_news(page)
            news_section = "\n".join([f"📍 {n}" for n in news])

            # 2단계: 에디터 접속 및 작성
            print("🚀 수집 정보 포함 정밀 리포트 발행 개시...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(10)

            # (중략: 도움말 제거 로직)
            await page.mouse.click(1885, 35) 
            await asyncio.sleep(2)

            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 테니스 장비 & 이슈 브리핑"
            content = (
                f"사령관님, 오늘 수집된 최신 테니스 장비 소식과 범 스포츠의 정밀 팁입니다!\n\n"
                f"[오늘의 장비 관리 Tip]\n"
                f"스트링이 끊어지지 않더라도 3개월이 지나면 탄성을 잃습니다. "
                f"승리를 위해 정기적으로 텐션을 점검하세요!\n\n"
                f"[실시간 테니스 이슈 브리핑]\n"
                f"{news_section}\n\n"
                f"위 정보들을 바탕으로 최적의 장비 세팅을 찾아보시기 바랍니다."
            )

            # (중략: Tab 입력 및 발행 로직)
            await page.mouse.click(960, 300)
            await page.keyboard.press("Tab")
            await page.keyboard.type(title)
            await page.keyboard.press("Tab")
            await page.keyboard.type(content)
            
            # 발행
            await page.mouse.click(1850, 45)
            await asyncio.sleep(3)
            await page.keyboard.press("Enter")
            
            print("🏁🏁🏁 외부 정보 수집 및 포스팅 완료!")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        finally:
            await page.screenshot(path="error_screenshot.png")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
