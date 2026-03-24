import requests
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# 깃허브 Secret 환경 변수 로드
API_KEY = os.environ.get('NL_API_KEY')
NAVER_ID = "parkbs669" # 사령관님 ID
NAVER_PW = os.environ.get('NAVER_PASSWORD')

def send_mail(content):
    if not NAVER_PW:
        print("❌ 오류: NAVER_PASSWORD 환경 변수를 찾을 수 없습니다.")
        return

    send_email = f"{NAVER_ID}@naver.com"
    recv_email = "parkbs669@naver.com" # 수신 메일 주소
    
    msg = MIMEMultipart()
    msg['Subject'] = f"🎾 [범 SF 알리미] {datetime.now().strftime('%Y-%m-%d')} 신착 도서 소식"
    msg['From'] = send_email
    msg['To'] = recv_email
    msg.attach(MIMEText(content, 'plain'))
    
    try:
        # 네이버 SMTP 서버 연결
        with smtplib.SMTP_SSL("smtp.naver.com", 465) as server:
            server.login(NAVER_ID, NAVER_PW)
            server.sendmail(send_email, recv_email, msg.as_string())
        print("📧 사령관님 메일함으로 전송 성공!")
    except Exception as e:
        print(f"❌ 메일 발송 실패: {e}")

def get_new_sf_books():
    url = "https://www.nl.go.kr/NL/search/openApi/search.do" # 국립중앙도서관 API
    headers = {'User-Agent': 'Mozilla/5.0'}
    params = {
        'key': API_KEY, 
        'kwd': 'SF 소설', # SF 소설 검색
        'category': '도서',
        'sort': 'date', 
        'apiType': 'json', 
        'pageNum': 1, 
        'pageSize': 10
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        data = response.json()
        items = data.get('result', [])

        if not items:
            return "📅 오늘 새로운 SF 소설 정보가 없습니다."

        mail_body = f"사령관님, 오늘의 SF 신작 리스트입니다.\n\n"
        for idx, item in enumerate(items, 1):
            # HTML 태그 제거 및 텍스트 정리
            title = item.get('titleInfo').replace('<span class="searching_txt">', '').replace('</span>', '')
            mail_body += f"{idx}. {title}\n"
            mail_body += f"   - 저자: {item.get('authorInfo')}\n"
            mail_body += f"   - 출판: {item.get('pubInfo')}\n"
            mail_body += "-" * 40 + "\n"
        
        return mail_body
    except Exception as e:
        return f"❗ 데이터 가져오기 오류: {e}"

if __name__ == "__main__":
    result_content = get_new_sf_books()
    print(result_content)
    send_mail(result_content)
