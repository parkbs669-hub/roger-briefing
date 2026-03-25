import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

# ===== 설정 (사령관님 정보) =====
NAVER_ID = "parkbs669"
NAVER_PW = os.environ.get('NAVER_PASSWORD')

async def debug_elements(target):
    """[디버깅] 현재 화면(또는 프레임)에 어떤 요소가 있는지 리포트"""
    print("\n" + "="*60)
    print("🔍 [데이터 판독] 현재 에디터 구성 요소 수색")
    print("="*60)
    
    # Textarea 수색
    textareas = await target.query_selector_all("textarea")
    print(f"📝 Textarea 개수: {len(textareas)}")
    for i, ta in enumerate(textareas):
        cls = await ta.get_attribute("class")
        ph = await ta.get_attribute("placeholder")
        print(f"  [{i}] class={cls}, placeholder={ph}")
    
    # 에디터 박스(contenteditable) 수색
    editables = await target.query_selector_all("[contenteditable='true']")
    print(f"✏️ 입력 가능 영역(Editable) 개수: {len(editables)}")
    
    print("="*60 + "\n")

async def main():
    async with async_playwright() as p:
        # 실제 브라우저와 똑같이 보이도록 설정
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale='ko-KR'
        )
        
        page = await context.new_page()
        
        try:
            # 1️⃣ 단계: 로그인 (보안 문자 회피를 위해 직접 입력 방식 사용)
            print("🔐 Step 1: 네이버 로그인 시도")
            await page.goto("https://nid.naver.com/nidlogin.login")
            await asyncio.sleep(2)
            
            await page.fill("#id", NAVER_ID)
            await asyncio.sleep(1)
            await page.fill("#pw", NAVER_PW)
            await asyncio.sleep(1)
            await page.click("#log\\.login")
            
            print("⏳ 로그인 처리 대기 (7초)...")
            await asyncio.sleep(7)
            
            if "nidlogin" in page.url:
                print("❌ 로그인 실패: 보안 문자(CAPTCHA) 또는 아이디 확인 필요")
                await page.screenshot(path="error_screenshot.png")
                return
            print("✅ 로그인 성공!")

            # 2️⃣ 단계: 에디터 접속 및 프레임 침투
            print("\n📝 Step 2: 블로그 에디터 진입")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="domcontentloaded")
            
            print("⏳ 에디터 로딩 대기 (10초)...")
            await asyncio.sleep(10)

            # [핵심] mainFrame 찾기
            main_frame = page.frame(name="mainFrame")
            target = main_frame if main_frame else page
            if main_frame:
                print("🖼️ mainFrame(iframe) 내부로 진입했습니다.")
            else:
                print("📱 프레임이 없는 다이렉트 에디터 구조입니다.")

            # [핵심] 도움말 팝업 제거 (사진에서 확인된 방해물)
            try:
                close_btn = await target.query_selector(".se-help-panel-close-button, .help_close, button[class*='close']")
                if close_btn:
                    await close_btn.click()
                    print("🛡️ 도움말 창을 성공적으로 닫았습니다.")
                    await asyncio.sleep(2)
            except:
                print("⚠️ 도움말 창이 발견되지 않았습니다.")

            # 데이터 디버깅 실행
            await debug_elements(target)

            # 3️⃣ 단계: 제목 입력
            print("✍️ Step 3: 제목 작성")
            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 통합 리포트"
            
            title_input = await target.query_selector("textarea.se-title-input, .se-title-input")
            if title_input:
                await title_input.click()
                await asyncio.sleep(1)
                await page.keyboard.type(title)
                print("✅ 제목 입력 완료")
            else:
                print("❌ 제목 칸을 찾을 수 없습니다. 강제 입력을 시도합니다.")
                await page.keyboard.press("Tab") # 제목 칸으로 이동 시도
                await page.keyboard.type(title)

            # 4️⃣ 단계: 본문 입력
            print("\n✍️ Step 4: 본문 작성")
            content = "사령관님, 디버깅과 침투 로직이 결합된 통합 코드로 마침내 미션을 완수했습니다!\n이 글이 보인다면 승리한 것입니다."
            
            # 본문 영역 클릭 (Tab 키 활용이 가장 안정적)
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=30)
            print("✅ 본문 작성 완료")

            # 5️⃣ 단계: 발행
            print("\n📤 Step 5: 최종 발행")
            publish_menu = await target.query_selector(".se-publish-button")
            if publish_menu:
                await publish_menu.click()
                await asyncio.sleep(2)
                
                confirm_btn = await target.query_selector(".se-confirm-button")
                if confirm_btn:
                    await confirm_btn.click()
                    print("🏁🏁🏁 [미션 클리어] 포스팅이 완료되었습니다!")
                    await asyncio.sleep(5)
                else:
                    print("⚠️ 최종 확인 버튼을 찾지 못했습니다.")
            else:
                print("⚠️ 발행 메뉴 버튼을 찾지 못했습니다.")

        except Exception as e:
            print(f"\n❌ 최종 오류 발생: {e}")
            await page.screenshot(path="error_screenshot.png", full_page=True)
            print("📸 스크린샷이 저장되었습니다.")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    if not NAVER_PW:
        print("❌ NAVER_PASSWORD 환경변수가 설정되지 않았습니다.")
        exit(1)
    asyncio.run(main())
