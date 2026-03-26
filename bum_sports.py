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
        
        aut_val = str(os.environ.get('NID_AUT') or "").strip()
        ses_val = str(os.environ.get('NID_SES') or "").strip()
        await context.add_cookies([
            {'name': 'NID_AUT', 'value': aut_val, 'domain': '.naver.com', 'path': '/'},
            {'name': 'NID_SES', 'value': ses_val, 'domain': '.naver.com', 'path': '/'}
        ])

        page = await context.new_page()

        try:
            trends = await get_tennis_trends(page)
            print(f"🚀 [범 스포츠] 리포트 작성 시작 (ID: {NAVER_ID})...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")
            await asyncio.sleep(15)

            # 🛡️ 1. 방해 요소(도움말/팝업)를 아예 뿌리째 뽑아버립니다.
            await page.evaluate("() => { document.querySelectorAll('.se-help-panel, .se-popup-guide, .se-viewer-help').forEach(el => el.remove()); }")
            
            # 2. 내용 입력
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d')} 테니스 정밀 리포트"
            content = f"사령관님, 오늘 수집된 테니스 이슈입니다!\n\n{trends}\n\n정밀 유도 시스템에 의한 자동 포스팅입니다."

            await page.mouse.click(960, 300)
            await page.keyboard.press("Tab")
            await page.keyboard.type(title, delay=50)
            await page.keyboard.press("Tab")
            await page.keyboard.type(content, delay=30)
            print("✅ 데이터 입력 및 버튼 활성화 대기...")
            await asyncio.sleep(5) # 버튼이 활성화될 시간을 충분히 줍니다.

            # 🎯 [1단계] 상단 오른쪽 '발행' 버튼 강제 타격
            print("📤 1단계: 상단 '발행' 버튼 강제 실행 중...")
            # '발행'이라는 텍스트를 가진 버튼 중 '클릭 가능한 것'을 찾아 강제로 클릭 명령을 내립니다.
            try:
                await page.evaluate("""() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const publishBtn = btns.find(b => b.innerText.includes('발행') && b.offsetWidth > 0);
                    if (publishBtn) publishBtn.click();
                }""")
                print("🎯 1단계 강제 클릭 명령 전달 완료")
            except Exception as e:
                print(f"⚠️ 1단계 실패, 좌표(1847, 25)로 보조 타격: {e}")
                await page.mouse.click(1847, 25)

            await asyncio.sleep(5) # 팝업창이 뜨길 기다립니다.

            # 🎯 [2단계] 팝업창 내 '발행' 버튼 강제 타격
            print("📤 2단계: 최종 '발행' 확정 명령 전송 중...")
            try:
                await page.evaluate("""() => {
                    const confirmBtns = Array.from(document.querySelectorAll('.se-confirm-button, button'));
                    const finalBtn = confirmBtns.find(b => b.innerText.includes('발행') && b.classList.contains('se-confirm-button'));
                    if (finalBtn) finalBtn.click();
                    else { // 클래스로 못 찾으면 글자로 다시 시도
                        const backupBtn = confirmBtns.reverse().find(b => b.innerText.includes('발행'));
                        if (backupBtn) backupBtn.click();
                    }
                }""")
                print("🏁 최종 발행 명령 성공!")
            except Exception as e:
                print(f"⚠️ 2단계 실패, 엔터 키로 강제 돌파 시도: {e}")
                for _ in range(3):
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(1)

            # 3. 서버 전송 대기 및 결과 보고
            print("⏳ 서버 응답 대기 및 최종 확인 중 (20초)...")
            await asyncio.sleep(20)
            await page.screenshot(path="final_report.png", full_page=True)
            print("🏁🏁🏁 모든 작전 종료! 블로그를 확인하십시오.")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            await page.screenshot(path="final_report.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
