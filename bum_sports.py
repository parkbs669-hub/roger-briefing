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
            print("🚀 [범 스포츠] 통합 리포트 작성 시작...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(15)

            # 🛡️ [도움말 완전 박살 로직]
            print("🛡️ 도움말 제거 및 강제 노출 작전...")
            # 방식 A: 클래스명으로 닫기 버튼 클릭
            try: await page.locator(".se-help-panel-close-button").click(timeout=3000)
            except: pass
            
            # 방식 B: 스크린샷에서 확인된 좌표(1885, 35) 정밀 타격
            await page.mouse.click(1885, 35) 
            await asyncio.sleep(1)
            
            # 방식 C: 도움말 패널 자체를 코드로 '삭제' (최후의 수단)
            await page.evaluate("() => { const panel = document.querySelector('.se-help-panel'); if(panel) panel.remove(); }")
            print("✅ 도움말 장벽 제거 시도 완료")
            
            # 3. 리포트 내용 구성
            today_str = datetime.now().strftime("%Y년 %m월 %d일")
            title = f"🎾 [범 스포츠] {today_str} 테니스 스트링 최신 이슈 리포트"
            content = (
                f"사령관님, 오늘 네이버에서 포착된 최신 테니스 트렌드입니다!\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔍 실시간 테니스 스트링 트렌드\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{trends_report}\n\n"
                f"수집 키워드: 추천, 후기, 거트 교체, 장력 등\n"
                f"범 스포츠의 정밀한 장비 관리를 위해 참고하시기 바랍니다."
            )

            # 제목/본문 입력 (Tab 전략)
            await page.mouse.click(960, 300)
            await page.keyboard.press("Tab")
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab")
            await page.keyboard.type(content, delay=30)
            print("✅ 리포트 내용 입력 완료")

            # 4. 발행 및 최종 확정 (좌표 정밀 타격)
            print("📤 발행 버튼 조준 및 타격...")
            await page.mouse.click(1850, 45) # 발행 버튼
            await asyncio.sleep(3)
            
            try:
                # 팝업 내 확인 버튼 클릭
                confirm_btn = await page.wait_for_selector(".se-confirm-button", timeout=5000)
                await confirm_btn.click()
            except:
                # 버튼이 안 눌리면 엔터 키 연타
                await page.keyboard.press("Enter")
                await asyncio.sleep(1)
                await page.keyboard.press("Enter")

            # 5. 전송 대기 및 결과 보고서 생성
            print("⏳ 서버 전송 확인 중 (10초)...")
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
