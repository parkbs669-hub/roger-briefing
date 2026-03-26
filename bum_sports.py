import os
import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def get_tennis_trends(page):
    """네이버에서 테니스 스트링 최신 정보를 수집합니다."""
    print("🔍 외부 정보 수집 및 분석 중...")
    search_url = "https://search.naver.com/search.naver?query=테니스+스트링+추천+후기+교체&nso=so:dd"
    await page.goto(search_url, wait_until="networkidle")
    await asyncio.sleep(3)
    
    items = await page.locator(".news_tit, .api_txt_lines.total_tit").all_inner_texts()
    seen = set()
    unique_items = []
    for item in items:
        clean_item = item.strip()
        if clean_item and clean_item not in seen:
            unique_items.append(f"📍 {clean_item}")
            seen.add(clean_item)
            if len(unique_items) >= 5: break
            
    return "\n".join(unique_items) if unique_items else "📍 최신 장비 소식을 정밀 분석 중입니다."

async def post_blog():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
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
            # 1. 정보 수집
            trends_report = await get_tennis_trends(page)

            # 2. 블로그 에디터 접속
            print(f"🚀 [범 스포츠] 통합 리포트 작성 시작 (ID: {NAVER_ID})...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(15)

            # 🛡️ 도움말 제거 (이전 성공 로직 유지)
            print("🛡️ 도움말 장벽 강제 제거 중...")
            await page.evaluate("() => { const panel = document.querySelector('.se-help-panel'); if(panel) panel.remove(); }")
            await page.mouse.click(1885, 35) 
            await asyncio.sleep(2)
            
            # 3. 리포트 내용 작성
            today_str = datetime.now().strftime("%Y년 %m월 %d일")
            title = f"🎾 [범 스포츠] {today_str} 테니스 스트링 정밀 분석 리포트"
            content = (
                f"사령관님, 오늘 네이버에서 수집된 최신 테니스 장비 이슈입니다!\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔍 실시간 테니스 스트링 트렌드\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{trends_report}\n\n"
                f"사령관님의 정밀 타격 좌표(1840, 30)를 적용하여 발행된 자동 리포트입니다.\n"
                f"오늘도 범 스포츠와 함께 승리하는 테니스 되시기 바랍니다."
            )

            # 데이터 입력 (Tab 전략)
            await page.mouse.click(960, 300)
            await page.keyboard.press("Tab")
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab")
            await page.keyboard.type(content, delay=30)
            print("✅ 리포트 내용 입력 완료")

            # 4. [정밀 타격] 발행 버튼 (사령관님 좌표: 1847, 25)
            print(f"📤 사령관님 지정 좌표(1847, 25) 정밀 타격 중...")
            await page.mouse.click(1847, 25) 
            await asyncio.sleep(3)
            
            # 5. 최종 발행 확정
            print("📤 최종 발행 확정 시도...")
            try:
                # 확인 버튼 클래스 탐색
                confirm_btn = await page.wait_for_selector(".se-confirm-button", timeout=5000)
                await confirm_btn.click()
                print("✅ 최종 확인 버튼 클릭 성공")
            except:
                # 안되면 엔터 연타
                print("⚠️ 확인 버튼 미포착 -> 엔터 키 연타로 강제 돌파")
                for _ in range(3):
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(1)

            # 6. 서버 전송 및 PNG 생성
            print("⏳ 서버 전송 완료 대기 (15초)...")
            await asyncio.sleep(15)
            await page.screenshot(path="final_report.png", full_page=True)
            print("🏁🏁🏁 미션 완수! final_report.png를 확인하십시오.")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="final_report.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
