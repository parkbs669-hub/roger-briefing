import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

# ===== 설정 (사령관님 정보) =====
NAVER_ID = "parkbs669"

async def run():
    async with async_playwright() as p:
        # 깃허브 서버(headless) 환경 최적화 실행
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        # ✅ 쿠키 주입 (Secrets에서 가져온 NID_AUT, NID_SES 사용)
        # str()로 감싸서 데이터 형식을 확실히 고정합니다.
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
            print("🚀 [전략] 쿠키 주입 침투 개시...")
            # 네이버 메인 접속으로 세션 유효성 확인
            await page.goto("https://www.naver.com", wait_until="networkidle")
            await asyncio.sleep(3)

            if "nidlogin" in page.url:
                print("❌ [실패] 쿠키가 만료되었습니다. PC에서 다시 복사해 주세요.")
                return

            print("✅ [성공] 쿠키 로그인 유효 확인!")

            # 글쓰기 페이지 직접 이동
            print("📝 에디터 진입 중...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")

            # iframe(mainFrame) 대기 및 전환
            frame = None
            for _ in range(15):
                frame = page.frame(name="mainFrame")
                if frame: break
                await asyncio.sleep(1)

            if not frame:
                print("❌ [실패] 에디터 프레임(mainFrame)을 찾을 수 없습니다.")
                return

            print("✅ 에디터 진입 성공!")

            # 내용 구성
            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 테니스 리포트"
            content = "사령관님, 마침내 쿠키 주입 방식으로 자동 포스팅에 성공했습니다!\n오늘도 즐거운 테니스 되십시오."

            # 제목 입력
            await frame.wait_for_selector("textarea.se-title-input")
            await frame.fill("textarea.se-title-input", title)
            await asyncio.sleep(1)

            # 본문 입력
            await frame.click(".se-main-container")
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=50) # 사람처럼 타이핑
            print("✍️ 본문 작성 완료")

            # 발행 버튼 클릭
            print("📤 발행 및 최종 확인 중...")
            await frame.click("button.se-publish-button")
            await asyncio.sleep(2)
            await frame.click("button.se-confirm-button")

            print("🏁🏁🏁🏁🏁 [미션 클리어] 포스팅 완료!")
            await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
