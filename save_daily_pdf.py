# 일일 브리핑 데이터를 수집해 Downloads 폴더에 PDF로 저장
import os, sys, datetime

# 필수 환경변수 세팅 (이메일 발송 없이 PDF만 저장)
os.environ.setdefault("PUBLIC_DATA_API_KEY", "")
os.environ.setdefault("NAVER_CLIENT_ID",     "")
os.environ.setdefault("NAVER_CLIENT_SECRET", "")
os.environ["NAVER_ADDRESS"]  = "parkbs669@gmail.com"
os.environ["NAVER_PASSWORD"] = "test"

import Daily_Report_Briefing as D
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

pdfmetrics.registerFont(TTFont("Malgun", r"C:\Windows\Fonts\malgun.ttf"))

DOWNLOADS = r"C:\Users\박범서\Downloads"
KST = datetime.timezone(datetime.timedelta(hours=9))
today_kst = datetime.datetime.now(KST)
today_str  = today_kst.strftime("%Y%m%d")
today_disp = today_kst.strftime("%Y년 %m월 %d일")


def text_to_pdf(text: str, out_path: str, title: str):
    c = canvas.Canvas(out_path, pagesize=A4)
    w, h = A4
    margin_x, margin_top, margin_bot = 50, 60, 50
    x = margin_x
    y = h - margin_top

    # 제목
    c.setFont("Malgun", 13)
    c.drawString(x, y, title)
    y -= 22
    c.setFont("Malgun", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(x, y, f"생성일시: {today_disp}")
    c.setFillColorRGB(0, 0, 0)
    y -= 18
    c.line(x, y, w - margin_x, y)
    y -= 14

    font_size, line_h, max_chars = 8, 12, 110
    c.setFont("Malgun", font_size)

    for para in text.split("\n"):
        # 섹션 헤더 강조
        if para.startswith("## "):
            y -= 6
            c.setFont("Malgun", 10)
            c.setFillColorRGB(0.1, 0.2, 0.6)
            para_text = para[3:]
        elif para.startswith("### "):
            c.setFont("Malgun", 9)
            c.setFillColorRGB(0.2, 0.4, 0.2)
            para_text = para[4:]
        elif para.startswith("| "):
            c.setFont("Malgun", 7)
            c.setFillColorRGB(0, 0, 0)
            para_text = para
            max_chars = 130
        else:
            c.setFont("Malgun", font_size)
            c.setFillColorRGB(0, 0, 0)
            para_text = para
            max_chars = 110

        # 긴 줄 자동 줄바꿈
        while len(para_text) > max_chars:
            c.drawString(x, y, para_text[:max_chars])
            para_text = "  " + para_text[max_chars:]
            y -= line_h
            if y < margin_bot:
                c.showPage()
                c.setFont("Malgun", font_size)
                c.setFillColorRGB(0, 0, 0)
                y = h - margin_top

        c.drawString(x, y, para_text)
        y -= line_h

        if y < margin_bot:
            c.showPage()
            c.setFont("Malgun", font_size)
            c.setFillColorRGB(0, 0, 0)
            y = h - margin_top

    c.save()
    print(f"✅ PDF 저장: {out_path}")


print(f"🚀 {today_disp} 일일 브리핑 데이터 수집 중...")
print("  - PubMed 논문 수집...")
pubmed  = D.collect_pubmed()
print(f"    → {len(pubmed)}건")
print("  - 네이버 뉴스 수집...")
news    = D.collect_naver_news()
print(f"    → {len(news)}건")
print("  - 나라장터 입찰 수집...")
g2b     = D.collect_g2b()
print(f"    → {len(g2b)}건")
print("  - 질병관리청 수집...")
kdca    = D.collect_kdca()
print(f"    → {len(kdca)}건")
print("  - 식약처 출하승인 수집...")
mfds    = D.collect_mfds()
print(f"    → {len(mfds)}건")
print("  - 심평원 약가 수집...")
hira    = D.collect_hira()
print(f"    → {len(hira)}건")

data = {"G2B": g2b, "NEWS": news, "PUBMED": pubmed,
        "KDCA": kdca, "MFDS": mfds, "HIRA": hira}

print("📄 마크다운 리포트 생성 중...")
md = D.build_markdown_report(data, today_disp)

out = os.path.join(DOWNLOADS, f"데일리브리핑_{today_str}.pdf")
text_to_pdf(md, out, f"📊 데일리 브리핑 — {today_disp}")

print("완료!")
