"""
News Agent - 뉴스 데이터 수집 에이전트
다양한 뉴스 소스에서 주식 관련 뉴스 수집
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
from urllib.parse import quote


@dataclass
class NewsArticle:
    """뉴스 기사 데이터 모델"""
    title: str              # 제목
    description: str        # 요약
    url: str               # URL
    source: str            # 출처
    published_at: str      # 발행일시
    author: Optional[str] = None  # 저자
    image_url: Optional[str] = None  # 이미지 URL
    sentiment: Optional[float] = None  # 감성 점수 (-1 ~ 1)


class NewsAgent:
    """뉴스 데이터 수집 에이전트"""
    
    def __init__(self, newsapi_key: Optional[str] = None, openai_key: Optional[str] = None):
        self.newsapi_key = newsapi_key or os.getenv("NEWSAPI_KEY", "")
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY", "")
        self.newsapi_url = "https://newsapi.org/v2"
        self.session = None
        
        # 뉴스 소스별 신뢰도 가중치
        self.source_weights = {
            # 국내
            "연합뉴스": 1.2,
            "한국경제": 1.1,
            "매일경제": 1.1,
            "조선비즈": 1.0,
            "이데일리": 1.0,
            "머니투데이": 0.9,
            
            # 해외
            "Reuters": 1.3,
            "Bloomberg": 1.3,
            "Financial Times": 1.2,
            "Wall Street Journal": 1.2,
            "CNBC": 1.1,
            "MarketWatch": 1.0,
            "Yahoo Finance": 0.9,
            "Seeking Alpha": 0.8
        }
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
            
    async def search_news(self,
                         query: str,
                         language: Optional[str] = None,
                         from_date: Optional[str] = None,
                         to_date: Optional[str] = None,
                         sort_by: str = "relevancy",
                         page_size: int = 20) -> Dict[str, Any]:
        """
        뉴스 검색
        
        Args:
            query: 검색어 (주식명, 티커 등)
            language: 언어 코드 (ko, en)
            from_date: 시작일 (YYYY-MM-DD)
            to_date: 종료일 (YYYY-MM-DD)
            sort_by: 정렬 방식 (relevancy, popularity, publishedAt)
            page_size: 페이지당 결과 수
        """
        if not self.newsapi_key:
            # API 키가 없으면 RSS 기반 실제 뉴스 사용
            print(f"[NEWS] Using RSS news for: {query}", flush=True)
            return await self._get_rss_news(query, language)
            
        # 날짜 기본값 설정 - 최적화된 기간 사용
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")
        if not from_date:
            # PeriodConfig에서 뉴스 최적 기간 가져오기
            from config.period_config import PeriodConfig
            from_date = (datetime.now() - timedelta(days=PeriodConfig.NEWS_PERIOD_DAYS)).strftime("%Y-%m-%d")
            
        params = {
            "q": query,
            "from": from_date,
            "to": to_date,
            "sortBy": sort_by,
            "pageSize": page_size,
            "apiKey": self.newsapi_key
        }
        
        if language:
            params["language"] = language
            
        try:
            async with self.session.get(
                f"{self.newsapi_url}/everything",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    articles = []
                    for item in data.get("articles", []):
                        article = NewsArticle(
                            title=item.get("title", ""),
                            description=item.get("description", ""),
                            url=item.get("url", ""),
                            source=item.get("source", {}).get("name", "Unknown"),
                            published_at=item.get("publishedAt", ""),
                            author=item.get("author"),
                            image_url=item.get("urlToImage")
                        )
                        articles.append(asdict(article))
                        
                    return {
                        "status": "success",
                        "total_results": data.get("totalResults", 0),
                        "articles": articles,
                        "data_source": "REAL_DATA"
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"HTTP error: {response.status}"
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
            
    async def search_korean_news(self, 
                                company_name: str,
                                days: int = 7) -> Dict[str, Any]:
        """
        한국 기업 뉴스 검색 (구글 뉴스 RSS 사용)
        
        Args:
            company_name: 회사명
            days: 조회 기간 (일)
        """
        try:
            # 구글 뉴스 RSS를 사용하여 실제 뉴스 검색
            import feedparser
            from urllib.parse import quote
            
            # 한국 뉴스 검색 (구글 뉴스)
            search_query = quote(f"{company_name} 주식")
            google_news_url = f"https://news.google.com/rss/search?q={search_query}&hl=ko&gl=KR&ceid=KR:ko"
            
            feed = feedparser.parse(google_news_url)
            
            articles = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for entry in feed.entries[:10]:  # 최대 10개
                try:
                    pub_date = datetime.fromisoformat(entry.published.replace('Z', '+00:00').replace(' GMT', '+00:00'))
                except:
                    pub_date = datetime.now()
                
                if pub_date >= cutoff_date:
                    # 뉴스 제목에서 유용한 정보 추출
                    title = entry.title
                    summary = self._extract_key_info(title, company_name)
                    
                    articles.append({
                        "title": title,
                        "description": entry.summary if hasattr(entry, 'summary') else entry.title,
                        "url": entry.link,
                        "source": entry.source.href if hasattr(entry, 'source') else "Google News",
                        "published_at": pub_date.isoformat(),
                        "sentiment": None,
                        "key_info": summary
                    })
            
            if articles:
                return {
                    "status": "success",
                    "company": company_name,
                    "period_days": days,
                    "count": len(articles),
                    "articles": articles,
                    "data_source": "REAL_DATA",
                    "message": f"구글 뉴스에서 {len(articles)}개 기사 수집"
                }
            else:
                # 실제 검색 결과가 없는 경우만 모의 데이터 반환
                return self._get_korean_mock_news(company_name)
                
        except Exception as e:
            print(f"Korean news search error: {str(e)}")
            # 에러 시 모의 데이터 반환
            return self._get_korean_mock_news(company_name)
    
    def _get_korean_mock_news(self, company_name: str) -> Dict[str, Any]:
        """한국 뉴스 모의 데이터"""
        mock_articles = [
            {
                "title": f"{company_name}, 3분기 실적 시장 예상 상회",
                "description": f"{company_name}이 3분기 실적에서 시장 예상을 크게 웃도는 성과를 거뒀다.",
                "url": "https://news.example.com/1",
                "source": "한국경제",
                "published_at": datetime.now().isoformat(),
                "sentiment": 0.8
            },
            {
                "title": f"{company_name} 신사업 진출 본격화",
                "description": f"{company_name}이 AI 분야 신사업 진출을 본격화한다고 밝혔다.",
                "url": "https://news.example.com/2",
                "source": "매일경제",
                "published_at": (datetime.now() - timedelta(days=1)).isoformat(),
                "sentiment": 0.6
            }
        ]
        
        return {
            "status": "success",
            "company": company_name,
            "period_days": 7,
            "count": len(mock_articles),
            "articles": mock_articles,
            "data_source": "MOCK_DATA",
            "message": "⚠️ 모의 데이터 - 실제 뉴스 수집 실패"
        }
        
    async def search_financial_news(self,
                                   ticker: str,
                                   news_type: str = "all") -> Dict[str, Any]:
        """
        재무 관련 뉴스 검색
        
        Args:
            ticker: 종목 티커
            news_type: 뉴스 유형 (earnings, analysis, market)
        """
        # 재무 뉴스에 특화된 검색
        query_map = {
            "earnings": f"{ticker} earnings report quarterly results",
            "analysis": f"{ticker} analyst rating price target",
            "market": f"{ticker} stock market trading volume",
            "all": ticker
        }
        
        query = query_map.get(news_type, ticker)
        
        # NewsAPI 또는 다른 재무 뉴스 API 사용
        result = await self.search_news(query, language="en")
        
        if result["status"] == "success":
            # 재무 관련 키워드로 필터링
            financial_keywords = [
                "earnings", "revenue", "profit", "quarterly", "analyst",
                "price target", "rating", "upgrade", "downgrade", "EPS"
            ]
            
            filtered_articles = []
            for article in result.get("articles", []):
                title_lower = article.get("title", "").lower()
                desc_lower = article.get("description", "").lower()
                
                # 재무 키워드가 포함된 기사만 선택
                if any(keyword in title_lower or keyword in desc_lower 
                      for keyword in financial_keywords):
                    filtered_articles.append(article)
                    
            result["articles"] = filtered_articles
            result["count"] = len(filtered_articles)
            # data_source는 원본 결과에서 유지됨
            
        return result
        
    async def get_trending_news(self,
                               sector: Optional[str] = None,
                               limit: int = 10) -> Dict[str, Any]:
        """
        트렌딩 뉴스 가져오기
        
        Args:
            sector: 섹터 (tech, finance, healthcare 등)
            limit: 최대 결과 수
        """
        # 섹터별 주요 키워드
        sector_keywords = {
            "tech": "technology stocks NASDAQ tech earnings",
            "finance": "banking financial services Fed interest rates",
            "healthcare": "pharmaceutical biotech FDA approval",
            "energy": "oil gas renewable energy crude prices",
            "retail": "consumer retail sales e-commerce"
        }
        
        query = sector_keywords.get(sector, "stock market trending")
        
        # 최신순으로 정렬하여 트렌딩 뉴스 가져오기
        result = await self.search_news(
            query=query,
            sort_by="publishedAt",
            page_size=limit
        )
        
        return result
        
    async def _get_mock_news(self, query: str) -> Dict[str, Any]:
        """API 키 없을 때 모의 뉴스 데이터 반환"""
        mock_articles = [
            {
                "title": f"{query} Shows Strong Q3 Performance",
                "description": f"{query} reported better-than-expected earnings for Q3 2024",
                "url": "https://example.com/news/1",
                "source": "Financial Times",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "published_at": datetime.now().isoformat(),
                "sentiment": 0.7
            },
            {
                "title": f"Analysts Upgrade {query} Price Target",
                "description": f"Major investment banks raise price targets for {query}",
                "url": "https://example.com/news/2",
                "source": "Reuters",
                "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
                "published_at": (datetime.now() - timedelta(days=1)).isoformat(),
                "sentiment": 0.8
            },
            {
                "title": f"{query} Faces Regulatory Challenges",
                "description": f"Regulators scrutinize {query}'s market practices",
                "url": "https://example.com/news/3",
                "source": "Bloomberg",
                "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
                "published_at": (datetime.now() - timedelta(days=2)).isoformat(),
                "sentiment": -0.3
            }
        ]
        
        return {
            "status": "success",
            "message": "⚠️ 모의 데이터 - NewsAPI 키가 설정되지 않음",
            "total_results": len(mock_articles),
            "count": len(mock_articles),
            "articles": mock_articles,
            "data_source": "MOCK_DATA"
        }
    
    async def _get_rss_news(self, query: str, language: str = "ko") -> Dict[str, Any]:
        """RSS를 통한 실제 뉴스 수집"""
        try:
            import feedparser
            from urllib.parse import quote
            
            print(f"[RSS NEWS] Fetching news for: {query}, language: {language}", flush=True)
            
            if language == "ko" or any(ord(char) > 127 for char in query):
                # 한국 뉴스 - 구글 뉴스
                search_query = quote(f"{query} 주식")
                rss_url = f"https://news.google.com/rss/search?q={search_query}&hl=ko&gl=KR&ceid=KR:ko"
            else:
                # 영어 뉴스 - 구글 뉴스
                search_query = quote(f"{query} stock")
                rss_url = f"https://news.google.com/rss/search?q={search_query}&hl=en&gl=US&ceid=US:en"
            
            print(f"[RSS NEWS] Fetching from URL: {rss_url}", flush=True)
            
            # RSS 파싱
            feed = feedparser.parse(rss_url)
            
            articles = []
            for entry in feed.entries[:10]:  # 최대 10개
                try:
                    # 발행일 파싱
                    pub_date = entry.published if hasattr(entry, 'published') else datetime.now().isoformat()
                    
                    # 기사 정보 추출
                    title = entry.title if hasattr(entry, 'title') else "제목 없음"
                    description = entry.summary if hasattr(entry, 'summary') else title
                    link = entry.link if hasattr(entry, 'link') else ""
                    
                    # 소스 추출
                    source = "Google News"
                    if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
                        source = entry.source.title
                    
                    articles.append({
                        "title": title,
                        "description": description,
                        "url": link,
                        "source": source,
                        "publishedAt": pub_date,
                        "sentiment": None,
                        "key_info": None
                    })
                    
                except Exception as article_error:
                    print(f"[RSS NEWS] Error parsing article: {article_error}", flush=True)
                    continue
                    
            print(f"[RSS NEWS] Found {len(articles)} articles", flush=True)
            
            if articles:
                return {
                    "status": "success",
                    "message": f"RSS에서 {len(articles)}개 뉴스 수집 완료",
                    "total_results": len(articles),
                    "articles": articles,
                    "data_source": "REAL_DATA"
                }
            else:
                return {
                    "status": "error",
                    "message": "RSS에서 뉴스를 찾을 수 없습니다",
                    "total_results": 0,
                    "articles": [],
                    "data_source": "REAL_DATA"
                }
                
        except Exception as e:
            print(f"[RSS NEWS] Error: {e}", flush=True)
            # RSS 실패 시 모의 데이터 반환
            return await self._get_mock_news(query)
        
    def calculate_news_sentiment_score(self, articles: List[Dict]) -> float:
        """
        뉴스 목록의 전체 감성 점수 계산
        
        Args:
            articles: 뉴스 기사 목록
            
        Returns:
            전체 감성 점수 (-1 ~ 1)
        """
        if not articles:
            return 0.0
            
        total_score = 0.0
        total_weight = 0.0
        
        for article in articles:
            # 출처별 가중치 적용
            source = article.get("source", "Unknown")
            weight = self.source_weights.get(source, 0.5)
            
            # 개별 기사 감성 점수 (실제로는 감성 분석 모델 사용)
            sentiment = article.get("sentiment", 0.0)
            
            total_score += sentiment * weight
            total_weight += weight
            
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _extract_key_info(self, title: str, company_name: str) -> str:
        """
        뉴스 제목에서 핵심 정보 추출
        
        사용자에게 유용한 정보:
        - 목표가 변경
        - 실적 발표
        - 주요 계약/파트너십
        - 규제/정책 변화
        - 경영진 변경
        """
        key_info = []
        
        # 목표가 관련
        if "목표가" in title or "price target" in title.lower():
            if "상향" in title or "raise" in title.lower() or "upgrade" in title.lower():
                key_info.append("📈 목표가 상향")
            elif "하향" in title or "lower" in title.lower() or "downgrade" in title.lower():
                key_info.append("📉 목표가 하향")
            else:
                key_info.append("🎯 목표가 조정")
                
        # 실적 관련
        if "실적" in title or "earnings" in title.lower() or "profit" in title.lower():
            if "호조" in title or "상승" in title or "beat" in title.lower():
                key_info.append("💰 실적 호조")
            elif "부진" in title or "하락" in title or "miss" in title.lower():
                key_info.append("⚠️ 실적 부진")
                
        # 주가 움직임
        if any(keyword in title for keyword in ["급등", "급락", "상승", "하락", "surge", "plunge", "rise", "fall"]):
            if any(keyword in title for keyword in ["급등", "상승", "surge", "rise"]):
                key_info.append("📊 주가 상승")
            else:
                key_info.append("📉 주가 하락")
                
        # 사업/계약 관련
        if any(keyword in title for keyword in ["계약", "수주", "파트너십", "인수", "합병", "contract", "partnership", "acquisition"]):
            key_info.append("🤝 주요 계약/파트너십")
            
        # 기술/제품 관련
        if any(keyword in title for keyword in ["신제품", "출시", "개발", "혁신", "launch", "develop", "innovation"]):
            key_info.append("🚀 신제품/기술 개발")
            
        # 규제/정책
        if any(keyword in title for keyword in ["규제", "정책", "법안", "제재", "regulation", "policy", "sanction"]):
            key_info.append("⚖️ 규제/정책 이슈")
            
        # 배당/자사주
        if any(keyword in title for keyword in ["배당", "자사주", "dividend", "buyback"]):
            key_info.append("💵 주주환원 정책")
        
        return " | ".join(key_info) if key_info else ""


# 테스트 함수
async def test_news_agent():
    """News Agent 테스트"""
    print("=== News Agent 테스트 ===\\n")
    
    async with NewsAgent() as agent:
        # 1. 일반 뉴스 검색
        print("1. Apple 뉴스 검색")
        result = await agent.search_news("Apple stock", language="en", page_size=5)
        if result["status"] == "success":
            print(f"전체 결과: {result.get('total_results')}건")
            for article in result.get("articles", [])[:3]:
                print(f"\\n제목: {article['title']}")
                print(f"출처: {article['source']}")
                print(f"발행일: {article['published_at']}")
                if article.get('description'):
                    print(f"요약: {article['description'][:100]}...")
                    
        print("\\n" + "-" * 50 + "\\n")
        
        # 2. 한국 기업 뉴스
        print("2. 삼성전자 뉴스 검색")
        result = await agent.search_korean_news("삼성전자", days=7)
        if result["status"] == "success":
            print(f"검색 기간: 최근 {result['period_days']}일")
            print(f"검색 결과: {result['count']}건")
            for article in result.get("articles", []):
                print(f"- [{article['source']}] {article['title']}")
                print(f"  감성 점수: {article.get('sentiment', 0)}")
                
        print("\\n" + "-" * 50 + "\\n")
        
        # 3. 재무 뉴스 검색
        print("3. Tesla 재무 뉴스")
        result = await agent.search_financial_news("TSLA", news_type="earnings")
        if result["status"] == "success":
            print(f"재무 관련 뉴스: {result.get('count', len(result.get('articles', [])))}건")
            for article in result.get("articles", [])[:2]:
                print(f"- {article['title']}")
                
        print("\\n" + "-" * 50 + "\\n")
        
        # 4. 감성 점수 계산
        print("4. 뉴스 감성 점수 계산")
        if result.get("articles"):
            sentiment_score = agent.calculate_news_sentiment_score(result["articles"])
            print(f"전체 감성 점수: {sentiment_score:.2f} (-1 ~ 1)")
            if sentiment_score > 0.3:
                print("➡️ 긍정적인 뉴스가 우세합니다")
            elif sentiment_score < -0.3:
                print("➡️ 부정적인 뉴스가 우세합니다")
            else:
                print("➡️ 중립적인 뉴스가 우세합니다")
                

if __name__ == "__main__":
    asyncio.run(test_news_agent())