import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"

async def post_blog():
    async with async_playwright() as p:
        # GPT 추천 옵션 적용 (자동화 탐지 방지)
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ]
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        # ✅ 우리의 필살기: 깃허브 시크릿 쿠키 주입
        aut_val = str(os.environ.get('NID_AUT') or "").strip()
        ses_val = str(os.environ.get('NID_SES') or "").strip()
        await context.add_cookies([
            {'name': 'NID_AUT', 'value': aut_val, 'domain': '.naver.com', 'path': '/'},
            {'name': 'NID_SES', 'value': ses_val, 'domain': '.naver.com', 'path': '/'}
        ])

        page = await context.new_page()

        try:
            print("🚀 [작전 개시] 융합 코드로 블로그 침투...")
            await page.goto(
                f"https://blog.naver.com/PostWriteForm.naver?blogId={NAVER_ID}",
                wait_until="networkidle"
            )

            # 🔥 GPT의 핵심 비책: iframe(mainFrame)이 나타날 때까지 20번 수색
            frame = None
            for i in range(20):
                frame = page.frame(name="mainFrame")
                if frame:
                    print(f"✅ {i+1}초 만에 mainFrame 진입 성공!")
                    break
                await asyncio.sleep(1)

            if not frame:
                # 프레임이 없는 최신 에디터일 경우를 대비해 page 자체를 타겟으로 설정
                print("⚠️ mainFrame을 찾지 못해 본체 페이지(Page)에서 진행합니다.")
                target = page
            else:
                target = frame

            # 🛡️ 도움말 창 제거 (이게 있으면 클릭이 씹힙니다)
            try:
                close_btn = await target.wait_for_selector(".se-help-panel-close-button, .help_close", timeout=5000)
                await close_btn.click()
                print("🛡️ 도움말 제거 완료")
            except: pass

            # ✍️ 제목 입력 (GPT 방식: textarea.se-title-input)
            title = f"🎾 [범 스포츠] {datetime.now().strftime('%Y-%m-%d %H:%M')} 리포트"
            print(f"✍️ 제목 작성 중: {title}")
            title_box = await target.wait_for_selector("textarea.se-title-input", timeout=15000)
            await title_box.click()
            await title_box.fill(title)

            # ✍️ 본문 입력 (GPT 방식: div.se-main-container)
            print("✍️ 본문 작성 중...")
            content = "사령관님, GPT의 프레임 수색 로직과 우리의 쿠키 기술을 합쳐 성공했습니다!\n테니스 스트링 머신 관리는 정밀함이 생명입니다."
            body = await target.wait_for_selector("div.se-main-container", timeout=15000)
            await body.click()
            await page.keyboard.type(content)

            # 📤 발행 버튼 (GPT 방식)
            print("📤 발행 버튼 탐색...")
            publish_btn = await target.wait_for_selector("button.se-publish-button", timeout=15000)
            await publish_btn.click()
            await asyncio.sleep(2)

            # 최종 확인 버튼
            confirm_btn = await target.wait_for_selector("button.se-confirm-button", timeout=15000)
            await confirm_btn.click()

            print("🏁🏁🏁🏁🏁 [최종 성공] 포스팅 완료!")
            await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ 오류: {e}")
            await page.screenshot(path="error.png", full_page=True)
            print("📸 error.png 저장됨 - 깃허브 Artifacts에서 확인하세요.")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(post_blog())
