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
            self.model = genai.GenerativeModel('gemini-pro')
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
        
        # 공시 제목에서 감성 키워드 분석
        positive_keywords = [
            "증가", "상승", "개선", "신고가", "흑자전환", "실적개선",
            "increase", "rise", "improve", "profit", "growth", "dividend"
        ]
        negative_keywords = [
            "감소", "하락", "악화", "적자", "손실", "감액",
            "decrease", "decline", "loss", "deficit", "warning", "cut"
        ]
        
        sentiment_scores = []
        for disclosure in disclosures[:10]:  # 최근 10개만 분석
            title = disclosure.get("report_nm", "") + disclosure.get("title", "")
            
            pos_count = sum(1 for keyword in positive_keywords if keyword in title)
            neg_count = sum(1 for keyword in negative_keywords if keyword in title)
            
            if pos_count > neg_count:
                sentiment = min(1.0, pos_count * 0.3)
            elif neg_count > pos_count:
                sentiment = max(-1.0, -neg_count * 0.3)
            else:
                sentiment = 0.0
                
            sentiment_scores.append(sentiment)
            
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        confidence = min(1.0, len(sentiment_scores) / 10)  # 데이터 양에 따른 신뢰도
        
        return {
            "sentiment": round(avg_sentiment, 2),
            "confidence": round(confidence, 2),
            "count": len(disclosures),
            "data_source": "MOCK_DATA"
        }
        
    async def _analyze_news_sentiment(self, news_data: Dict) -> Dict:
        """뉴스 데이터 감성 분석"""
        if not news_data or "articles" not in news_data:
            return {"sentiment": 0.0, "confidence": 0.0, "data_source": "MOCK_DATA"}
            
        articles = news_data.get("articles", [])
        
        # 이미 감성 점수가 있으면 사용, 없으면 계산
        sentiments = []
        for article in articles:
            if "sentiment" in article and article["sentiment"] is not None:
                sentiments.append(article["sentiment"])
            else:
                # 간단한 규칙 기반 분석
                title = article.get("title", "").lower()
                description = article.get("description", "").lower()
                text = title + " " + description
                
                # 긍정/부정 단어 점수
                positive_words = ["surge", "gain", "rise", "beat", "strong", "upgrade"]
                negative_words = ["fall", "drop", "miss", "weak", "downgrade", "concern"]
                
                pos_score = sum(1 for word in positive_words if word in text)
                neg_score = sum(1 for word in negative_words if word in text)
                
                sentiment = (pos_score - neg_score) * 0.2
                sentiment = max(-1.0, min(1.0, sentiment))
                sentiments.append(sentiment)
                
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        confidence = min(1.0, len(sentiments) / 20)
        
        return {
            "sentiment": round(avg_sentiment, 2),
            "confidence": round(confidence, 2),
            "count": len(articles),
            "data_source": "MOCK_DATA"
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
            return self._get_default_analysis(sentiments.get("overall_sentiment", 0.0))
            
    def _get_default_analysis(self, sentiment: float) -> Dict:
        """기본 분석 (AI 사용 불가 시)"""
        if sentiment >= 0.5:
            recommendation = "⚠️ 모의 데이터 - Gemini API 키가 설정되지 않음\n\n시장 심리가 매우 긍정적입니다. 단기적으로 상승 모멘텀이 예상됩니다."
        elif sentiment >= 0.2:
            recommendation = "⚠️ 모의 데이터 - Gemini API 키가 설정되지 않음\n\n시장 심리가 긍정적입니다. 안정적인 흐름이 예상됩니다."
        elif sentiment >= -0.2:
            recommendation = "⚠️ 모의 데이터 - Gemini API 키가 설정되지 않음\n\n시장 심리가 중립적입니다. 추가적인 모니터링이 필요합니다."
        elif sentiment >= -0.5:
            recommendation = "⚠️ 모의 데이터 - Gemini API 키가 설정되지 않음\n\n시장 심리가 부정적입니다. 신중한 접근이 필요합니다."
        else:
            recommendation = "⚠️ 모의 데이터 - Gemini API 키가 설정되지 않음\n\n시장 심리가 매우 부정적입니다. 리스크 관리에 주의하세요."
            
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