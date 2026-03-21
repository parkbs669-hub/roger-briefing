"""
Gemini AI 종합 분석 에이전트 (전체 5개 API 통합)
"""
import google.generativeai as genai
import os
import datetime

def analyze_with_gemini(g2b, pubmed, kdca, mfds, hira):
    """5개 API 데이터 종합 분석"""
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
    today = datetime.date.today().strftime("%Y년 %m월 %d일")

    # 나라장터
    g2b_text = "【나라장터 입찰공고】\n"
    if g2b:
        for item in g2b[:5]:
            price = item.get("presmptPrce", "0") or "0"
            try: price_fmt = f"{int(float(price)):,}원"
            except: price_fmt = "미정"
            g2b_text += f"- {item.get('bidNtceNm','-')} | {item.get('ntceInsttNm','-')} | 마감:{item.get('bidClseDt','-')} | {price_fmt}\n"
    else:
        g2b_text += "최근 7일 신규 공고 없음\n"

    # PubMed
    pub_text = "【최신 논문】\n"
    if pubmed:
        for p in pubmed[:5]:
            pub_text += f"- {p.get('title','-')} ({p.get('journal','-')}, {p.get('year','-')})\n"
            pub_text += f"  초록: {p.get('abstract','')[:150]}...\n"
    else:
        pub_text += "최근 30일 신규 논문 없음\n"

    # 질병관리청
    kdca_text = "【감염병 발생현황 (질병관리청)】\n"
    if kdca:
        for item in kdca[:5]:
            kdca_text += f"- {item}\n"
    else:
        kdca_text += "수집된 데이터 없음 (API 확인 필요)\n"

    # 식약처
    mfds_text = "【국가출하승인 (식약처)】\n"
    if mfds:
        for item in mfds[:5]:
            mfds_text += f"- {item}\n"
    else:
        mfds_text += "최근 신규 출하승인 없음\n"

    # 심평원
    hira_text = "【약가/급여 현황 (심평원)】\n"
    if hira:
        for item in hira[:5]:
            hira_text += f"- {item}\n"
    else:
        hira_text += "수집된 데이터 없음 (API 확인 필요)\n"

    prompt = f"""
당신은 폐렴구균 백신 시장 전문 분석가입니다.
오늘 날짜: {today}

아래 5개 공공 데이터를 종합 분석하여 실무자용 일일 브리핑을 한국어로 작성해주세요.

{g2b_text}
{pub_text}
{kdca_text}
{mfds_text}
{hira_text}

아래 형식으로 작성해주세요:

# 💉 폐렴구균 백신 일일 인텔리전스 브리핑
## 날짜: {today}

## 📋 오늘의 핵심 요약
(가장 중요한 3가지를 2~3문장으로)

## 🏛 나라장터 입찰 동향
(입찰공고 분석 및 시사점, 마감 임박 공고 강조)

## 🦠 감염병 발생 현황
(폐렴구균 환자 발생 트렌드 분석)

## 💊 식약처 출하승인 동향
(신규 출하승인 및 시장 공급 분석)

## 💰 급여/약가 현황
(보험 급여 및 약가 변동 분석)

## 🔬 최신 논문 동향
(주요 논문 요약 및 임상적 의의)

## 💡 오늘의 액션 아이템
(실무자가 오늘 당장 해야 할 일 3가지)

## ➡️ 내일 주목할 사항
(마감 임박 공고, 예정 이벤트 등)
"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"  Gemini 오류: {e}")
        return f"AI 분석 실패: {e}"
