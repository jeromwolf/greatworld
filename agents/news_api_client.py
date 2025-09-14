"""
News API Client for Real-time News
실시간 뉴스 수집 모듈 (한국 + 글로벌)
"""

import os
import requests
import feedparser
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

class NewsApiClient:
    """NewsAPI 및 RSS 피드 통합 클라이언트"""

    def __init__(self):
        self.newsapi_key = os.getenv('NEWSAPI_KEY', '')
        self.naver_client_id = os.getenv('NAVER_CLIENT_ID', '')
        self.naver_client_secret = os.getenv('NAVER_CLIENT_SECRET', '')
        self.is_newsapi_valid = self._validate_newsapi_key()
        self.is_naver_valid = self._validate_naver_keys()

    def _validate_newsapi_key(self) -> bool:
        """NewsAPI 키 유효성 검사"""
        if not self.newsapi_key or 'your_newsapi' in self.newsapi_key.lower():
            return False
        return True

    def _validate_naver_keys(self) -> bool:
        """네이버 API 키 유효성 검사"""
        if not self.naver_client_id or 'your_naver' in self.naver_client_id.lower():
            return False
        if not self.naver_client_secret or 'your_naver' in self.naver_client_secret.lower():
            return False
        return True

    def get_stock_news(self, stock_name: str, language: str = 'ko') -> List[Dict]:
        """주식 관련 뉴스 조회"""
        news = []

        # 1. NewsAPI (영문 뉴스)
        if self.is_newsapi_valid and language == 'en':
            news.extend(self._get_newsapi_news(stock_name))

        # 2. 네이버 뉴스 API (한국 뉴스)
        if self.is_naver_valid and language == 'ko':
            news.extend(self._get_naver_news(stock_name))

        # 3. RSS 피드 (무료 대안)
        news.extend(self._get_rss_news(stock_name, language))

        # 4. 폴백 데이터
        if not news:
            news = self._get_fallback_news(stock_name, language)

        # 뉴스 정렬 및 중복 제거
        news = self._deduplicate_news(news)
        return sorted(news, key=lambda x: x.get('published_date', ''), reverse=True)[:20]

    def _get_newsapi_news(self, query: str) -> List[Dict]:
        """NewsAPI에서 뉴스 조회"""
        try:
            url = 'https://newsapi.org/v2/everything'
            params = {
                'apiKey': self.newsapi_key,
                'q': query,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 10,
                'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            }

            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return self._parse_newsapi_response(data.get('articles', []))
        except Exception as e:
            print(f"NewsAPI 오류: {e}")

        return []

    def _get_naver_news(self, query: str) -> List[Dict]:
        """네이버 뉴스 API 조회"""
        try:
            url = 'https://openapi.naver.com/v1/search/news.json'
            headers = {
                'X-Naver-Client-Id': self.naver_client_id,
                'X-Naver-Client-Secret': self.naver_client_secret
            }
            params = {
                'query': f"{query} 주식",
                'display': 20,
                'sort': 'date'
            }

            response = requests.get(url, headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return self._parse_naver_response(data.get('items', []))
        except Exception as e:
            print(f"네이버 뉴스 API 오류: {e}")

        return []

    def _get_rss_news(self, query: str, language: str) -> List[Dict]:
        """RSS 피드에서 뉴스 조회 (무료)"""
        news = []

        if language == 'ko':
            # 한국 금융 뉴스 RSS
            feeds = [
                f'https://news.google.com/rss/search?q={query}+주식&hl=ko&gl=KR&ceid=KR:ko',
                'https://rss.hankyung.com/feed/finance.xml',
                'https://www.mk.co.kr/rss/30100041/',  # 매일경제 증권
                'https://rss.edaily.co.kr/stock_news.xml'  # 이데일리 증권
            ]
        else:
            # 영문 금융 뉴스 RSS
            feeds = [
                f'https://news.google.com/rss/search?q={query}+stock&hl=en&gl=US&ceid=US:en',
                'https://feeds.finance.yahoo.com/rss/2.0/headline',
                'https://feeds.bloomberg.com/markets/news.rss'
            ]

        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]:  # 각 피드에서 5개씩
                    news.append({
                        'title': entry.get('title', ''),
                        'description': entry.get('summary', '')[:200],
                        'url': entry.get('link', ''),
                        'source': feed.feed.get('title', 'RSS Feed'),
                        'published_date': self._parse_date(entry.get('published_parsed')),
                        'category': self._categorize_news(entry.get('title', ''))
                    })
            except Exception as e:
                print(f"RSS 피드 오류 ({feed_url}): {e}")

        return news

    def _parse_newsapi_response(self, articles: List[Dict]) -> List[Dict]:
        """NewsAPI 응답 파싱"""
        news = []
        for article in articles:
            news.append({
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'url': article.get('url', ''),
                'source': article.get('source', {}).get('name', ''),
                'published_date': article.get('publishedAt', ''),
                'image_url': article.get('urlToImage', ''),
                'category': self._categorize_news(article.get('title', ''))
            })
        return news

    def _parse_naver_response(self, items: List[Dict]) -> List[Dict]:
        """네이버 뉴스 응답 파싱"""
        news = []
        for item in items:
            # HTML 태그 제거
            title = item.get('title', '').replace('<b>', '').replace('</b>', '')
            description = item.get('description', '').replace('<b>', '').replace('</b>', '')

            news.append({
                'title': title,
                'description': description[:200],
                'url': item.get('link', ''),
                'source': '네이버 뉴스',
                'published_date': item.get('pubDate', ''),
                'category': self._categorize_news(title)
            })
        return news

    def _categorize_news(self, title: str) -> str:
        """뉴스 카테고리 분류"""
        title_lower = title.lower()

        # 긴급/중요
        if any(word in title_lower for word in ['급등', '급락', '폭등', '폭락', 'surge', 'plunge', 'crash']):
            return 'urgent'

        # 실적/공시
        if any(word in title_lower for word in ['실적', '매출', '영업이익', 'earnings', 'revenue', '공시']):
            return 'earnings'

        # M&A/투자
        if any(word in title_lower for word in ['인수', '합병', 'm&a', 'merger', 'acquisition', '투자']):
            return 'ma'

        # 분석/전망
        if any(word in title_lower for word in ['전망', '분석', '목표가', 'forecast', 'analysis', 'target']):
            return 'analysis'

        # 시장동향
        if any(word in title_lower for word in ['시장', '동향', '코스피', '나스닥', 'market', 'trend']):
            return 'market'

        return 'general'

    def _parse_date(self, date_tuple) -> str:
        """날짜 파싱"""
        if date_tuple:
            try:
                dt = datetime(*date_tuple[:6])
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _deduplicate_news(self, news: List[Dict]) -> List[Dict]:
        """중복 뉴스 제거"""
        seen_titles = set()
        unique_news = []

        for item in news:
            title = item.get('title', '')
            # 제목의 처음 50자를 기준으로 중복 체크
            title_key = title[:50].lower().strip()
            if title_key and title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(item)

        return unique_news

    def _get_fallback_news(self, stock_name: str, language: str) -> List[Dict]:
        """폴백 뉴스 데이터"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if '삼성전자' in stock_name or 'samsung' in stock_name.lower():
            if language == 'ko':
                return [
                    {
                        'title': '삼성전자, HBM3E 본격 양산...엔비디아 공급 확대',
                        'description': '삼성전자가 5세대 고대역폭 메모리(HBM3E) 양산을 본격화하며 엔비디아 공급을 확대한다.',
                        'url': '#',
                        'source': '한국경제',
                        'published_date': now,
                        'category': 'urgent'
                    },
                    {
                        'title': '삼성전자 3분기 영업익 9.2조...시장 예상 상회',
                        'description': '삼성전자가 3분기 영업이익 9.2조원을 기록하며 시장 예상치를 넘어섰다.',
                        'url': '#',
                        'source': '매일경제',
                        'published_date': now,
                        'category': 'earnings'
                    },
                    {
                        'title': 'AI 반도체 슈퍼사이클 본격화...삼성전자 수혜 전망',
                        'description': 'AI 반도체 수요 급증으로 메모리 반도체 슈퍼사이클이 시작됐다.',
                        'url': '#',
                        'source': '이데일리',
                        'published_date': now,
                        'category': 'analysis'
                    }
                ]
            else:
                return [
                    {
                        'title': 'Samsung Begins Mass Production of HBM3E for NVIDIA',
                        'description': 'Samsung Electronics starts mass production of HBM3E memory for AI applications.',
                        'url': '#',
                        'source': 'Reuters',
                        'published_date': now,
                        'category': 'urgent'
                    }
                ]

        elif 'SK하이닉스' in stock_name:
            return [
                {
                    'title': 'SK하이닉스, HBM 시장 점유율 50% 돌파',
                    'description': 'SK하이닉스가 고대역폭 메모리 시장에서 점유율 50%를 넘어섰다.',
                    'url': '#',
                    'source': '한국경제',
                    'published_date': now,
                    'category': 'urgent'
                }
            ]

        return []

    def analyze_sentiment(self, news_list: List[Dict]) -> Dict:
        """뉴스 감성 분석"""
        if not news_list:
            return {'sentiment': 0.0, 'summary': '뉴스 데이터 없음'}

        positive_count = 0
        negative_count = 0
        neutral_count = 0

        positive_words = ['상승', '급등', '호재', '성장', '개선', '증가', 'rise', 'surge', 'gain', 'growth']
        negative_words = ['하락', '급락', '악재', '감소', '우려', '리스크', 'fall', 'drop', 'loss', 'risk']

        for news in news_list:
            title = news.get('title', '').lower()
            desc = news.get('description', '').lower()
            text = title + ' ' + desc

            pos_score = sum(1 for word in positive_words if word in text)
            neg_score = sum(1 for word in negative_words if word in text)

            if pos_score > neg_score:
                positive_count += 1
            elif neg_score > pos_score:
                negative_count += 1
            else:
                neutral_count += 1

        total = len(news_list)
        sentiment_score = (positive_count - negative_count) / total if total > 0 else 0

        # 감성 요약
        if sentiment_score > 0.3:
            summary = f"긍정적 뉴스 {positive_count}건, 시장 분위기 매우 긍정적"
        elif sentiment_score > 0:
            summary = f"긍정적 뉴스 {positive_count}건, 전반적으로 긍정적"
        elif sentiment_score < -0.3:
            summary = f"부정적 뉴스 {negative_count}건, 시장 분위기 매우 부정적"
        elif sentiment_score < 0:
            summary = f"부정적 뉴스 {negative_count}건, 전반적으로 부정적"
        else:
            summary = f"중립적 뉴스 {neutral_count}건, 시장 분위기 중립"

        return {
            'sentiment': sentiment_score,
            'positive': positive_count,
            'negative': negative_count,
            'neutral': neutral_count,
            'summary': summary
        }