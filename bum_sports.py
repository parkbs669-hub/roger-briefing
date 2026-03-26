import os
import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def get_tennis_trends(page):
    """네이버에서 최신 테니스 정보를 수집합니다."""
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
            
    return "\n".join(unique_items) if unique_items else "📍 최신 소식 분석 중"

async def post_blog():
    async with async_playwright() as p:
        # 가상 환경에서도 안정적인 브라우저 구동 설정
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        
        # 쿠키 주입 (Secrets 설정 확인 필수)
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

            # 2. 에디터 접속
            print(f"🚀 [범 스포츠] 통합 리포트 작성 시작 (ID: {NAVER_ID})...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(15)

            # 3. 도움말 및 방해 요소 강제 제거 (JS 방식)
            print("🛡️ 방해 요소(도움말/팝업) 제거 중...")
            await page.evaluate("() => { document.querySelectorAll('.se-help-panel, .se-popup-guide, .se-viewer-help').forEach(el => el.remove()); }")
            await asyncio.sleep(2)
            
            # 4. 리포트 내용 입력
            today_str = datetime.now().strftime("%Y년 %m월 %d일")
            title = f"🎾 [범 스포츠] {today_str} 테니스 트렌드 리포트"
            content = (
                f"사령관님, 오늘 수집된 최신 테니스 이슈입니다!\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{trends_report}\n\n"
                f"본 포스팅은 좌표 방식의 한계를 극복한 JS 강제 실행 시스템으로 발행되었습니다."
            )

            # 데이터 입력 (Tab 전략)
            await page.mouse.click(960, 300)
            await page.keyboard.press("Tab")
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab")
            await page.keyboard.type(content, delay=30)
            print("✅ 데이터 입력 완료 및 버튼 활성화 대기...")
            await asyncio.sleep(5)

            # 5. [핵심] 1단계 발행 버튼 - 사령관님의 JS 유도탄 투하
            print("📤 1단계: 발행 메뉴 JS 강제 클릭...")
            result1 = await page.evaluate("""
                () => {
                    const selectors = ['.se-publish-button', 'button[class*="publish"]', 'button:has-text("발행")'];
                    for (const sel of selectors) {
                        const btn = document.querySelector(sel) || Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('발행'));
                        if (btn) { btn.click(); return '클릭 성공: ' + sel; }
                    }
                    return '버튼 미포착';
                }
            """)
            print(f"📢 1단계 결과: {result1}")
            await asyncio.sleep(5) # 팝업창 로딩 대기

            # 6. 2단계 최종 발행 확정 - JS 강제 클릭
            print("📤 2단계: 최종 발행 확정 JS 강제 클릭...")
            result2 = await page.evaluate("""
                () => {
                    const confirmSelectors = ['.se-confirm-button', 'button:has-text("발행하기")', '.btn_ok'];
                    for (const sel of confirmSelectors) {
                        const btn = document.querySelector(sel) || Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('발행'));
                        if (btn) { btn.click(); return '최종 발행 클릭 성공'; }
                    }
                    return '최종 버튼 미포착';
                }
            """)
            print(f"📢 2단계 결과: {result2}")

            # 7. 서버 전송 대기 및 결과 보고
            print("⏳ 서버 응답 대기 (20초)...")
            await asyncio.sleep(20)
            await page.screenshot(path="final_report.png", full_page=True)
            print("🏁🏁🏁 작전 종료! 블로그를 확인하십시오.")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="final_report.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
