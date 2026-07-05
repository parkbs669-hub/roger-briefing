# 주간 브리핑 테스트 실행 — parkbs669@naver.com 단독 발송
import os, sys

# 환경변수 주입 (테스트용)
os.environ["DEEPSEEK_API_KEY"] = "sk-efa05a2776ab490cacfd2d65ee61e8af"
os.environ["NEWS_API_KEY"]     = "080ad328fd004e36bfe0d2037e11e65d"
os.environ["NAVER_ADDRESS"]  = "parkbs669@gmail.com"
os.environ["NAVER_PASSWORD"] = "Bs1809bs01*"

TEST_RECIPIENT = ["parkbs669@gmail.com"]

target = sys.argv[1] if len(sys.argv) > 1 else "both"

if target in ("weekly", "both"):
    import Weekly_Report_Briefing as W
    W.RECIPIENTS = TEST_RECIPIENT
    print("=== [테스트] 주간 업무 보고서 생성 중... ===")
    report = W.get_weekly_report()
    print("=== 이메일 발송 중 (수신: parkbs669@naver.com) ===")
    W.send_email(report)

if target in ("academic", "both"):
    import weekly_academic_briefing as A
    A.RECIPIENTS = TEST_RECIPIENT
    print("=== [테스트] 주간 학술 브리핑 생성 중... ===")
    briefing = A.get_weekly_briefing()
    print("=== 이메일 발송 중 (수신: parkbs669@naver.com) ===")
    A.send_email(briefing)

print("✅ 테스트 완료")
