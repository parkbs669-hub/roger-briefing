"""주간 학술 브리핑 이메일 테스트 전용 실행 파일.

원본 weekly_academic_briefing.py의 수집·작성 로직은 그대로 사용한다.
메일은 TEST_RECIPIENT 한 명에게만 보내며 Vault에는 저장하지 않는다.
"""

import sys

import weekly_academic_briefing as briefing


TEST_RECIPIENT = "parkbs669@naver.com"


class TestMIMEMultipart(briefing.MIMEMultipart):
    """테스트 메일임을 제목에서 바로 알 수 있게 한다."""

    def __setitem__(self, name, value):
        if name.lower() == "subject":
            value = f"🧪 [테스트] {value}"
        super().__setitem__(name, value)


def main():
    briefing.RECIPIENTS = [TEST_RECIPIENT]
    briefing.GH_PAT = ""
    briefing.MIMEMultipart = TestMIMEMultipart

    print(f"🧪 주간 학술 브리핑 테스트 시작: {TEST_RECIPIENT} 한 곳에만 발송합니다.")
    generated_briefing = briefing.get_weekly_briefing()

    empty_count = generated_briefing.count("확인된 정보 없음") + generated_briefing.count("해당 없음")
    if empty_count >= 8 and "※ AI 지식 기반" not in generated_briefing:
        print(f"⚠️ 브리핑 내용이 대부분 비어있습니다 (빈 항목 {empty_count}개). 발송을 건너뜁니다.")
        sys.exit(1)

    briefing.send_email(generated_briefing)
    print("✅ 테스트 메일 발송 완료 — Vault 저장은 건너뜁니다.")


if __name__ == "__main__":
    main()
