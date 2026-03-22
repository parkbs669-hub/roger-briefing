"""
Claude AI 종합 분석 에이전트 v3
네이버 뉴스 추가 + 국내 현황 반영
"""
import anthropic
import os
import datetime

def analyze_with_claude(g2b, pubmed, kdca, mfds, hira, naver_news=None):
    """Claude로 수집 데이터 종합 분석"""
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY", "")
    )
    today = datetime.date.today().strftime("%Y년 %m월 %d일")

    # 나라장터
    g2b_text = "【나라장터 입찰공고】\n"
    if g2b:
        for item in g2b[:5]:
            price = item.get("presmptPrce", "0") or "0"
            try: price_fmt = f"{int(float(price)):,}원"
            except: price_fmt = "미정"
            g2b_text += (f"- {item.get('bidNtceNm','-')}\n"
                        f"  발주: {item.get('ntceInsttNm','-')} | "
                        f"마감: {item.get('bidClseDt','-')} | "
                        f"금액: {price_fmt}\n")
    else:
        g2b_text += "최근 7일 신규 공고 없음\n"

    # 네이버 뉴스
    news_text = "【국내 최신 뉴스 (네이버)】\n"
    if naver_news:
        for item in naver_news[:10]:
            news_text += (f"- {item.get('title','-')}\n"
                         f"  {item.get('description','')[:100]}...\n"
                         f"  날짜: {item.get('pubDate','')}\n")
    else:
        news_text += "수집된 뉴스 없음\n"

    # PubMed
    pub_text = "【최신 논문 (PubMed)】\n"
    if pubmed:
        for p in pubmed[:5]:
            pub_text += (f"- {p.get('title','-')}\n"
                        f"  ({p.get('journal','-')}, {p.get('year','-')})\n"
                        f"  초록: {p.get('abstract','')[:200]}...\n")
    else:
        pub_text += "최근 30일 신규 논문 없음\n"

    # 질병관리청
    kdca_text = "【감염병 발생현황 (질병관리청)】\n"
    kdca_text += "\n".join([str(i) for i in kdca[:5]]) if kdca else "수집 데이터 없음\n"

    # 식약처
    mfds_text = "【국가출하승인 (식약처)】\n"
    mfds_text += "\n".join([str(i) for i in mfds[:5]]) if mfds else "최근 신규 출하승인 없음\n"

    # 심평원
    hira_text = "【약가/급여 현황 (심평원)】\n"
    hira_text += "\n".join([str(i) for i in hira[:5]]) if hira else "수집 데이터 없음\n"

    prompt = f"""당신은 폐렴구균 백신 시장 전문 분석가입니다.
오늘 날짜: {today}

===== 국내 폐렴구균 백신 현황 (반드시 숙지) =====

1. 캡박시브 (PCV21) - 한국MSD
   - 2025년 8월 27일 식약처 허가
   - 2026년 3월 3일 전국 출시 완료 ← 이미 출시됨!
   - 18세 이상 성인 전용, 1회 접종
   - 가격: 약 18~20만원
   - NIP 미편입 (향후 논의 예정)
   - 국내 성인 IPD 원인 혈청형 74% 커버

2. 프리베나20 (PCV20) - 화이자
   - 소아 NIP 적용 중 (2025.10~)
   - 성인 유료 접종 가능

3. 프로디악스23 (PPSV23) - 한국MSD
   - 65세 이상 NIP 무료 접종 중

===== 이번 주 수집된 실시간 데이터 =====

{news_text}

{g2b_text}

{pub_text}

{kdca_text}

{mfds_text}

{hira_text}

===== 브리핑 작성 지침 =====

위 데이터를 종합 분석하여 아래 형식으로 작성하세요.
특히 네이버 뉴스의 최신 정보를 적극 반영하세요.

# 💉 폐렴구균 백신 주간 인텔리전스 브리핑
## 날짜: {today}

## 📋 이번 주 핵심 요약
(가장 중요한 3가지를 2~3문장으로)

## 📰 국내 최신 뉴스 동향
(네이버 뉴스 기반 이번 주 주요 소식)

## 🏛 나라장터 입찰 동향
(입찰공고 분석, 마감 임박 강조)

## 🦠 감염병 발생 현황
(폐렴구균 환자 발생 트렌드)

## 💊 식약처 출하승인 동향
(신규 출하 및 공급 분석)

## 💰 급여/약가 현황
(보험 급여 및 약가 변동)

## 🔬 최신 논문 동향
(주요 논문 요약 및 국내 적용성)

## 📊 시장 현황 요약
(PCV20 vs PCV21 경쟁 구도)

## 💡 이번 주 액션 아이템
(실무자가 이번 주 해야 할 일 3가지)

## ➡️ 다음 주 주목할 사항"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        print(f"  Claude 오류: {e}")
        return f"AI 분석 실패: {e}"
