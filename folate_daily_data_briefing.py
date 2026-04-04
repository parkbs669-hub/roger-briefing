import os
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from folate_g2b_collector import collect_g2b_notices
from folate_naver_news_collector import collect_naver_news
from folate_pubmed_collector import collect_pneumo_papers
from folate_kdca_collector import collect_kdca
from folate_mfds_collector import collect_mfds
from folate_hira_collector import collect_hira

# 범용 표 생성기 (링크 처리 로직 복구)
def make_table(items, columns, col_keys):
    if not items: return "<p style='color:#7f8c8d; font-size:13px;'>관련 데이터가 없습니다.</p>"
    th_html = "".join([f"<th style='padding:8px; text-align:left; background:#f4f6f7; border-bottom:2px solid #bdc3c7;'>{col}</th>" for col in columns])
    tr_html = ""
    for i in items:
        tds = []
        for key in col_keys:
            val = str(i.get(key, ''))
            # ✅ 링크 텍스트 맞춤 설정 (공고보기, PubMed 등)
            if key == 'bidNtceUrl' and val:
                val = f"<a href='{val}' style='color:#3498db; text-decoration:none;'>공고보기</a>"
            elif key == 'link' and val:
                link_text = "기사보기" if "naver.com" in val else "PubMed" if "pubmed" in val else "확인하기"
                val = f"<a href='{val}' style='color:#3498db; text-decoration:none;'>{link_text}</a>"
            
            tds.append(f"<td style='padding:8px; border-bottom:1px solid #ecf0f1; font-size:13px;'>{val}</td>")
        tr_html += f"<tr>{''.join(tds)}</tr>"
    return f"<table width='100%' style='border-collapse:collapse;'><thead><tr>{th_html}</tr></thead><tbody>{tr_html}</tbody></table>"

# 일반 섹션 빌더
def build_section(title, all_data, columns, col_keys, icon, color):
    v_data = [i for i in all_data if i.get('category') == '백신']
    n_data = [i for i in all_data if i.get('category') == '영양제']
    
    html = f"""
    <div style='margin-bottom:30px; border:1px solid #dcdde1; border-radius:8px; overflow:hidden; background:#ffffff;'>
        <div style='background:{color}; color:#ffffff; padding:12px 15px; font-size:16px; font-weight:bold;'>
            {icon} {title}
        </div>
        <div style='padding:15px;'>
            <h4 style='margin:0 0 10px 0; color:#2c3e50; border-left:4px solid {color}; padding-left:8px;'>💉 백신 섹션</h4>
            {make_table(v_data, columns, col_keys)}
            
            <h4 style='margin:25px 0 10px 0; color:#27ae60; border-left:4px solid #27ae60; padding-left:8px;'>🤰 임산부 영양제 섹션</h4>
            {make_table(n_data, columns, col_keys)}
        </div>
    </div>"""
    return html

# ✅ 질병관리청 전용 카드 UI 빌더 (총 건수 포함)
def build_kdca_section(title, all_data, icon, color):
    v_data = [i for i in all_data if i.get('category') == '백신']
    n_data = [i for i in all_data if i.get('category') == '영양제']
    
    def calc_total(items):
        return sum(int(i.get("resultVal", i.get("patntCnt", "0"))) for i in items if str(i.get("resultVal", i.get("patntCnt", ""))).isdigit())

    v_total = calc_total(v_data)
    n_total = calc_total(n_data)
    total_sum = v_total + n_total

    def make_cards(items):
        if not items: return "<p style='color:#7f8c8d; font-size:13px;'>관련 데이터가 없습니다.</p>"
        cards = ""
        for i in items:
            disease = i.get("icdNm", i.get("diseaseNm", ""))
            group = i.get("icdGroupNm", "")
            count = i.get("resultVal", i.get("patntCnt", ""))
            url = "https://dportal.kdca.go.kr/pot/is/inftnsdsEDW.do"
            cards += f"""
            <div style='display:inline-block; background:#fff5f5; border:1px solid #ffcccc; border-left:4px solid #e74c3c; border-radius:6px; padding:12px 16px; margin:4px; min-width:200px; vertical-align:top;'>
                <div style='font-size:15px; font-weight:bold; color:#c0392b;'>{disease}</div>
                <div style='font-size:12px; color:#888; margin:4px 0;'>{group} | 2026년 누계</div>
                <div style='font-size:22px; font-weight:bold; color:#e74c3c;'>{count}<span style='font-size:13px; color:#888;'>건</span></div>
                <div style='margin-top:6px;'><a href='{url}' style='font-size:11px; color:#1a73e8; text-decoration:none;'>질병관리청 상세보기 -></a></div>
            </div>"""
        return f"<div style='padding:4px;'>{cards}</div>"

    html = f"""
    <div style='margin-bottom:30px; border:1px solid #dcdde1; border-radius:8px; overflow:hidden; background:#ffffff;'>
        <div style='background:{color}; color:#ffffff; padding:12px 15px; font-size:16px; font-weight:bold;'>
            {icon} {title}
            <span style='float:right; background:rgba(255,255,255,0.3); padding:2px 10px; border-radius:12px; font-size:13px;'>{total_sum}건</span>
        </div>
        <div style='padding:15px;'>
            <h4 style='margin:0 0 10px 0; color:#2c3e50; border-left:4px solid {color}; padding-left:8px;'>💉 백신 섹션 (총 {v_total}건)</h4>
            {make_cards(v_data)}
            
            <h4 style='margin:25px 0 10px 0; color:#27ae60; border-left:4px solid #27ae60; padding-left:8px;'>🤰 임산부 영양제 섹션 (총 {n_total}건)</h4>
            {make_cards(n_data)}
            <p style='color:#aaa; font-size:11px; margin-top:12px;'>※ 출처: 질병관리청 감염병포털 (방역통합정보시스템 전수신고 기준)</p>
        </div>
    </div>"""
    return html

def main():
    today = datetime.date.today().strftime("%Y년 %m월 %d일")
    print(f"데이터 수집 시작: {today}")
    
    data = {
        "G2B": collect_g2b_notices(),
        "NEWS": collect_naver_news(),
        "PUBMED": collect_pneumo_papers(),
        "KDCA": collect_kdca(),
        "MFDS": collect_mfds(),
        "HIRA": collect_hira()
    }
    
    html_body = f"""
    <html><body style='font-family:"Malgun Gothic", sans-serif; padding:20px; background:#f0f2f5; color:#333;'>
        <div style='max-width:800px; margin:0 auto;'>
            <div style='text-align:center; margin-bottom:30px;'>
                <h1 style='color:#2c3e50; margin-bottom:5px;'>📊 통합 인텔리전스 브리핑</h1>
                <p style='color:#7f8c8d; font-size:14px;'>{today} 기준 자동화 리포트</p>
            </div>
            
            {build_section("네이버 최신 뉴스", data['NEWS'], ['제목', '날짜', '링크'], ['title', 'pubDate', 'link'], "📰", "#3498db")}
            {build_section("나라장터 입찰공고", data['G2B'], ['공고명', '기관명', '공고일', '링크'], ['bidNtceNm', 'ntceInsttNm', 'bidNtceDt', 'bidNtceUrl'], "🏛️", "#e67e22")}
            {build_section("학술 논문 (PubMed)", data['PUBMED'], ['논문 제목', '저널', '발행년도', '링크'], ['title', 'journal', 'year', 'link'], "🔬", "#9b59b6")}
            {build_kdca_section("질병관리청 감염병 현황", data['KDCA'], "🏥", "#e74c3c")}
            {build_section("식약처 국가출하승인", data['MFDS'], ['제품명', '제조사', '승인일'], ['SAMPLE_TYPE', 'MANUF_ENTP_NAME', 'RESULT_TIME'], "💊", "#1abc9c")}
            {build_section("심평원 약가 정보", data['HIRA'], ['제품명', '제약사', '상한금액(원)'], ['itmNm', 'entrpsNm', 'mxDpc'], "💰", "#f1c40f")}
            
            <div style='text-align:center; padding:20px; color:#95a5a6; font-size:12px; border-top:1px solid #bdc3c7;'>
                본 메일은 GitHub Actions를 통해 자동 발송되었습니다.
            </div>
        </div>
    </body></html>
    """

    addr = os.environ.get("NAVER_ADDRESS")
    pw = os.environ.get("NAVER_PASSWORD")
    
    if not addr or not pw: return

    msg = MIMEMultipart()
    msg["Subject"] = f"📊 [백신+영양제] 통합 인텔리전스 브리핑 - {today}"
    msg["From"] = addr
    msg["To"] = addr
    msg.attach(MIMEText(html_body, "html"))
    
    try:
        with smtplib.SMTP_SSL("smtp.naver.com", 465) as s:
            s.login(addr, pw)
            s.send_message(msg)
        print("✅ 브리핑 이메일 발송 완료!")
    except Exception as e:
        print(f"❌ 이메일 발송 오류: {e}")

if __name__ == "__main__":
    main()
