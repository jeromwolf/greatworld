"""
Social Agent - SNS 데이터 수집 에이전트
Reddit, X(Twitter), StockTwits 등에서 투자자 심리 데이터 수집
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
import re


@dataclass
class SocialPost:
    """소셜 미디어 포스트 데이터 모델"""
    content: str            # 내용
    author: str            # 작성자
    platform: str          # 플랫폼 (reddit, twitter, stocktwits)
    created_at: str        # 작성일시
    url: str              # URL
    score: int = 0        # 점수/좋아요
    comments: int = 0     # 댓글 수
    sentiment: Optional[float] = None  # 감성 점수


class SocialAgent:
    """SNS 데이터 수집 에이전트"""
    
    def __init__(self, 
                 reddit_client_id: Optional[str] = None,
                 reddit_client_secret: Optional[str] = None):
        # Reddit API 설정
        self.reddit_client_id = reddit_client_id or os.getenv("REDDIT_CLIENT_ID", "")
        self.reddit_client_secret = reddit_client_secret or os.getenv("REDDIT_CLIENT_SECRET", "")
        self.reddit_base_url = "https://oauth.reddit.com"
        
        self.session = None
        self.reddit_token = None
        
        # 플랫폼별 가중치
        self.platform_weights = {
            "reddit_wsb": 0.8,      # r/wallstreetbets
            "reddit_stocks": 0.9,   # r/stocks
            "reddit_investing": 1.0, # r/investing
            "stocktwits": 0.7,
            "twitter": 0.6,
            "discord": 0.5
        }
        
        # 주요 서브레딧
        self.stock_subreddits = [
            "wallstreetbets",
            "stocks", 
            "investing",
            "StockMarket",
            "SecurityAnalysis",
            "ValueInvesting",
            "options"
        ]
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession()
        # Reddit 인증
        if self.reddit_client_id and self.reddit_client_secret:
            await self._authenticate_reddit()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
            
    async def _authenticate_reddit(self):
        """Reddit OAuth 인증"""
        auth = aiohttp.BasicAuth(self.reddit_client_id, self.reddit_client_secret)
        data = {
            'grant_type': 'client_credentials'
        }
        headers = {'User-Agent': 'StockAI/1.0'}
        
        async with self.session.post(
            'https://www.reddit.com/api/v1/access_token',
            auth=auth,
            data=data,
            headers=headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                self.reddit_token = result['access_token']
                
    async def search_reddit(self,
                           query: str,
                           subreddit: Optional[str] = None,
                           sort: str = "relevance",
                           time_filter: str = "week",
                           limit: int = 25) -> Dict[str, Any]:
        """
        Reddit 검색
        
        Args:
            query: 검색어 (주식명, 티커)
            subreddit: 특정 서브레딧 (없으면 주식 관련 모든 서브레딧)
            sort: 정렬 방식 (relevance, hot, top, new)
            time_filter: 시간 필터 (day, week, month, year, all)
            limit: 결과 수
        """
        if not self.reddit_token:
            # 인증 없이 모의 데이터 반환
            return await self._get_mock_reddit_data(query)
            
        headers = {
            'Authorization': f'Bearer {self.reddit_token}',
            'User-Agent': 'StockAI/1.0'
        }
        
        # 서브레딧 지정
        if subreddit:
            search_url = f"{self.reddit_base_url}/r/{subreddit}/search"
        else:
            # 주식 관련 서브레딧 전체 검색
            subreddit_str = "+".join(self.stock_subreddits)
            search_url = f"{self.reddit_base_url}/r/{subreddit_str}/search"
            
        params = {
            'q': query,
            'sort': sort,
            't': time_filter,
            'limit': limit,
            'restrict_sr': 'on'  # 해당 서브레딧으로 제한
        }
        
        try:
            async with self.session.get(
                search_url,
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    posts = []
                    for item in data.get('data', {}).get('children', []):
                        post_data = item['data']
                        
                        post = SocialPost(
                            content=f"{post_data.get('title', '')}\n{post_data.get('selftext', '')}",
                            author=post_data.get('author', 'unknown'),
                            platform=f"reddit_{post_data.get('subreddit', '').lower()}",
                            created_at=datetime.fromtimestamp(post_data.get('created_utc', 0)).isoformat(),
                            url=f"https://reddit.com{post_data.get('permalink', '')}",
                            score=post_data.get('score', 0),
                            comments=post_data.get('num_comments', 0)
                        )
                        posts.append(asdict(post))
                        
                    return {
                        "status": "success",
                        "platform": "reddit",
                        "count": len(posts),
                        "posts": posts,
                        "data_source": "REAL_DATA"
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"HTTP error: {response.status}",
                        "data_source": "REAL_DATA"
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "message": f"Request failed: {str(e)}",
                "data_source": "REAL_DATA"
            }
            
    async def get_wsb_sentiment(self, ticker: str) -> Dict[str, Any]:
        """
        r/wallstreetbets에서 특정 종목의 감성 분석
        
        Args:
            ticker: 종목 티커
        """
        # WSB 특화 검색
        result = await self.search_reddit(
            query=f"${ticker} OR {ticker}",
            subreddit="wallstreetbets",
            sort="hot",
            time_filter="day",
            limit=50
        )
        
        if result["status"] == "success":
            posts = result.get("posts", [])
            
            # 감성 분석 (간단한 규칙 기반)
            bullish_keywords = [
                "moon", "rocket", "buy", "calls", "bullish", "long",
                "🚀", "💎", "🙌", "green", "up", "pump", "squeeze"
            ]
            bearish_keywords = [
                "puts", "short", "sell", "bearish", "crash", "dump",
                "📉", "🐻", "red", "down", "overvalued", "bubble"
            ]
            
            sentiment_scores = []
            total_score = 0
            total_comments = 0
            
            for post in posts:
                content_lower = post['content'].lower()
                
                # 긍정/부정 키워드 수 계산
                bullish_count = sum(1 for keyword in bullish_keywords if keyword in content_lower)
                bearish_count = sum(1 for keyword in bearish_keywords if keyword in content_lower)
                
                # 개별 포스트 감성 점수
                if bullish_count > bearish_count:
                    sentiment = min(1.0, bullish_count * 0.2)
                elif bearish_count > bullish_count:
                    sentiment = max(-1.0, -bearish_count * 0.2)
                else:
                    sentiment = 0.0
                    
                # 점수와 댓글 수로 가중치 적용
                weight = 1 + (post['score'] / 100) + (post['comments'] / 50)
                sentiment_scores.append(sentiment * weight)
                
                total_score += post['score']
                total_comments += post['comments']
                
            # 전체 감성 점수 계산
            if sentiment_scores:
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            else:
                avg_sentiment = 0.0
                
            return {
                "status": "success",
                "ticker": ticker,
                "platform": "reddit_wallstreetbets",
                "post_count": len(posts),
                "total_score": total_score,
                "total_comments": total_comments,
                "sentiment_score": round(avg_sentiment, 2),
                "sentiment_label": self._get_sentiment_label(avg_sentiment),
                "top_posts": posts[:5],  # 상위 5개 포스트
                "data_source": result.get("data_source", "REAL_DATA")
            }
        else:
            return result
            
    async def search_stocktwits(self, ticker: str) -> Dict[str, Any]:
        """
        StockTwits에서 종목 검색 (모의 데이터)
        
        Args:
            ticker: 종목 티커
        """
        # StockTwits API는 인증이 필요하므로 모의 데이터 반환
        mock_posts = [
            {
                "content": f"⚠️ 모의 데이터 - StockTwits API 인증이 설정되지 않음\n${ticker} 상승 모멘텀 강하게 보임! $150 저항선 돌파 🚀",
                "author": "trader123",
                "platform": "stocktwits",
                "created_at": datetime.now().isoformat(),
                "url": f"https://stocktwits.com/symbol/{ticker}",
                "score": 45,
                "comments": 12,
                "sentiment": 0.7
            },
            {
                "content": f"⚠️ 모의 데이터 - StockTwits API 인증이 설정되지 않음\n${ticker} RSI 과매수 상태, 조정 예상",
                "author": "technicaltrader",
                "platform": "stocktwits", 
                "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "url": f"https://stocktwits.com/symbol/{ticker}",
                "score": 23,
                "comments": 5,
                "sentiment": -0.3
            }
        ]
        
        return {
            "status": "success",
            "platform": "stocktwits",
            "ticker": ticker,
            "count": len(mock_posts),
            "posts": mock_posts,
            "data_source": "MOCK_DATA"
        }
        
    async def get_trending_tickers(self, platform: str = "all") -> Dict[str, Any]:
        """
        트렌딩 종목 가져오기
        
        Args:
            platform: 플랫폼 (reddit, stocktwits, all)
        """
        trending = {
            "reddit": [
                {"ticker": "GME", "mentions": 1523, "sentiment": 0.6},
                {"ticker": "AMC", "mentions": 892, "sentiment": 0.4},
                {"ticker": "TSLA", "mentions": 756, "sentiment": 0.2},
                {"ticker": "NVDA", "mentions": 623, "sentiment": 0.8},
                {"ticker": "SPY", "mentions": 412, "sentiment": -0.1}
            ],
            "stocktwits": [
                {"ticker": "AAPL", "mentions": 2341, "sentiment": 0.5},
                {"ticker": "TSLA", "mentions": 1876, "sentiment": 0.3},
                {"ticker": "AMD", "mentions": 1234, "sentiment": 0.7},
                {"ticker": "MSFT", "mentions": 987, "sentiment": 0.4},
                {"ticker": "META", "mentions": 765, "sentiment": 0.2}
            ]
        }
        
        if platform == "all":
            # 모든 플랫폼 통합
            all_tickers = {}
            for plat, tickers in trending.items():
                for item in tickers:
                    ticker = item["ticker"]
                    if ticker not in all_tickers:
                        all_tickers[ticker] = {
                            "mentions": 0,
                            "sentiment_sum": 0,
                            "platforms": []
                        }
                    all_tickers[ticker]["mentions"] += item["mentions"]
                    all_tickers[ticker]["sentiment_sum"] += item["sentiment"] * item["mentions"]
                    all_tickers[ticker]["platforms"].append(plat)
                    
            # 평균 감성 계산 및 정렬
            result = []
            for ticker, data in all_tickers.items():
                avg_sentiment = data["sentiment_sum"] / data["mentions"]
                result.append({
                    "ticker": ticker,
                    "total_mentions": data["mentions"],
                    "avg_sentiment": round(avg_sentiment, 2),
                    "platforms": data["platforms"]
                })
                
            result.sort(key=lambda x: x["total_mentions"], reverse=True)
            
            return {
                "status": "success",
                "platform": "all",
                "trending": result[:10],  # 상위 10개
                "data_source": "MOCK_DATA"
            }
        else:
            return {
                "status": "success", 
                "platform": platform,
                "trending": trending.get(platform, []),
                "data_source": "MOCK_DATA"
            }
            
    async def _get_mock_reddit_data(self, query: str) -> Dict[str, Any]:
        """Reddit API 인증 없이 모의 데이터 반환"""
        mock_posts = [
            SocialPost(
                content=f"⚠️ 모의 데이터 - Reddit API 인증이 설정되지 않음\n{query} DD: 이 주식에 대한 강세 전망 🚀🚀🚀",
                author="WSBTrader123",
                platform="reddit_wallstreetbets",
                created_at=datetime.now().isoformat(),
                url="https://reddit.com/r/wallstreetbets/mock1",
                score=1523,
                comments=234,
                sentiment=0.8
            ),
            SocialPost(
                content=f"⚠️ 모의 데이터 - Reddit API 인증이 설정되지 않음\n기술적 분석: {query} 컵앤핸들 패턴 형성 중",
                author="TechnicalTrader",
                platform="reddit_stocks",
                created_at=(datetime.now() - timedelta(hours=5)).isoformat(),
                url="https://reddit.com/r/stocks/mock2",
                score=456,
                comments=78,
                sentiment=0.5
            ),
            SocialPost(
                content=f"⚠️ 모의 데이터 - Reddit API 인증이 설정되지 않음\n{query} 주의 필요, 현재 가격 수준에서 과대평가됨",
                author="ValueInvestor",
                platform="reddit_investing",
                created_at=(datetime.now() - timedelta(days=1)).isoformat(),
                url="https://reddit.com/r/investing/mock3",
                score=234,
                comments=45,
                sentiment=-0.3
            )
        ]
        
        return {
            "status": "success",
            "message": "⚠️ 모의 데이터 - Reddit API 인증이 설정되지 않음",
            "platform": "reddit",
            "count": len(mock_posts),
            "posts": [asdict(post) for post in mock_posts],
            "data_source": "MOCK_DATA"
        }
        
    def _get_sentiment_label(self, score: float) -> str:
        """감성 점수를 라벨로 변환"""
        if score >= 0.6:
            return "Very Bullish 🚀"
        elif score >= 0.2:
            return "Bullish 📈"
        elif score >= -0.2:
            return "Neutral ➖"
        elif score >= -0.6:
            return "Bearish 📉"
        else:
            return "Very Bearish 🐻"


# 테스트 함수
async def test_social_agent():
    """Social Agent 테스트"""
    print("=== Social Agent 테스트 ===\\n")
    
    async with SocialAgent() as agent:
        # 1. Reddit 검색
        print("1. Reddit에서 TSLA 검색")
        result = await agent.search_reddit("TSLA", limit=5)
        if result["status"] == "success":
            print(f"검색 결과: {result['count']}건")
            for post in result.get("posts", [])[:3]:
                content_lines = post['content'].split('\n')
                print("")
                print(f"제목: {content_lines[0][:80]}...")
                print(f"작성자: {post['author']}")
                print(f"점수: {post['score']}, 댓글: {post['comments']}")
                
        print("\n" + "-" * 50 + "\n")
        
        # 2. WSB 감성 분석
        print("2. r/wallstreetbets GME 감성 분석")
        result = await agent.get_wsb_sentiment("GME")
        if result["status"] == "success":
            print(f"분석 포스트 수: {result['post_count']}")
            print(f"총 점수: {result['total_score']}")
            print(f"총 댓글: {result['total_comments']}")
            print(f"감성 점수: {result['sentiment_score']} ({result['sentiment_label']})")
            
        print("\n" + "-" * 50 + "\n")
        
        # 3. StockTwits 검색
        print("3. StockTwits AAPL 검색")
        result = await agent.search_stocktwits("AAPL")
        if result["status"] == "success":
            print(f"검색 결과: {result['count']}건")
            for post in result.get("posts", []):
                print(f"- {post['content']}")
                print(f"  감성: {post['sentiment']}")
                
        print("\n" + "-" * 50 + "\n")
        
        # 4. 트렌딩 종목
        print("4. 전체 플랫폼 트렌딩 종목")
        result = await agent.get_trending_tickers("all")
        if result["status"] == "success":
            print("Top 5 트렌딩 종목:")
            for item in result["trending"][:5]:
                print(f"- {item['ticker']}: {item['total_mentions']}회 언급")
                print(f"  평균 감성: {item['avg_sentiment']}")
                print(f"  플랫폼: {', '.join(item['platforms'])}")
                

if __name__ == "__main__":
    asyncio.run(test_social_agent())