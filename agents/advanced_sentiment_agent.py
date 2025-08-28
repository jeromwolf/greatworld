"""
Advanced Sentiment Agent - 고도화된 감성 분석 에이전트
도메인 특화 감성 사전과 컨텍스트 분석을 통한 정확한 감성 스코어링
"""

import os
import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict
import json


@dataclass
class SentimentScore:
    """감성 점수 상세 정보"""
    raw_score: float           # 원시 점수 (-1 ~ 1)
    weighted_score: float      # 가중치 적용 점수
    confidence: float          # 신뢰도 (0 ~ 1)
    category: str             # 카테고리 (매우긍정/긍정/중립/부정/매우부정)
    factors: List[str]        # 주요 감성 요인
    keywords: Dict[str, int]  # 감성 키워드와 빈도


class AdvancedSentimentAgent:
    """고도화된 감성 분석 에이전트"""
    
    def __init__(self):
        # 도메인 특화 감성 사전 초기화
        self._initialize_sentiment_lexicon()
        
    def _initialize_sentiment_lexicon(self):
        """금융 도메인 특화 감성 사전 초기화"""
        
        # 긍정 키워드 (점수: 0.1 ~ 1.0)
        self.positive_keywords = {
            # 매우 긍정적 (0.8 ~ 1.0)
            "대박": 1.0, "급등": 0.9, "폭등": 0.9, "상한가": 0.9,
            "신고가": 0.8, "돌파": 0.8, "흑자전환": 0.9,
            "surge": 0.9, "skyrocket": 0.9, "breakthrough": 0.8,
            "record high": 0.8, "beat expectations": 0.8,
            
            # 긍정적 (0.5 ~ 0.7)
            "상승": 0.6, "증가": 0.6, "성장": 0.7, "개선": 0.6,
            "호재": 0.7, "매수": 0.6, "목표가상향": 0.7,
            "rise": 0.6, "gain": 0.6, "growth": 0.7, "improve": 0.6,
            "buy": 0.6, "upgrade": 0.7, "outperform": 0.7,
            
            # 약간 긍정적 (0.1 ~ 0.4)
            "안정": 0.3, "회복": 0.4, "반등": 0.4, "지지": 0.3,
            "steady": 0.3, "recover": 0.4, "rebound": 0.4, "support": 0.3
        }
        
        # 부정 키워드 (점수: -1.0 ~ -0.1)
        self.negative_keywords = {
            # 매우 부정적 (-1.0 ~ -0.8)
            "폭락": -0.9, "급락": -0.9, "하한가": -0.9,
            "적자전환": -0.9, "파산": -1.0, "상장폐지": -1.0,
            "plunge": -0.9, "crash": -0.9, "collapse": -0.9,
            "bankruptcy": -1.0, "delisting": -1.0,
            
            # 부정적 (-0.7 ~ -0.5)
            "하락": -0.6, "감소": -0.6, "부진": -0.6, "악재": -0.7,
            "매도": -0.6, "목표가하향": -0.7, "경고": -0.6,
            "fall": -0.6, "decline": -0.6, "drop": -0.6,
            "sell": -0.6, "downgrade": -0.7, "warning": -0.6,
            
            # 약간 부정적 (-0.4 ~ -0.1)
            "우려": -0.3, "불안": -0.3, "약세": -0.4, "압력": -0.3,
            "concern": -0.3, "worry": -0.3, "weak": -0.4, "pressure": -0.3
        }
        
        # 강조 표현 (배수)
        self.intensifiers = {
            "매우": 1.5, "정말": 1.5, "너무": 1.5, "대단히": 1.5,
            "약간": 0.7, "조금": 0.7, "다소": 0.7,
            "very": 1.5, "extremely": 1.8, "really": 1.5,
            "slightly": 0.7, "somewhat": 0.7, "a bit": 0.7
        }
        
        # 부정 표현
        self.negations = {
            "안", "못", "없", "아니", "않",
            "not", "no", "never", "neither", "nor"
        }
        
        # 컨텍스트별 가중치
        self.context_weights = {
            "title": 2.0,        # 제목
            "summary": 1.5,      # 요약
            "content": 1.0,      # 본문
            "comment": 0.8,      # 댓글
            "disclosure": 1.8,   # 공시
            "analyst": 1.5       # 애널리스트 의견
        }
        
    def analyze_text_sentiment(self, text: str, context: str = "content") -> SentimentScore:
        """
        텍스트의 감성 분석
        
        Args:
            text: 분석할 텍스트
            context: 텍스트 컨텍스트 (title, summary, content 등)
            
        Returns:
            SentimentScore 객체
        """
        if not text:
            return SentimentScore(0.0, 0.0, 0.0, "중립", [], {})
            
        # 텍스트 전처리
        text_lower = text.lower()
        sentences = re.split(r'[.!?。！？]', text)
        
        # 감성 점수 계산
        total_score = 0.0
        keyword_counts = defaultdict(int)
        factors = []
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            sentence_score = 0.0
            sentence_keywords = []
            
            # 긍정 키워드 검색
            for keyword, score in self.positive_keywords.items():
                if keyword in sentence.lower():
                    # 부정어 체크
                    if self._has_negation(sentence, keyword):
                        sentence_score -= score * 0.8  # 부정어가 있으면 반대로
                    else:
                        sentence_score += score
                        sentence_keywords.append(f"+{keyword}")
                    keyword_counts[keyword] += 1
                    
            # 부정 키워드 검색
            for keyword, score in self.negative_keywords.items():
                if keyword in sentence.lower():
                    # 부정어 체크
                    if self._has_negation(sentence, keyword):
                        sentence_score -= score * 0.8  # 부정의 부정은 긍정
                    else:
                        sentence_score += score
                        sentence_keywords.append(f"-{keyword}")
                    keyword_counts[keyword] += 1
                    
            # 강조 표현 적용
            for intensifier, multiplier in self.intensifiers.items():
                if intensifier in sentence.lower():
                    sentence_score *= multiplier
                    
            # 문장 점수를 전체 점수에 반영
            total_score += sentence_score
            
            # 주요 요인 기록
            if abs(sentence_score) > 0.3 and sentence_keywords:
                factors.append(f"{sentence.strip()[:50]}... ({', '.join(sentence_keywords)})")
                
        # 평균 점수 계산
        avg_score = total_score / max(len(sentences), 1)
        
        # -1 ~ 1 범위로 정규화
        normalized_score = max(-1.0, min(1.0, avg_score))
        
        # 컨텍스트 가중치 적용
        context_weight = self.context_weights.get(context, 1.0)
        weighted_score = normalized_score * context_weight
        weighted_score = max(-1.0, min(1.0, weighted_score))
        
        # 신뢰도 계산
        confidence = self._calculate_confidence(keyword_counts, len(text.split()))
        
        # 카테고리 결정
        category = self._determine_category(weighted_score)
        
        return SentimentScore(
            raw_score=normalized_score,
            weighted_score=weighted_score,
            confidence=confidence,
            category=category,
            factors=factors[:5],  # 상위 5개 요인만
            keywords=dict(keyword_counts)
        )
        
    def _has_negation(self, text: str, keyword: str) -> bool:
        """키워드 주변에 부정어가 있는지 확인"""
        # 키워드 위치 찾기
        keyword_pos = text.lower().find(keyword)
        if keyword_pos == -1:
            return False
            
        # 키워드 앞 20자 내에 부정어가 있는지 확인
        start = max(0, keyword_pos - 20)
        prefix = text[start:keyword_pos].lower()
        
        for negation in self.negations:
            if negation in prefix:
                return True
                
        return False
        
    def _calculate_confidence(self, keyword_counts: Dict[str, int], word_count: int) -> float:
        """신뢰도 계산"""
        if word_count == 0:
            return 0.0
            
        # 키워드 밀도
        keyword_density = sum(keyword_counts.values()) / word_count
        
        # 키워드 다양성
        keyword_diversity = len(keyword_counts) / 10  # 10개 이상이면 1.0
        
        # 신뢰도 = (밀도 * 0.6 + 다양성 * 0.4)
        confidence = (min(keyword_density * 10, 1.0) * 0.6 + 
                     min(keyword_diversity, 1.0) * 0.4)
        
        return confidence
        
    def _determine_category(self, score: float) -> str:
        """점수에 따른 카테고리 결정"""
        if score >= 0.6:
            return "매우긍정"
        elif score >= 0.2:
            return "긍정"
        elif score >= -0.2:
            return "중립"
        elif score >= -0.6:
            return "부정"
        else:
            return "매우부정"
            
    async def analyze_news_sentiment(self, articles: List[Dict]) -> Dict[str, Any]:
        """
        뉴스 기사 리스트의 종합 감성 분석
        
        Args:
            articles: 뉴스 기사 리스트
            
        Returns:
            종합 감성 분석 결과
        """
        if not articles:
            return {
                "overall_score": 0.0,
                "category": "중립",
                "confidence": 0.0,
                "article_sentiments": [],
                "key_factors": [],
                "sentiment_distribution": {
                    "매우긍정": 0,
                    "긍정": 0,
                    "중립": 0,
                    "부정": 0,
                    "매우부정": 0
                }
            }
            
        article_sentiments = []
        all_factors = []
        sentiment_distribution = defaultdict(int)
        
        for article in articles:
            # 제목 분석
            title_sentiment = self.analyze_text_sentiment(
                article.get("title", ""), 
                context="title"
            )
            
            # 요약/설명 분석
            description = article.get("description", "") or article.get("summary", "")
            desc_sentiment = self.analyze_text_sentiment(
                description,
                context="summary"
            )
            
            # 종합 점수 (제목 70%, 요약 30%)
            article_score = (title_sentiment.weighted_score * 0.7 + 
                           desc_sentiment.weighted_score * 0.3)
            
            article_result = {
                "title": article.get("title", ""),
                "score": article_score,
                "category": self._determine_category(article_score),
                "title_sentiment": asdict(title_sentiment),
                "description_sentiment": asdict(desc_sentiment),
                "published_at": article.get("published_at", "")
            }
            
            article_sentiments.append(article_result)
            all_factors.extend(title_sentiment.factors)
            all_factors.extend(desc_sentiment.factors)
            sentiment_distribution[article_result["category"]] += 1
            
        # 시간 가중치 적용 (최신 기사일수록 가중치 높음)
        weighted_scores = []
        sorted_articles = sorted(
            article_sentiments, 
            key=lambda x: x["published_at"],
            reverse=True
        )
        
        for i, article in enumerate(sorted_articles):
            # 최신 기사는 1.0, 오래된 기사는 0.5까지 감소
            time_weight = 1.0 - (i * 0.5 / len(sorted_articles))
            weighted_scores.append(article["score"] * time_weight)
            
        # 전체 감성 점수
        overall_score = sum(weighted_scores) / len(weighted_scores) if weighted_scores else 0.0
        
        # 신뢰도 계산
        score_variance = sum((s - overall_score) ** 2 for s in weighted_scores) / len(weighted_scores) if weighted_scores else 0
        consistency_confidence = 1.0 - min(score_variance, 1.0)  # 일관성이 높을수록 신뢰도 높음
        
        # 주요 요인 정리
        factor_counts = defaultdict(int)
        for factor in all_factors:
            factor_counts[factor] += 1
            
        key_factors = sorted(
            factor_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "overall_score": overall_score,
            "category": self._determine_category(overall_score),
            "confidence": consistency_confidence,
            "article_sentiments": article_sentiments,
            "key_factors": [f[0] for f in key_factors],
            "sentiment_distribution": dict(sentiment_distribution),
            "total_articles": len(articles)
        }
        
    async def analyze_social_sentiment(self, posts: List[Dict]) -> Dict[str, Any]:
        """
        소셜 미디어 포스트의 감성 분석
        
        Args:
            posts: 소셜 포스트 리스트
            
        Returns:
            종합 감성 분석 결과
        """
        if not posts:
            return {
                "overall_score": 0.0,
                "category": "중립",
                "confidence": 0.0,
                "post_sentiments": [],
                "trending_keywords": {}
            }
            
        post_sentiments = []
        all_keywords = defaultdict(int)
        
        for post in posts:
            # 포스트 내용 분석
            content = post.get("content", "") or post.get("text", "")
            sentiment = self.analyze_text_sentiment(content, context="comment")
            
            # 좋아요/업보트 등을 가중치로 사용
            engagement_weight = 1.0
            if post.get("likes", 0) > 100:
                engagement_weight = 1.2
            elif post.get("likes", 0) > 50:
                engagement_weight = 1.1
                
            weighted_score = sentiment.weighted_score * engagement_weight
            
            post_result = {
                "content": content[:100] + "..." if len(content) > 100 else content,
                "score": weighted_score,
                "category": self._determine_category(weighted_score),
                "engagement": post.get("likes", 0) + post.get("comments", 0),
                "keywords": sentiment.keywords
            }
            
            post_sentiments.append(post_result)
            
            # 키워드 집계
            for keyword, count in sentiment.keywords.items():
                all_keywords[keyword] += count
                
        # 전체 감성 점수
        if post_sentiments:
            overall_score = sum(p["score"] for p in post_sentiments) / len(post_sentiments)
        else:
            overall_score = 0.0
            
        # 트렌딩 키워드
        trending_keywords = dict(
            sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        return {
            "overall_score": overall_score,
            "category": self._determine_category(overall_score),
            "confidence": 0.7,  # 소셜 미디어는 기본적으로 신뢰도가 낮음
            "post_sentiments": post_sentiments[:20],  # 상위 20개만
            "trending_keywords": trending_keywords,
            "total_posts": len(posts)
        }


# 테스트 함수
async def test_advanced_sentiment():
    agent = AdvancedSentimentAgent()
    
    # 테스트 텍스트
    test_texts = [
        {
            "text": "삼성전자가 역대 최고 실적을 달성하며 주가가 급등했습니다. 애널리스트들은 목표가를 상향 조정했습니다.",
            "context": "title"
        },
        {
            "text": "경기 침체 우려로 주가가 폭락했습니다. 투자자들의 매도세가 이어지고 있습니다.",
            "context": "title"
        },
        {
            "text": "실적은 예상치를 상회했으나 향후 전망은 불확실합니다.",
            "context": "summary"
        }
    ]
    
    for test in test_texts:
        result = agent.analyze_text_sentiment(test["text"], test["context"])
        print(f"\n텍스트: {test['text']}")
        print(f"점수: {result.weighted_score:.2f}")
        print(f"카테고리: {result.category}")
        print(f"신뢰도: {result.confidence:.2f}")
        print(f"키워드: {result.keywords}")
        print(f"요인: {result.factors}")


if __name__ == "__main__":
    asyncio.run(test_advanced_sentiment())