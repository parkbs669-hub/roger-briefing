import os,smtplib,datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import anthropic
A=os.environ["ANTHROPIC_API_KEY"]
N=os.environ["NAVER_ADDRESS"]
P=os.environ["NAVER_PASSWORD"]
R="parkbs669@naver.com"
def run():
    c=anthropic.Anthropic(api_key=A)
    t=datetime.date.today().strftime("%Y년 %m월 %d일")
    res=c.messages.create(model="claude-opus-4-5",max_tokens=4000,tools=[{"type":"web_search_20250305","name":"web_search"}],messages=[{"role":"user","content":f"오늘({t}) 폐렴구균 백신 PCV20 PCV21 뉴스를 검색하고 시장동향 임상허가 접종정책 카테고리로 상세 브리핑 작성"}])
    body="".join(b.text for b in res.content if hasattr(b,"text"))
    msg=MIMEMultipart()
    msg["Subject"]=f"[폐렴구균백신] {t} 브리핑"
    msg["From"]=N
    msg["To"]=R
    msg.attach(MIMEText(f"안녕하세요\n\n{t} 브리핑입니다\n\n{body}","plain","utf-8"))
    with smtplib.SMTP_SSL("smtp.naver.com",465) as s:
        s.login(N,P)
        s.sendmail(N,R,msg.as_string())
    print("완료!")
run()
