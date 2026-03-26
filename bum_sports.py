name: 🎾 Bum Sports Auto Posting

on:
  schedule:
    - cron: '15 0 * * *'   # 매일 한국 시간(KST) 오전 9:15 자동 실행
  workflow_dispatch:      # 사령관님께서 수동으로 즉시 실행 가능

jobs:
  build_and_run:
    runs-on: ubuntu-latest

    steps:
      - name: 📥 코드 체크아웃
        uses: actions/checkout@v4

      - name: 🐍 Python 설정 (3.11)
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: 📦 필수 패키지 및 Playwright 설치
        run: |
          python -m pip install --upgrade pip
          pip install playwright
          playwright install chromium
          playwright install-deps

      - name: 🚀 bum_sports.py 실행 (정보 수집 및 포스팅)
        env:
          NID_AUT: ${{ secrets.NID_AUT }}
          NID_SES: ${{ secrets.NID_SES }}
        run: python bum_sports.py

      - name: 📸 결과물 PNG 직접 업로드
        if: always() # 실패하더라도 스크린샷은 무조건 업로드하여 보고함
        uses: actions/upload-artifact@v4
        with:
          name: bum-sports-final-report  # 결과물 이름
          path: final_report.png         # bum_sports.py에서 생성한 파일명과 일치
          retention-days: 1              # 저장 공간 절약을 위해 1일 후 자동 삭제
          if-no-files-found: warn        # 파일이 없을 경우 경고 메시지 출력
