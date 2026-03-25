import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def run():
    async with async_playwright() as p:
        # ❗ 깃허브 서버에서는 headless=True 여야만 작동합니다.
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        # ✅ 쿠키 주입 (Secrets에 등록한 NID_AUT, NID_SES 사용)
        cookies = [
            {'name': 'NID_AUT', 'value': os.environ.get('NID_AUT'), 'domain': '.naver.com', 'path': '/'},
            {'name': 'NID_SES', 'value': os.environ.get('NID_SES'), 'domain': '.naver.com', 'path': '/'},
        ]

        # NID_JKL이 있다면 추가 (세션 강화)
        if os.environ.get('NID_JKL'):
            cookies.append({'name': 'NID_JKL', 'value': os.environ.get('NID_JKL'), 'domain': '.naver.com', 'path': '/'})

        await context.add_cookies(cookies)
        page = await context.new_page()

        try:
            print("🚀 [전략] 쿠키 주입 침투 개시")
            # 네이버 메인에서 세션 활성화
            await page.goto("https://www.naver.com", wait_until="networkidle")
            await asyncio.sleep(3)

            # 로그인 여부 체크 (URL에 nidlogin이 보이면 쿠키가 만료된 것)
            if "nidlogin" in page.url:
                print("❌ [실패] 쿠키 만료됨 (PC 브라우저에서 다시 복사하세요)")
                return

            print("✅ [성공] 쿠키 로그인 유효 확인")

            # 글쓰기 페이지 직접 이동
            print("📝 에디터 진입 중...")
            await page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}", wait_until="networkidle")

            # iframe 안전 접근 (mainFrame 찾기)
            frame = None
            for i in range(15): # 대기 시간을 조금 더 넉넉히
                frame = page.frame(name="mainFrame")
                if frame:
                    break
                await asyncio.sleep(1)

            if not frame:
                print("❌ [실패] iframe(mainFrame) 진입 불가")
                return

            print("✅ 에디터 진입 성공")

            title = f"🎾 [BUM Sports] {datetime.now().strftime('%Y-%m-%d')} 최종 테스트"
            content = "사령관님, 쿠키 주입 방식으로 마침내 보안망을 뚫고 성공했습니다!"

            # 제목 입력
            await frame.wait_for_selector("textarea.se-title-input")
            await frame.fill("textarea.se-title-input", title)
            await asyncio.sleep(1)

            # 본문 입력
            await frame.click(".se-main-container")
            await asyncio.sleep(1)
            await page.keyboard.type(content, delay=50) # 사람처럼 보이게 타이핑 딜레이 추가
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
