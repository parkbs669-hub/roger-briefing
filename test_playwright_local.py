"""
🧪 로컬 테스트용 Playwright 간단 버전
VPN 없이 기본 동작만 확인하는 스크립트
"""

import os
import asyncio
from playwright.async_api import async_playwright

NAVER_ID = "parkbs669"
NAVER_PW = os.environ.get('NAVER_PASSWORD')

async def test_playwright_basic():
    """Playwright 기본 동작 테스트"""
    
    print("🧪 Playwright 로컬 테스트 시작")
    print("=" * 60)
    
    async with async_playwright() as p:
        # Chromium 시작 (headless=False로 GUI 보기)
        browser = await p.chromium.launch(headless=False)
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080},
        )
        
        page = await context.new_page()
        
        try:
            # 1. 테스트: 구글 접속
            print("\n✅ Step 1: Google 접속")
            await page.goto("https://www.google.com")
            await asyncio.sleep(2)
            title = await page.title()
            print(f"   페이지 제목: {title}")
            
            # 2. 테스트: 요소 찾기
            print("\n✅ Step 2: 검색창 찾기")
            search_box = await page.query_selector('[name="q"]')
            if search_box:
                print("   ✓ 검색창 발견!")
                await search_box.fill("Playwright")
                await asyncio.sleep(1)
            
            # 3. 테스트: 마우스 움직임
            print("\n✅ Step 3: 마우스 움직임")
            await page.mouse.move(500, 500)
            await asyncio.sleep(0.5)
            await page.mouse.move(800, 300)
            print("   ✓ 마우스 움직임 완료")
            
            # 4. 테스트: 스크롤
            print("\n✅ Step 4: 페이지 스크롤")
            await page.evaluate("window.scrollBy(0, 500)")
            await asyncio.sleep(1)
            print("   ✓ 스크롤 완료")
            
            # 5. 테스트: IP 확인
            print("\n✅ Step 5: 현재 IP 확인")
            try:
                await page.goto("https://ipinfo.io")
                await asyncio.sleep(2)
                ip_text = await page.text_content("body")
                print(f"   IP 정보: {ip_text[:100]}...")
            except:
                print("   ⚠️ IP 조회 실패")
            
            # 6. 테스트: 네이버 접속 (실제 로그인은 안 함)
            print("\n✅ Step 6: 네이버 접속")
            await page.goto("https://www.naver.com")
            await asyncio.sleep(2)
            title = await page.title()
            print(f"   페이지 제목: {title}")
            
            print("\n" + "=" * 60)
            print("🎉 모든 테스트 완료!")
            print("=" * 60)
            
            # 15초 동안 브라우저 열어둠 (결과 확인용)
            await asyncio.sleep(15)
            
        except Exception as e:
            print(f"\n❌ 에러: {e}")
        
        finally:
            await context.close()
            await browser.close()

async def test_naver_login():
    """네이버 로그인 테스트 (실제 로그인)"""
    
    if not NAVER_PW:
        print("❌ NAVER_PASSWORD 환경변수 미설정")
        return
    
    print("\n🔐 네이버 로그인 테스트 시작")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
        )
        
        page = await context.new_page()
        
        try:
            print("\n📍 로그인 페이지 접속 중...")
            await page.goto("https://nid.naver.com/nidlogin.login")
            await asyncio.sleep(3)
            
            print("📝 ID 입력 중...")
            await page.fill("#id", NAVER_ID)
            await asyncio.sleep(1)
            
            print("🔑 PW 입력 중...")
            await page.fill("#pw", NAVER_PW)
            await asyncio.sleep(1)
            
            print("🖱️ 로그인 버튼 클릭...")
            await page.click("#log\\.login")
            await asyncio.sleep(5)
            
            print(f"📄 현재 URL: {page.url}")
            
            if "nidlogin" in page.url:
                print("❌ 로그인 실패")
            else:
                print("✅ 로그인 성공!")
            
            # 30초 동안 브라우저 유지
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"❌ 에러: {e}")
        
        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    import sys
    
    print("🎯 Playwright 로컬 테스트 메뉴")
    print("=" * 60)
    print("1. 기본 기능 테스트 (구글, IP 확인 등)")
    print("2. 네이버 로그인 테스트")
    print("=" * 60)
    
    choice = input("\n선택 (1 또는 2): ").strip()
    
    if choice == "1":
        asyncio.run(test_playwright_basic())
    elif choice == "2":
        asyncio.run(test_naver_login())
    else:
        print("잘못된 선택입니다.")
