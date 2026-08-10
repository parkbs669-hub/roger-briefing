"""데일리 브리핑 이메일 테스트 전용 실행 파일.

원본 Daily_Report_Briefing.py의 수집·리포트 생성 로직을 그대로 사용한다.
다만 메일은 TEST_RECIPIENT 한 명에게만 보내고, Vault 커밋은 하지 않는다.
"""

import os

import Daily_Report_Briefing as briefing


TEST_RECIPIENT = "parkbs669@naver.com"


class TestMIMEMultipart(briefing.MIMEMultipart):
    """테스트 메일 제목에 식별 문구를 붙인다."""

    def __setitem__(self, name, value):
        if name.lower() == "subject":
            value = f"🧪 [테스트] {value}"
        super().__setitem__(name, value)


def main():
    # GitHub Secret REPORT_RECIPIENTS 값과 무관하게 테스트 수신자만 사용한다.
    os.environ["REPORT_RECIPIENTS"] = TEST_RECIPIENT

    # 테스트 실행이 실제 Vault 일일 리포트를 덮어쓰지 않도록 직접 커밋은 비활성화한다.
    os.environ.pop("GH_PAT", None)

    # 원본 모듈이 이 클래스를 사용해 테스트 제목을 만들도록 교체한다.
    briefing.MIMEMultipart = TestMIMEMultipart

    print(f"🧪 테스트 브리핑 시작: {TEST_RECIPIENT} 한 곳에만 발송합니다.")
    briefing.main()


if __name__ == "__main__":
    main()
