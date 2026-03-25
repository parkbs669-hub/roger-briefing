import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

# ===== 설정 (사령관님 정보) =====
NAVER_ID = "parkbs669"

async def run():
    async with async_playwright() as p:
        # 깃허브 서버 환경 최적화 실행
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        # ✅ 쿠키 주입 (Secrets에서 가져온 NID_AUT, NID_SES 사용)
        aut_val = str(os.environ.get('NID_AUT') or "").strip()
        ses_val = str(os.environ.get('NID_SES') or "").strip()

        if not aut_val or not ses_val:
            print("❌ [중단] Secrets에 NID_AUT 또는 NID_SES가 등록되지 않았습니다.")
            await browser.close()
            return

        await context.add_cookies([
            {'name': 'NID_AUT', 'value': aut_val, 'domain': '.naver.com', 'path': '/'},
            {'name': 'NID_SES', 'value': ses_val, 'domain': '.naver.com', 'path': '/'}
        ])
        
        page = await context.new_page()

        try:
            print("🚀 [전략] 쿠키 주입 침투 개시 (네트워크 최적화 모드)...")
            
            # [수정] 모든 요소가 뜰 때까지 기다리지 않고 뼈대만 뜨면 진행 (timeout 60초로 확장)
            try:
                await page.goto("https://www.naver.com", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(5) # 세션이 안정화될 시간을 줍니다.
            except Exception as e:
                print(f"⚠️ 네이버 메인 로딩 지연 중 (계속 진행 시도): {e}")

            if "nidlogin" in page.url:
                print("❌ [실패] 쿠키가 만료되었습니다. PC 브라우저(F12)에서 다시 복사해 주세요.")
                return

            print("✅ [성공] 쿠키 로그인 유효 확인!")

            # 글쓰기 페이지 직접 이동 (여기도 60초 인내심 적용)
            print("📝 에디터 진입 시도 중...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", 
                            wait_until="domcontentloaded", timeout=60000)

            # iframe(mainFrame) 대기 및 전환 (최대 40초간 끈질기게 수색)
            frame = None
            for i in range(20):
                frame = page.frame(name="mainFrame")
                if frame: break
                print(f"⏳ 에디터 로딩 대기 중... ({i+1}/20)")
                await asyncio.sleep(2)

            if not frame:
                print("❌ [실패] 에디터 프레임(mainFrame)을 끝내 찾지 못했습니다.")
                return

            print("✅ 에디터 진입 성공!")

            # 내용 구성
            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 자동 브리핑"
            content = "사령관님, 네트워크 지연을 뚫고 마침내 자동 포스팅에 성공했습니다!\n성공 메시지를 보게 되어 기쁩니다."

            # 제목 입력
            await frame.wait_for_selector("textarea.se-title-input", timeout=30000)
            await frame.fill("textarea.se-title-input", title)
            await asyncio.sleep(1)

            # 본문 입력
            await frame.click(".se-main-container")
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=50) 
            print("✍️ 본문 작성 완료")

            # 발행 버튼 클릭
            print("📤 발행 및 최종 확인 중...")
            await frame.click("button.se-publish-button")
            await asyncio.sleep(2)
            await frame.click("button.se-confirm-button")

            print("🏁🏁🏁🏁🏁 [미션 클리어] 포스팅 완료!")
            await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ 최종 오류 발생: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
