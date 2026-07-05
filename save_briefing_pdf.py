# 주간 브리핑을 PDF로 생성해 Downloads 폴더에 저장
import os, sys, datetime
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

os.environ["DEEPSEEK_API_KEY"] = "sk-efa05a2776ab490cacfd2d65ee61e8af"
os.environ["NEWS_API_KEY"]     = "080ad328fd004e36bfe0d2037e11e65d"
os.environ["NAVER_ADDRESS"]    = "parkbs669@gmail.com"
os.environ["NAVER_PASSWORD"]   = "parkbs669@gmail.com"

DOWNLOADS = r"C:\Users\박범서\Downloads"
FONT_PATH = r"C:\Windows\Fonts\malgun.ttf"
pdfmetrics.registerFont(TTFont("Malgun", FONT_PATH))

KST = datetime.timezone(datetime.timedelta(hours=9))
today_str = datetime.datetime.now(KST).strftime("%Y%m%d")


def text_to_pdf(text: str, out_path: str, title: str):
    c = canvas.Canvas(out_path, pagesize=A4)
    w, h = A4
    margin = 50
    x = margin
    y = h - margin
    line_h = 14
    font_size = 9

    c.setFont("Malgun", 12)
    c.drawString(x, y, title)
    y -= line_h * 2

    c.setFont("Malgun", font_size)
    for para in text.split("\n"):
        # 긴 줄 자동 줄바꿈
        max_chars = 90
        while len(para) > max_chars:
            c.drawString(x, y, para[:max_chars])
            para = para[max_chars:]
            y -= line_h
            if y < margin:
                c.showPage()
                c.setFont("Malgun", font_size)
                y = h - margin
        c.drawString(x, y, para)
        y -= line_h
        if y < margin:
            c.showPage()
            c.setFont("Malgun", font_size)
            y = h - margin

    c.save()
    print(f"✅ PDF 저장: {out_path}")


target = sys.argv[1] if len(sys.argv) > 1 else "both"

if target in ("weekly", "both"):
    import Weekly_Report_Briefing as W
    print("=== 주간 업무 보고서 생성 중... ===")
    report = W.get_weekly_report()
    out = os.path.join(DOWNLOADS, f"주간업무보고_{today_str}.pdf")
    text_to_pdf(report, out, f"폐렴구균 백신 주간 업무 보고 ({today_str})")

if target in ("academic", "both"):
    import weekly_academic_briefing as A
    print("=== 주간 학술 브리핑 생성 중... ===")
    briefing = A.get_weekly_briefing()
    out = os.path.join(DOWNLOADS, f"주간학술브리핑_{today_str}.pdf")
    text_to_pdf(briefing, out, f"폐렴구균 주간 학술 브리핑 ({today_str})")

print("완료!")
