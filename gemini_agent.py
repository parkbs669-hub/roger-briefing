"""
Gemini AI 종합 분석 에이전트
수집된 모든 데이터를 종합하여 브리핑 생성
"""
import google.generativeai as genai
import os
import datetime

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def analyze_with_gemini(g2b_data, pubmed_data):
    """Gemini로 수집 데이터 종합 분석"""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    today = datetime.date.today().strftime("%Y년 %m월 %d일")

    # 나라장터 데이터 정리
    g2b_text = ""
    if g2b_data:
        g2b_text = "【나라장터 입찰공고】\n"
        for item in g2b_data[:5]:
            price = item.get("presmptPrce", "0") or "0"
            try:
                price_fmt = f"{int(float(price)):,}원"
            except:
                price_fmt = "미정"
            g2b_text += f"""
공고명: {item.get('bidNtceNm', '-')}
발주기관: {item.get('ntceInsttNm', '-')}
공고일: {item.get('bidNtceDt', '-')}
마감일: {item.get('bidClseDt', '-')}
추정금액: {price_fmt}
---"""
    else:
        g2b_text = "【나라장터 입찰공고】\n최근 7일간 신규 공고 없음\n"

    # PubMed 데이터 정리
    pubmed_text = ""
    if pubmed_data:
        pubmed_text = "【최신 논문】\n"
        for paper in pubmed_data[:5]:
            pubmed_text += f"""
제목: {paper.get('title', '-')}
저널: {paper.get('journal', '-')} ({paper.get('year', '-')})
저자: {paper.get('authors', '-')}
초록: {paper.get('abstract', '-')}
URL: {paper.get('url', '-')}
---"""
    else:
        pubmed_text = "【최신 논문】\n최근 30일간 신규 논문 없음\n"

    prompt = f"""
당신은 폐렴구균 백신 시장 전문 분석가입니다.
오늘 날짜: {today}

아래 데이터를 분석하여 실무자를 위한 일일 브리핑을 한국어로 작성해주세요.

{g2b_text}

{pubmed_text}

아래 형식으로 작성해주세요:

# 💉 폐렴구균 백신 일일 인텔리전스 브리핑
## 날짜: {today}

## 📋 오늘의 핵심 요약
(가장 중요한 3가지를 2~3문장으로)

## 🏛 나라장터 입찰 동향
(입찰공고 분석 및 시사점)

## 🔬 최신 논문 동향
(논문 요약 및 임상적 의의)

## 💡 오늘의 액션 아이템
(실무자가 오늘 당장 해야 할 일 3가지)

## ➡️ 내일 주목할 사항
(마감 임박 공고, 예정된 이벤트 등)
"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"  Gemini 오류: {e}")
        return f"AI 분석 실패: {e}"
