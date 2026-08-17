"""주간 업무 보고 이메일 테스트 전용 실행 파일.

원본 Weekly_Report_Briefing.py의 수집·작성 로직은 그대로 사용한다.
메일은 TEST_RECIPIENT 한 명에게만 보내며 Vault에는 저장하지 않는다.
"""

import sys

import Weekly_Report_Briefing as report


TEST_RECIPIENT = "parkbs669@naver.com"


class TestMIMEMultipart(report.MIMEMultipart):
    """테스트 메일임을 제목에서 바로 알 수 있게 한다."""

    def __setitem__(self, name, value):
        if name.lower() == "subject":
            value = f"🧪 [테스트] {value}"
        super().__setitem__(name, value)


def main():
    report.RECIPIENTS = [TEST_RECIPIENT]
    report.GH_PAT = ""
    report.MIMEMultipart = TestMIMEMultipart

    print(f"🧪 주간 업무 보고 테스트 시작: {TEST_RECIPIENT} 한 곳에만 발송합니다.")
    generated_report = report.get_weekly_report()

    if not generated_report or generated_report.startswith("(") or len(generated_report.strip()) < 200:
        print(f"⚠️ 보고서 생성에 실패하였거나 내용이 유효하지 않습니다:\n{generated_report}\n발송을 건너뜁니다.")
        sys.exit(1)

    empty_count = generated_report.count("확인된 정보 없음") + generated_report.count("해당 없음")
    if empty_count >= 10 and "※ AI 분석 정보" not in generated_report:
        print(f"⚠️ 보고서 내용이 대부분 비어있습니다 (빈 항목 {empty_count}개). 발송을 건너뜁니다.")
        sys.exit(1)

    report.send_email(generated_report)
    print("✅ 테스트 메일 발송 완료 — Vault 저장은 건너뜁니다.")


if __name__ == "__main__":
    main()
