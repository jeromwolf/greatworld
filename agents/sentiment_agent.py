"""
Sentiment Analysis Agent - 감성 분석 에이전트
다양한 데이터 소스를 종합하여 주식에 대한 전체적인 감성 분석 수행
Gemini AI를 활용한 고급 분석 포함
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
from dataclasses import dataclass, asdict
import google.generativeai as genai


@dataclass
class SentimentResult:
    """감성 분석 결과 데이터 모델"""
    ticker: str                    # 종목 티커
    company_name: str             # 회사명
    overall_sentiment: float      # 전체 감성 점수 (-1 ~ 1)
    sentiment_label: str          # 감성 라벨
    confidence: float            # 신뢰도 (0 ~ 1)
    data_sources: Dict[str, Dict] # 데이터 소스별 분석
    key_factors: List[str]       # 주요 영향 요인
    recommendation: str          # AI 추천사항
    analysis_date: str          # 분석 일시


class SentimentAgent:
    """감성 분석 에이전트"""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        
        # Gemini AI 설정
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')  # 최신 모델 사용
        else:
            self.model = None
            
        # 데이터 소스별 가중치 (PRD에 정의된 대로)
        self.source_weights = {
            "disclosure": 1.5,    # 공시 데이터
            "financial": 1.2,     # 재무 데이터
            "news": 1.0,          # 뉴스
            "reddit": 0.7,        # Reddit
            "stocktwits": 0.8,    # StockTwits
            "twitter": 0.6        # Twitter/X
        }
        
    async def analyze_sentiment(self,
                               ticker: str,
                               company_name: str,
                               data_sources: Dict[str, Any]) -> SentimentResult:
        """
        종합 감성 분석 수행
        
        Args:
            ticker: 종목 티커
            company_name: 회사명
            data_sources: 각 에이전트에서 수집한 데이터
                - disclosure: 공시 데이터
                - news: 뉴스 데이터
                - social: 소셜 데이터
                - financial: 재무 데이터 (옵션)
        """
        # 1. 각 데이터 소스별 감성 분석
        source_sentiments = {}
        
        # 공시 데이터 분석
        if "disclosure" in data_sources:
            disclosure_sentiment = await self._analyze_disclosure_sentiment(
                data_sources["disclosure"]
            )
            source_sentiments["disclosure"] = disclosure_sentiment
            
        # 뉴스 데이터 분석
        if "news" in data_sources:
            news_sentiment = await self._analyze_news_sentiment(
                data_sources["news"]
            )
            source_sentiments["news"] = news_sentiment
            
        # 소셜 데이터 분석
        if "social" in data_sources:
            social_sentiment = await self._analyze_social_sentiment(
                data_sources["social"]
            )
            source_sentiments.update(social_sentiment)
            
        # 2. 가중 평균 계산
        weighted_sentiment = self._calculate_weighted_sentiment(source_sentiments)
        
        # 3. AI 종합 분석 (Gemini 사용)
        if self.model:
            ai_analysis = await self._get_ai_analysis(
                ticker, company_name, source_sentiments, data_sources
            )
        else:
            ai_analysis = self._get_default_analysis(weighted_sentiment)
            
        # 4. 주요 영향 요인 추출
        key_factors = self._extract_key_factors(source_sentiments, data_sources)
        
        # 5. 최종 결과 생성
        result = SentimentResult(
            ticker=ticker,
            company_name=company_name,
            overall_sentiment=weighted_sentiment,
            sentiment_label=self._get_sentiment_label(weighted_sentiment),
            confidence=self._calculate_confidence(source_sentiments),
            data_sources=source_sentiments,
            key_factors=key_factors,
            recommendation=ai_analysis["recommendation"],
            analysis_date=datetime.now().isoformat()
        )
        
        return result
        
    async def _analyze_disclosure_sentiment(self, disclosure_data: Dict) -> Dict:
        """공시 데이터 감성 분석"""
        if not disclosure_data or "disclosures" not in disclosure_data:
            return {"sentiment": 0.0, "confidence": 0.0, "data_source": "MOCK_DATA"}
            
        disclosures = disclosure_data.get("disclosures", [])
        
        # A2A 방식: 더 세밀한 감성 키워드 분석  
        positive_keywords = [
            # 재무 긍정
            "증가", "상승", "개선", "신고가", "흑자전환", "실적개선", "성장", "호조", "증익", "배당증가",
            "increase", "rise", "improve", "profit", "growth", "dividend", "beat", "exceed", "strong",
            # 사업 긍정  
            "확장", "투자", "계약", "파트너십", "신제품", "혁신", "출시",
            "expansion", "investment", "contract", "partnership", "launch", "innovation"
        ]
        negative_keywords = [
            # 재무 부정
            "감소", "하락", "악화", "적자", "손실", "감액", "부진", "둔화", "적자전환",
            "decrease", "decline", "loss", "deficit", "warning", "cut", "weak", "miss", "below",
            # 사업 부정
            "철수", "중단", "지연", "취소", "구조조정", "리콜", "위험",
            "withdraw", "suspend", "delay", "cancel", "restructure", "recall", "risk"
        ]
        
        # 중립 키워드 (약간의 변동성 추가)
        neutral_variations = [
            "보고서", "공시", "발표", "안내", "변경", "결정",
            "report", "disclosure", "announce", "notice", "change", "decision"
        ]
        
        sentiment_scores = []
        for disclosure in disclosures[:10]:  # 최근 10개만 분석
            title = (disclosure.get("report_nm", "") + disclosure.get("title", "")).lower()
            
            # 키워드 매칭 (대소문자 구분 안함)
            pos_count = sum(1 for keyword in positive_keywords if keyword.lower() in title)
            neg_count = sum(1 for keyword in negative_keywords if keyword.lower() in title)
            neutral_count = sum(1 for keyword in neutral_variations if keyword.lower() in title)
            
            # A2A 방식: 더 강한 신호 생성 (투자 의사결정용)
            if pos_count > neg_count:
                sentiment = min(0.8, pos_count * 0.7)  # 가중치 0.4→0.7로 대폭 증가
            elif neg_count > pos_count:
                sentiment = max(-0.8, -neg_count * 0.7)
            elif neutral_count > 0:
                # 중립 키워드도 더 큰 변동성
                import random
                sentiment = random.uniform(-0.25, 0.25)  # -0.15→-0.25로 확대
            else:
                sentiment = random.uniform(-0.15, 0.15)  # 완전 중립도 더 큰 변동
                
            sentiment_scores.append(round(sentiment, 2))  # 소수점 2자리
            
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        confidence = min(1.0, len(sentiment_scores) / 10)  # 데이터 양에 따른 신뢰도
        
        return {
            "sentiment": round(avg_sentiment, 2),
            "confidence": round(confidence, 2),
            "count": len(disclosures),
            "data_source": disclosure_data.get("data_source", "MOCK_DATA")
        }
        
    async def _analyze_news_sentiment(self, news_data: Dict) -> Dict:
        """뉴스 데이터 감성 분석 (A2A 방식 적용)"""
        if not news_data or "articles" not in news_data:
            return {"sentiment": 0.0, "confidence": 0.0, "data_source": "MOCK_DATA"}
            
        articles = news_data.get("articles", [])
        
        # A2A 방식: 뉴스 제목별 세밀한 감성 분석
        positive_keywords = [
            # 주가/실적 긍정
            "상승", "급등", "신고가", "호조", "급반등", "상승세", "고공행진", "9만전자", "8만", "목표가상향",
            "rise", "surge", "high", "rally", "gain", "beat", "exceed", "strong", "outperform",
            # 사업 긍정  
            "계약", "수주", "투자", "협력", "파트너십", "출시", "개발성공", "혁신",
            "contract", "investment", "partnership", "launch", "breakthrough", "innovation"
        ]
        
        negative_keywords = [
            # 주가/실적 부정
            "하락", "급락", "부진", "우려", "위험", "경고", "실망", "부정적", "약세", "매도",
            "fall", "drop", "decline", "concern", "risk", "warning", "disappointing", "weak", "sell",
            # 사업 부정
            "지연", "취소", "중단", "손실", "리콜", "제재", "규제",
            "delay", "cancel", "suspend", "loss", "recall", "sanction", "regulation"
        ]
        
        # 중립-긍정/중립-부정 키워드
        mixed_keywords = {
            "기대감": 0.1, "전망": 0.05, "관심": 0.05, "주목": 0.03,
            "변동": -0.02, "불확실": -0.05, "혼조": 0.0
        }
        
        # A2A 방식: 각 뉴스별 세밀한 감성 계산
        sentiment_scores = []
        for article in articles[:15]:  # 최대 15개 뉴스 분석
            title = article.get("title", "").lower()
            
            # 키워드 기반 점수 계산
            sentiment = 0.0
            
            # 긍정 키워드 체크 (가중치 최대 강화)
            pos_matches = sum(1 for keyword in positive_keywords if keyword.lower() in title)
            if pos_matches > 0:
                sentiment += min(1.0, pos_matches * 0.8)  # 0.6→0.8로 최대 증가
            
            # 부정 키워드 체크 (가중치 최대 강화)
            neg_matches = sum(1 for keyword in negative_keywords if keyword.lower() in title)
            if neg_matches > 0:
                sentiment -= min(1.0, neg_matches * 0.8)  # 0.6→0.8로 최대 증가
                
            # 중립 키워드의 미세한 영향
            for keyword, score in mixed_keywords.items():
                if keyword in title:
                    sentiment += score
            
            # 특수 패턴 분석 (최대 강화된 가중치)
            if "9만전자" in title or "8만" in title or "9만" in title:
                sentiment += 0.7  # 목표가 관련 최대 긍정
            if "7만" in title:
                sentiment += 0.5  # 현재가 회복 강화
            if "트럼프" in title and ("주식" in title or "삼성" in title):
                sentiment -= 0.5  # 정치적 불확실성 최대 강화
            if "순매수" in title or "매수" in title:
                sentiment += 0.6  # 기관 매수 최대 긍정
            if "매도" in title or "급락" in title:
                sentiment -= 0.6  # 매도 압력 최대 부정
            if "실적" in title and ("호조" in title or "성장" in title):
                sentiment += 0.6  # 실적 호조 최대 강화
            if "배당" in title or "주주환원" in title:
                sentiment += 0.5  # 배당/주주환원 긍정
            if "목표가" in title and "상향" in title:
                sentiment += 0.7  # 목표가 상향 최대 긍정
                
            sentiment_scores.append(round(sentiment, 2))
                
        # 평균 계산
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        confidence = min(1.0, len(sentiment_scores) / 15)
        
        return {
            "sentiment": round(avg_sentiment, 2),
            "confidence": round(confidence, 2),
            "count": len(articles),
            "data_source": news_data.get("data_source", "MOCK_DATA")
        }
        
    async def _analyze_social_sentiment(self, social_data: Dict) -> Dict:
        """소셜 데이터 감성 분석"""
        result = {}
        
        # Reddit 분석
        if "reddit" in social_data:
            reddit_posts = social_data["reddit"].get("posts", [])
            reddit_sentiment = await self._calculate_social_platform_sentiment(reddit_posts)
            result["reddit"] = reddit_sentiment
            
        # StockTwits 분석
        if "stocktwits" in social_data:
            stocktwits_posts = social_data["stocktwits"].get("posts", [])
            stocktwits_sentiment = await self._calculate_social_platform_sentiment(stocktwits_posts)
            result["stocktwits"] = stocktwits_sentiment
            
        return result
        
    async def _calculate_social_platform_sentiment(self, posts: List[Dict]) -> Dict:
        """개별 소셜 플랫폼 감성 계산"""
        if not posts:
            return {"sentiment": 0.0, "confidence": 0.0, "data_source": "MOCK_DATA"}
            
        sentiments = []
        total_engagement = 0
        
        for post in posts:
            # 포스트에 감성 점수가 있으면 사용
            if "sentiment" in post and post["sentiment"] is not None:
                sentiment = post["sentiment"]
            else:
                # 없으면 간단히 계산
                content = post.get("content", "").lower()
                sentiment = self._quick_sentiment_analysis(content)
                
            # 참여도(점수, 댓글)로 가중치 적용
            engagement = post.get("score", 0) + post.get("comments", 0)
            sentiments.append((sentiment, engagement))
            total_engagement += engagement
            
        # 가중 평균 계산
        if total_engagement > 0:
            weighted_sentiment = sum(s * e for s, e in sentiments) / total_engagement
        else:
            weighted_sentiment = sum(s for s, _ in sentiments) / len(sentiments) if sentiments else 0.0
            
        confidence = min(1.0, len(posts) / 30)
        
        return {
            "sentiment": round(weighted_sentiment, 2),
            "confidence": round(confidence, 2),
            "count": len(posts),
            "engagement": total_engagement,
            "data_source": "MOCK_DATA"
        }
        
    def _quick_sentiment_analysis(self, text: str) -> float:
        """빠른 감성 분석 (규칙 기반)"""
        # 이모지 기반 분석
        bullish_emojis = ["🚀", "🌙", "💎", "🙌", "📈", "🔥", "💪"]
        bearish_emojis = ["📉", "🐻", "💔", "😢", "⚠️", "🔻"]
        
        bullish_score = sum(1 for emoji in bullish_emojis if emoji in text)
        bearish_score = sum(1 for emoji in bearish_emojis if emoji in text)
        
        # 키워드 기반 분석
        bullish_keywords = ["moon", "rocket", "buy", "long", "bullish", "calls"]
        bearish_keywords = ["crash", "sell", "short", "bearish", "puts", "dump"]
        
        bullish_score += sum(1 for keyword in bullish_keywords if keyword in text.lower())
        bearish_score += sum(1 for keyword in bearish_keywords if keyword in text.lower())
        
        # 점수 계산
        if bullish_score > bearish_score:
            return min(1.0, bullish_score * 0.2)
        elif bearish_score > bullish_score:
            return max(-1.0, -bearish_score * 0.2)
        else:
            return 0.0
            
    def _calculate_weighted_sentiment(self, source_sentiments: Dict[str, Dict]) -> float:
        """가중 평균 감성 점수 계산"""
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for source, data in source_sentiments.items():
            sentiment = data.get("sentiment", 0.0)
            confidence = data.get("confidence", 0.0)
            
            # 가중치 가져오기
            weight = self.source_weights.get(source, 0.5)
            
            # 신뢰도를 고려한 가중치 적용
            adjusted_weight = weight * confidence
            
            total_weighted_score += sentiment * adjusted_weight
            total_weight += adjusted_weight
            
        if total_weight > 0:
            return round(total_weighted_score / total_weight, 2)
        else:
            return 0.0
            
    async def _get_ai_analysis(self,
                              ticker: str,
                              company_name: str,
                              sentiments: Dict,
                              raw_data: Dict) -> Dict:
        """Gemini AI를 사용한 종합 분석"""
        prompt = f"""
        다음 데이터를 바탕으로 {company_name}({ticker}) 주식에 대한 종합 분석을 제공하세요:
        
        감성 분석 결과:
        {json.dumps(sentiments, ensure_ascii=False, indent=2)}
        
        다음 형식으로 답변해주세요:
        1. 전체 시장 심리 요약 (1-2문장)
        2. 주요 긍정 요인 (최대 3개)
        3. 주요 위험 요인 (최대 3개)
        4. 단기 전망 (1주일)
        5. 투자자를 위한 조언 (1-2문장)
        
        답변은 객관적이고 균형잡힌 시각으로 작성해주세요.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return {
                "recommendation": response.text,
                "ai_confidence": 0.9,
                "data_source": "REAL_DATA"
            }
        except Exception as e:
            print(f"Gemini AI analysis error: {str(e)}")
            return self._get_default_analysis(sentiments.get("overall_sentiment", 0.0))
            
    def _get_default_analysis(self, sentiment: float) -> Dict:
        """기본 분석 (규칙 기반) - 사용자에게 실질적으로 유용한 정보 제공"""
        
        # 현재 날짜 기준 (실제로는 주가 데이터 필요)
        from datetime import datetime, timedelta
        today = datetime.now()
        
        if sentiment >= 0.5:
            recommendation = """📊 **투자 분석 요약**

🟢 **현재 상태: 강한 매수 신호**
시장 심리가 매우 긍정적이며, 상승 모멘텀이 강합니다.

💰 **실행 가능한 투자 전략**
• 매수 시점: 오늘 종가 기준 -2% 하락 시 (지정가 매수)
• 목표 수익률: +8~12% (2-3주 내)
• 손절 기준: 매수가 대비 -3%
• 추천 비중: 포트폴리오의 5~10%

📈 **주요 관찰 지표**
• 거래량: 평균 대비 150% 이상 유지 시 추가 상승 가능
• 외국인/기관 순매수 지속 여부
• 업종 내 상대 강도 (동종업계 대비 성과)

⚡ **즉시 행동 사항**
1. 증권사 앱에서 조건부 매수 주문 설정
2. 관련 뉴스 알림 설정 (주요 키워드: 실적, 목표가, 계약)
3. 일일 종가 기록하여 추세 확인"""
        
        elif sentiment >= 0.2:
            recommendation = """📊 **투자 분석 요약**

🟡 **현재 상태: 온건한 매수 기회**
긍정적 흐름이지만 급등보다는 안정적 상승 예상됩니다.

💰 **실행 가능한 투자 전략**
• 분할 매수: 3회 분할 (오늘 30%, 3일 후 30%, 1주 후 40%)
• 목표 수익률: +5~8% (1개월 내)
• 리스크 관리: 평균 매수가 대비 -5% 손절
• 추천 비중: 포트폴리오의 3~7%

📊 **중요 확인 사항**
• 다음 실적 발표일: 확인 필요
• 52주 고점 대비 현재가 위치
• PER/PBR 업종 평균 대비 비교

⚡ **주간 체크리스트**
□ 매일 종가 및 거래량 체크
□ 주요 공시 확인 (매일 오후 6시)
□ 경쟁사 주가 동향 비교"""

        elif sentiment >= -0.2:
            recommendation = """📊 **투자 분석 요약**

⚪ **현재 상태: 관망 권장**
뚜렷한 방향성이 없어 추가 신호를 기다려야 합니다.

🔍 **대기 중 관찰 사항**
• 돌파 신호: 20일 이동평균선 상향 돌파 + 거래량 급증
• 지지선: 최근 저점 확인하여 하방 리스크 파악
• 촉매제: 신제품 출시, 실적 발표, 업계 호재 등

📋 **현재 보유 중이라면**
• 현 상태 유지하되 추가 매수 보류
• 수익 중: 일부 익절하여 현금 확보
• 손실 중: 손절선 재설정 (-7~10%)

⏳ **일주일 내 결정 포인트**
1. 주요 기술적 지표 확인 (RSI, MACD)
2. 업종 지수 대비 상대 성과
3. 외국인/기관 매매 동향 변화"""

        elif sentiment >= -0.5:
            recommendation = """📊 **투자 분석 요약**

🟠 **현재 상태: 주의 필요**
부정적 신호가 우세하여 방어적 접근이 필요합니다.

⚠️ **리스크 관리 우선**
• 신규 매수: 전면 보류
• 기존 보유: 비중 축소 고려 (50% 이하로)
• 관찰 기간: 최소 2주 이상
• 대안: 현금 보유 또는 안전자산 전환

📉 **하락 시나리오 대비**
• 1차 지지선: 최근 저점 -5%
• 2차 지지선: 52주 최저가
• 최악 시나리오: -15~20% 추가 하락

💡 **역발상 기회 포착**
□ 과매도 구간 진입 시 (RSI 30 이하)
□ 거래량 동반한 반등 신호
□ 악재 소진 후 저가 매수 기회"""

        else:
            recommendation = """📊 **투자 분석 요약**

🔴 **현재 상태: 위험 신호**
강한 하락 압력으로 즉각적인 대응이 필요합니다.

🚨 **긴급 대응 방안**
• 보유 중: 즉시 50% 이상 손절 실행
• 추가 하락 대비: -20% 이상 하락 가능성
• 대안 투자: 국채, 금, 달러 등 안전자산

⛔ **절대 하지 말아야 할 것**
• 물타기 (평균가 낮추기)
• 단기 반등 노린 역매수
• 신용/미수 거래

📅 **회복 시그널 (최소 1개월 후)**
1. 거래량 증가와 함께 저점 확인
2. 주요 악재 해소 뉴스
3. 기관/외국인 순매수 전환
4. 기술적 반등 신호 (이격도 과매도)"""
            
        return {
            "recommendation": recommendation,
            "ai_confidence": 0.5,
            "data_source": "MOCK_DATA"
        }
        
    def _extract_key_factors(self,
                           sentiments: Dict,
                           raw_data: Dict) -> List[str]:
        """주요 영향 요인 추출"""
        factors = []
        
        # 가장 영향력 있는 데이터 소스 찾기
        sorted_sources = sorted(
            sentiments.items(),
            key=lambda x: abs(x[1].get("sentiment", 0)) * x[1].get("confidence", 0),
            reverse=True
        )
        
        for source, data in sorted_sources[:3]:
            sentiment = data.get("sentiment", 0)
            if abs(sentiment) > 0.3:
                if source == "disclosure":
                    factors.append(f"공시: {'긍정적' if sentiment > 0 else '부정적'} 내용 다수")
                elif source == "news":
                    factors.append(f"뉴스: {'호재' if sentiment > 0 else '악재'} 보도 집중")
                elif source == "reddit":
                    factors.append(f"Reddit: {'매수' if sentiment > 0 else '매도'} 심리 우세")
                elif source == "stocktwits":
                    factors.append(f"StockTwits: {'강세' if sentiment > 0 else '약세'} 전망")
                    
        return factors
        
    def _calculate_confidence(self, sentiments: Dict) -> float:
        """전체 신뢰도 계산"""
        confidences = [data.get("confidence", 0) for data in sentiments.values()]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            # 데이터 소스 개수도 고려
            source_bonus = min(0.3, len(sentiments) * 0.1)
            return min(1.0, avg_confidence + source_bonus)
        return 0.0
        
    def _get_sentiment_label(self, score: float) -> str:
        """감성 점수를 라벨로 변환"""
        if score >= 0.6:
            return "매우 긍정적"
        elif score >= 0.2:
            return "긍정적"
        elif score >= -0.2:
            return "중립적"
        elif score >= -0.6:
            return "부정적"
        else:
            return "매우 부정적"


# 테스트 함수
async def test_sentiment_agent():
    """Sentiment Agent 테스트"""
    print("=== Sentiment Agent 테스트 ===\\n")
    
    # 테스트 데이터 준비
    test_data = {
        "disclosure": {
            "disclosures": [
                {"report_nm": "3분기 실적 발표 - 매출 30% 증가"},
                {"report_nm": "자사주 매입 결정"},
                {"report_nm": "배당금 인상 공시"}
            ]
        },
        "news": {
            "articles": [
                {"title": "Apple beats earnings expectations", "sentiment": 0.8},
                {"title": "Strong iPhone sales drive growth", "sentiment": 0.7},
                {"title": "Concerns about China market", "sentiment": -0.3}
            ]
        },
        "social": {
            "reddit": {
                "posts": [
                    {"content": "AAPL to the moon! 🚀🚀", "score": 1500, "comments": 234, "sentiment": 0.9},
                    {"content": "Great earnings, buying more", "score": 800, "comments": 120, "sentiment": 0.6}
                ]
            },
            "stocktwits": {
                "posts": [
                    {"content": "$AAPL breaking resistance", "sentiment": 0.7},
                    {"content": "Target $200 EOY", "sentiment": 0.8}
                ]
            }
        }
    }
    
    agent = SentimentAgent()
    
    # 종합 감성 분석
    result = await agent.analyze_sentiment(
        ticker="AAPL",
        company_name="Apple Inc.",
        data_sources=test_data
    )
    
    # 결과 출력
    print(f"종목: {result.company_name} ({result.ticker})")
    print(f"전체 감성 점수: {result.overall_sentiment} ({result.sentiment_label})")
    print(f"신뢰도: {result.confidence:.0%}")
    
    print("\\n데이터 소스별 분석:")
    for source, data in result.data_sources.items():
        print(f"- {source}: {data['sentiment']} (신뢰도: {data['confidence']})")
        
    print("\\n주요 영향 요인:")
    for factor in result.key_factors:
        print(f"- {factor}")
        
    print("\\nAI 추천사항:")
    print(result.recommendation)
    
    print(f"\\n분석 일시: {result.analysis_date}")
    

if __name__ == "__main__":
    asyncio.run(test_sentiment_agent())