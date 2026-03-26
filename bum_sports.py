import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def get_tennis_trends(page):
    print("🔍 테니스 최신 이슈 수집 중...")
    search_url = "https://search.naver.com/search.naver?query=테니스+스트링+추천+후기+교체&nso=so:dd"
    await page.goto(search_url, wait_until="networkidle")
    await asyncio.sleep(3)
    items = await page.locator(".news_tit, .api_txt_lines.total_tit").all_inner_texts()
    unique_items = list(dict.fromkeys([item.strip() for item in items if len(item.strip()) > 5]))
    return "\n".join([f"📍 {i}" for i in unique_items[:5]])

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
            trends = await get_tennis_trends(page)
            print(f"🚀 [범 스포츠] 통합 리포트 작성 시작 (ID: {NAVER_ID})...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            
            # 에디터 로딩 대기 (충분히 15초)
            await asyncio.sleep(15)

            # 🛡️ [강력한 방해물 제거] 사령관님이 보신 '예약 발행 글' 팝업 등을 코드로 직접 삭제
            print("🛡️ 방해물(예약 발행/도움말/팝업) 소거 중...")
            await page.evaluate("""() => {
                // 예약 발행 글, 도움말, 각종 가이드 팝업을 모두 찾아 삭제합니다.
                const popups = document.querySelectorAll('.se-help-panel, .se-popup-guide, .se-viewer-help, [class*="popup"], [class*="layer"]');
                popups.forEach(el => el.remove());
                
                // 만약 '취소'나 '닫기' 버튼이 있다면 강제 클릭
                const closeBtns = Array.from(document.querySelectorAll('button')).filter(b => b.innerText.includes('취소') || b.innerText.includes('닫기'));
                closeBtns.forEach(b => b.click());
            }""")
            await asyncio.sleep(3)
            
            # 📝 본문 작성
            today_str = datetime.now().strftime("%Y년 %m월 %d일")
            title = f"🎾 [범 스포츠] {today_str} 테니스 트렌드 리포트"
            content = f"사령관님, 오늘 수집된 테니스 이슈입니다!\n\n{trends}\n\n시스템 자동 포스팅 미션 수행 중입니다."

            # 본문 영역을 확실히 클릭하여 포커스를 잡습니다.
            await page.mouse.click(960, 500) 
            await page.keyboard.press("Control+A") # 혹시 모를 기존 내용 삭제
            await page.keyboard.press("Backspace")
            
            # 제목/본문 입력
            await page.mouse.click(960, 300)
            await page.keyboard.press("Tab")
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab")
            await page.keyboard.type(content, delay=30)
            print("✅ 리포트 내용 입력 완료")

            # 📤 1단계: 상단 '발행' 버튼 JS 강제 클릭
            print("📤 1단계: 상단 '발행' 버튼 타격 중...")
            await page.evaluate("""() => {
                // '발행' 글자가 정확히 일치하는 상단 버튼만 골라 클릭
                const btns = Array.from(document.querySelectorAll('button'));
                const publishBtn = btns.find(b => b.innerText.trim() === '발행' && b.classList.contains('se-publish-button'));
                if (publishBtn) publishBtn.click();
                else { // 백업: '발행' 포함된 버튼 강제 클릭
                    const backup = btns.find(b => b.innerText.includes('발행') && b.offsetWidth > 0);
                    if (backup) backup.click();
                }
            }""")
            await asyncio.sleep(5)

            # 📤 2단계: 최종 '발행하기' 확인 버튼 JS 강제 클릭
            print("📤 2단계: 최종 발행 확정 명령 전송...")
            await page.evaluate("""() => {
                const confirmBtns = Array.from(document.querySelectorAll('.se-confirm-button, button'));
                const finalBtn = confirmBtns.find(b => b.innerText.includes('발행'));
                if (finalBtn) finalBtn.click();
            }""")

            print("⏳ 서버 응답 대기 및 최종 확인 중 (20초)...")
            await asyncio.sleep(20)
            await page.screenshot(path="final_report.png", full_page=True)
            print("🏁🏁🏁 작전 종료! 이제 블로그를 확인해 보세요.")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="final_report.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
