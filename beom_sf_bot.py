name: 🚀 Bum Sports Automation

on:
  schedule:
    - cron: '15 0 * * *'   # 매일 09:15 (KST)
    - cron: '45 5 * * *'   # 매일 14:45 (KST)
    - cron: '30 11 * * *'  # 매일 20:30 (KST)
  workflow_dispatch:

jobs:
  run_script:
    runs-on: ubuntu-latest
    
    steps:
      - name: 📥 코드 체크아웃
        uses: actions/checkout@v3

      - name: 🐍 Python 설정
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: 📦 의존성 설치 (Playwright 포함)
        run: |
          python -m pip install --upgrade pip
          pip install playwright
          playwright install chromium
          playwright install-deps

      - name: 🔍 설치 확인 (수정됨)
        run: |
          echo "✅ Python 버전:"
          python --version
          echo ""
          echo "✅ Playwright 설치 확인:"
          python -c "import playwright; print('Playwright is installed ✅')"
          echo ""
          echo "✅ Chromium 설치 확인:"
          playwright show browsers

      - name: 🕐 시간 확인
        run: |
          echo "UTC: $(date -u '+%Y-%m-%d %H:%M:%S')"
          echo "KST: $(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"

      - name: 🚀 bum_sports.py 실행
        env:
          NAVER_PASSWORD: ${{ secrets.NAVER_PASSWORD }}
          VPN_ENABLED: 'false'
        run: python bum_sports.py

      - name: ✅ 성공
        if: success()
        run: echo "🎉 완료! $(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"

      - name: ❌ 실패 시 로그
        if: failure()
        run: |
          echo "⚠️ 실패!"
          echo "확인 사항:"
          echo "1. NAVER_PASSWORD secret 등록 여부"
          echo "2. Playwright 설치 여부"
          echo "3. 네이버 로그인 가능 여부"
