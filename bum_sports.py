import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def get_tennis_news(page):
    """네이버에서 최신 테니스 소식을 수집합니다."""
    print("🔍 외부 정보 수집 중...")
    search_url = "https://search.naver.com/search.naver?query=테니스+스트링+리뷰&nso=so:dd"
    await page.goto(search_url, wait_until="networkidle")
    await asyncio.sleep(3)
    news_items = await page.locator(".news_tit, .api_txt_lines.total_tit").all_inner_texts()
    return [item.strip() for item in news_items if len(item.strip()) > 5][:3]

async def post_blog():
    async with async_playwright() as p:
        # 모바일 환경 시뮬레이션
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 375, 'height': 812}, # 아이폰 크기
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
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
            # 1. 정보 수집
            news = await get_tennis_news(page)
            news_section = "\n".join([f"📍 {n}" for n in news]) if news else "📍 최신 장비 소식을 분석 중입니다."

            # 2. 모바일 글쓰기 페이지 접속
            print("🚀 [모바일 작전] 리포트 작성 시작...")
            await page.goto(f"https://m.blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(5)

            # 3. 내용 작성 (모바일은 구조가 매우 단순함)
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 정밀 리포트"
            content = f"오늘의 최신 테니스 소식입니다!\n\n{news_section}\n\n범 스포츠에서 전해드렸습니다."

            # 제목 입력
            await page.fill("input#subject", title)
            await asyncio.sleep(1)
            
            # 본문 입력
            await page.click("#content_common") # 본문 영역 클릭
            await page.keyboard.type(content, delay=30)
            print("✅ 내용 작성 완료")

            # 4. 등록 버튼 클릭
            await page.click(".btn_ok") # 모바일 등록 버튼
            print("📤 등록 버튼 클릭 완료")
            
            await asyncio.sleep(10) # 전송 대기
            
            # 결과물 PNG 생성
            await page.screenshot(path="final_report.png", full_page=True)
            print("🏁🏁🏁 작전 성공! final_report.png 생성 완료")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="final_report.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
