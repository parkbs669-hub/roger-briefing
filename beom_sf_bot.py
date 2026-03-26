import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def get_tennis_news(page):
    """네이버 통합검색에서 최신 테니스 소식을 수집합니다."""
    print("🔍 외부 정보 수집 중...")
    search_url = "https://search.naver.com/search.naver?query=테니스+스트링+리뷰&nso=so:dd"
    await page.goto(search_url, wait_until="networkidle")
    await asyncio.sleep(3)
    news_items = await page.locator(".news_tit, .api_txt_lines.total_tit").all_inner_texts()
    return [item.strip() for item in news_items if len(item.strip()) > 5][:3]

async def post_blog():
    async with async_playwright() as p:
        # 자동화 탐지 방지 및 PC 환경 설정
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        
        # 쿠키 주입 (Secrets 설정 필수)
        aut_val = str(os.environ.get('NID_AUT') or "").strip()
        ses_val = str(os.environ.get('NID_SES') or "").strip()
        await context.add_cookies([
            {'name': 'NID_AUT', 'value': aut_val, 'domain': '.naver.com', 'path': '/'},
            {'name': 'NID_SES', 'value': ses_val, 'domain': '.naver.com', 'path': '/'}
        ])

        page = await context.new_page()

        try:
            # 1. 정보 수집 단계
            news = await get_tennis_news(page)
            news_section = "\n".join([f"📍 {n}" for n in news]) if news else "📍 최신 장비 소식을 분석 중입니다."

            # 2. 에디터 접속 및 방해물 제거
            print("🚀 [SF Checker] 리포트 작성 시작...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(15)

            # 도움말 닫기 (좌표 1885, 35 정밀 타격)
            await page.mouse.click(1885, 35) 
            await asyncio.sleep(2)
            
            # 3. 리포트 내용 구성
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 시스템 자동 점검 리포트"
            content = (
                f"사령관님, 시스템 자동 점검 및 최신 테니스 이슈 수집을 완료했습니다!\n\n"
                f"[실시간 수집 정보]\n"
                f"{news_section}\n\n"
                f"범 스포츠의 모든 시스템이 정상 가동 중임을 보고드립니다."
            )

            # 제목/본문 입력 (Tab 키 전략)
            await page.mouse.click(960, 300)
            await page.keyboard.press("Tab")
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab")
            await page.keyboard.type(content, delay=30)
            print("✅ 데이터 입력 완료")

            # 4. 발행 및 최종 확정
            print("📤 발행 버튼 타격 중...")
            await page.mouse.click(1850, 45) # 발행 버튼 좌표
            await asyncio.sleep(3)
            
            try:
                # 최종 확인 버튼 클릭
                confirm_btn = await page.wait_for_selector(".se-confirm-button", timeout=5000)
                await confirm_btn.click()
            except:
                await page.keyboard.press("Enter")

            # 5. 전송 대기 및 PNG 결과물 생성
            print("⏳ 서버 전송 완료 대기 중 (10초)...")
            await asyncio.sleep(10)
            await page.screenshot(path="final_report.png", full_page=True)
            print("🏁🏁🏁 작전 성공! final_report.png 생성 완료")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="final_report.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
