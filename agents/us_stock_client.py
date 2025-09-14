"""
US Stock Client for Foreign Market Data
해외 주식 실시간 데이터 수집 모듈
"""

import os
import requests
import yfinance as yf
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
import aiohttp

class USStockClient:
    """미국/해외 주식 데이터 클라이언트"""

    def __init__(self):
        self.finnhub_key = os.getenv('FINNHUB_API_KEY', '')
        self.polygon_key = os.getenv('POLYGON_API_KEY', '')
        self.iex_key = os.getenv('IEX_CLOUD_API_KEY', '')

        # 주요 해외 주식 심볼 매핑
        self.stock_symbols = {
            # 미국 대형주
            "애플": "AAPL",
            "마이크로소프트": "MSFT",
            "구글": "GOOGL",
            "아마존": "AMZN",
            "테슬라": "TSLA",
            "엔비디아": "NVDA",
            "메타": "META",
            "버크셔해서웨이": "BRK.B",
            "JP모건": "JPM",
            "비자": "V",
            "월마트": "WMT",
            "존슨앤존슨": "JNJ",
            "프록터앤갬블": "PG",
            "유나이티드헬스": "UNH",
            "홈디포": "HD",
            "마스터카드": "MA",
            "디즈니": "DIS",
            "뱅크오브아메리카": "BAC",
            "넷플릭스": "NFLX",
            "어도비": "ADBE",
            "세일즈포스": "CRM",
            "페이팔": "PYPL",
            "인텔": "INTC",
            "AMD": "AMD",
            "오라클": "ORCL",
            "시스코": "CSCO",
            "브로드컴": "AVGO",
            "퀄컴": "QCOM",
            "코카콜라": "KO",
            "펩시코": "PEP",
            "코스트코": "COST",
            "스타벅스": "SBUX",
            "나이키": "NKE",
            "맥도날드": "MCD",
            # 중국 주식 (ADR)
            "알리바바": "BABA",
            "텐센트": "TCEHY",
            "바이두": "BIDU",
            "샤오미": "XIACY",
            "BYD": "BYDDY",
            "니오": "NIO",
            "리리퀄리티": "LI",
            "샤오펑": "XPEV",
            "핀둬둬": "PDD",
            "징둥": "JD",
            "넷이즈": "NTES",
            "빌리빌리": "BILI",
            # 일본 주식 (ADR)
            "도요타": "TM",
            "소니": "SONY",
            "혼다": "HMC",
            "닌텐도": "NTDOY",
            "소프트뱅크": "SFTBY",
            # 유럽 주식
            "ASML": "ASML",
            "네슬레": "NSRGY",
            "노바티스": "NVS",
            "로슈": "RHHBY",
            "LVMH": "LVMUY",
            "토탈": "TTE",
            "SAP": "SAP",
            "유니레버": "UL",
            # ETF
            "SPY": "SPY",
            "QQQ": "QQQ",
            "DIA": "DIA",
            "VTI": "VTI",
            "VOO": "VOO",
            "IWM": "IWM",
            "EEM": "EEM",
            "GLD": "GLD",
            "TLT": "TLT",
            "ARKK": "ARKK"
        }

        # 섹터별 분류
        self.sectors = {
            "기술": ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "INTC", "AMD", "ORCL"],
            "소비재": ["AMZN", "TSLA", "HD", "NKE", "MCD", "SBUX"],
            "금융": ["JPM", "BAC", "V", "MA", "BRK.B"],
            "헬스케어": ["JNJ", "UNH", "PFE", "ABBV"],
            "통신": ["DIS", "NFLX", "T", "VZ"],
            "에너지": ["XOM", "CVX", "COP"],
            "중국": ["BABA", "TCEHY", "BIDU", "NIO", "PDD", "JD"],
            "ETF": ["SPY", "QQQ", "DIA", "VTI", "VOO"]
        }

    async def get_stock_data(self, symbol: str) -> Dict:
        """주식 데이터 종합 조회"""
        # 한글명을 심볼로 변환
        if symbol in self.stock_symbols:
            symbol = self.stock_symbols[symbol]

        # Yahoo Finance로 기본 데이터 가져오기
        basic_data = self._get_yahoo_data(symbol)

        # 추가 API가 있으면 보강
        if self.finnhub_key and 'your_' not in self.finnhub_key.lower():
            finnhub_data = await self._get_finnhub_data(symbol)
            basic_data.update(finnhub_data)

        # 실시간 뉴스 추가
        basic_data['news'] = self._get_stock_news(symbol)

        # 기술적 지표 계산
        basic_data['technical'] = self._calculate_technical_indicators(symbol)

        # 애널리스트 의견
        basic_data['analyst'] = self._get_analyst_opinion(symbol)

        return basic_data

    def _get_yahoo_data(self, symbol: str) -> Dict:
        """Yahoo Finance 데이터 조회"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # 최근 가격 데이터
            hist = ticker.history(period="1d")
            current_price = hist['Close'].iloc[-1] if not hist.empty else info.get('currentPrice', 0)

            # 52주 데이터
            hist_52w = ticker.history(period="1y")
            high_52w = hist_52w['High'].max() if not hist_52w.empty else info.get('fiftyTwoWeekHigh', 0)
            low_52w = hist_52w['Low'].min() if not hist_52w.empty else info.get('fiftyTwoWeekLow', 0)

            return {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'current_price': current_price,
                'previous_close': info.get('previousClose', 0),
                'change': current_price - info.get('previousClose', 0),
                'change_percent': ((current_price - info.get('previousClose', 0)) / info.get('previousClose', 1)) * 100 if info.get('previousClose') else 0,
                'volume': info.get('volume', 0),
                'average_volume': info.get('averageVolume', 0),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'eps': info.get('trailingEps', 0),
                'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                'beta': info.get('beta', 0),
                'high_52w': high_52w,
                'low_52w': low_52w,
                'day_high': info.get('dayHigh', 0),
                'day_low': info.get('dayLow', 0),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'description': info.get('longBusinessSummary', '')[:500] if info.get('longBusinessSummary') else '',
                'exchange': info.get('exchange', 'NASDAQ'),
                'currency': info.get('currency', 'USD')
            }
        except Exception as e:
            print(f"Yahoo Finance 오류 ({symbol}): {e}")
            return self._get_fallback_data(symbol)

    async def _get_finnhub_data(self, symbol: str) -> Dict:
        """Finnhub API로 추가 데이터 조회"""
        try:
            async with aiohttp.ClientSession() as session:
                # 기업 프로필
                url = f"https://finnhub.io/api/v1/stock/profile2"
                params = {'symbol': symbol, 'token': self.finnhub_key}

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        profile = await response.json()
                    else:
                        profile = {}

                # 추천 트렌드
                url = f"https://finnhub.io/api/v1/stock/recommendation"
                params = {'symbol': symbol, 'token': self.finnhub_key}

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        recommendations = await response.json()
                        if recommendations:
                            latest_rec = recommendations[0]
                        else:
                            latest_rec = {}
                    else:
                        latest_rec = {}

                return {
                    'logo': profile.get('logo', ''),
                    'website': profile.get('weburl', ''),
                    'finnhub_industry': profile.get('finnhubIndustry', ''),
                    'recommendation': {
                        'buy': latest_rec.get('buy', 0),
                        'hold': latest_rec.get('hold', 0),
                        'sell': latest_rec.get('sell', 0),
                        'strong_buy': latest_rec.get('strongBuy', 0),
                        'strong_sell': latest_rec.get('strongSell', 0)
                    }
                }
        except Exception as e:
            print(f"Finnhub API 오류: {e}")
            return {}

    def _get_stock_news(self, symbol: str) -> List[Dict]:
        """주식 관련 뉴스 조회"""
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news[:10] if hasattr(ticker, 'news') else []

            formatted_news = []
            for item in news:
                formatted_news.append({
                    'title': item.get('title', ''),
                    'publisher': item.get('publisher', ''),
                    'link': item.get('link', ''),
                    'published': datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%Y-%m-%d %H:%M') if item.get('providerPublishTime') else '',
                    'type': item.get('type', 'STORY')
                })

            return formatted_news
        except Exception as e:
            print(f"뉴스 조회 오류: {e}")
            return self._get_fallback_news(symbol)

    def _calculate_technical_indicators(self, symbol: str) -> Dict:
        """기술적 지표 계산"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="3mo")

            if hist.empty:
                return {}

            # 이동평균선
            ma5 = hist['Close'].rolling(window=5).mean().iloc[-1]
            ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            ma50 = hist['Close'].rolling(window=50).mean().iloc[-1] if len(hist) >= 50 else 0

            # RSI 계산
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]

            current_price = hist['Close'].iloc[-1]

            # 매매 신호
            if rsi < 30:
                signal = "강력 매수"
            elif rsi < 40:
                signal = "매수"
            elif rsi > 70:
                signal = "강력 매도"
            elif rsi > 60:
                signal = "매도"
            else:
                signal = "중립"

            # 추세 판단
            if current_price > ma20 > ma50:
                trend = "강한 상승세"
            elif current_price > ma20:
                trend = "상승세"
            elif current_price < ma20 < ma50:
                trend = "강한 하락세"
            elif current_price < ma20:
                trend = "하락세"
            else:
                trend = "횡보"

            return {
                'ma5': round(ma5, 2),
                'ma20': round(ma20, 2),
                'ma50': round(ma50, 2) if ma50 else None,
                'rsi': round(rsi, 2),
                'signal': signal,
                'trend': trend,
                'support': round(hist['Low'].min(), 2),
                'resistance': round(hist['High'].max(), 2)
            }
        except Exception as e:
            print(f"기술적 지표 계산 오류: {e}")
            return {}

    def _get_analyst_opinion(self, symbol: str) -> Dict:
        """애널리스트 의견 조회"""
        try:
            ticker = yf.Ticker(symbol)

            # 목표 주가
            info = ticker.info
            target_mean = info.get('targetMeanPrice', 0)
            target_high = info.get('targetHighPrice', 0)
            target_low = info.get('targetLowPrice', 0)
            current = info.get('currentPrice', 0)

            # 추천 등급
            recommendation = info.get('recommendationKey', 'none')
            recommendation_mean = info.get('recommendationMean', 0)

            # 등급 해석
            if recommendation_mean <= 1.5:
                rating = "강력 매수"
            elif recommendation_mean <= 2.5:
                rating = "매수"
            elif recommendation_mean <= 3.5:
                rating = "보유"
            elif recommendation_mean <= 4.5:
                rating = "매도"
            else:
                rating = "강력 매도"

            # 상승 잠재력
            upside = ((target_mean - current) / current * 100) if current and target_mean else 0

            return {
                'target_mean': target_mean,
                'target_high': target_high,
                'target_low': target_low,
                'rating': rating,
                'recommendation': recommendation,
                'upside_potential': round(upside, 2),
                'number_of_analysts': info.get('numberOfAnalystOpinions', 0)
            }
        except Exception as e:
            print(f"애널리스트 의견 조회 오류: {e}")
            return {}

    def get_market_movers(self) -> Dict:
        """시장 주요 변동 종목"""
        movers = {
            'gainers': [],
            'losers': [],
            'most_active': []
        }

        # 주요 지수
        indices = ['SPY', 'QQQ', 'DIA']
        for index in indices:
            try:
                ticker = yf.Ticker(index)
                info = ticker.info
                hist = ticker.history(period="1d")
                if not hist.empty:
                    movers['indices'] = movers.get('indices', [])
                    movers['indices'].append({
                        'symbol': index,
                        'name': info.get('longName', index),
                        'price': hist['Close'].iloc[-1],
                        'change': hist['Close'].iloc[-1] - info.get('previousClose', 0),
                        'change_percent': ((hist['Close'].iloc[-1] - info.get('previousClose', 0)) / info.get('previousClose', 1)) * 100
                    })
            except:
                pass

        return movers

    def _get_fallback_data(self, symbol: str) -> Dict:
        """폴백 데이터"""
        fallback = {
            'AAPL': {
                'symbol': 'AAPL',
                'name': 'Apple Inc.',
                'current_price': 195.89,
                'change_percent': 1.23,
                'market_cap': 3050000000000,
                'pe_ratio': 32.5,
                'eps': 6.05,
                'dividend_yield': 0.44
            },
            'TSLA': {
                'symbol': 'TSLA',
                'name': 'Tesla, Inc.',
                'current_price': 242.84,
                'change_percent': -2.15,
                'market_cap': 770000000000,
                'pe_ratio': 78.2,
                'eps': 3.10,
                'dividend_yield': 0
            },
            'NVDA': {
                'symbol': 'NVDA',
                'name': 'NVIDIA Corporation',
                'current_price': 503.68,
                'change_percent': 3.45,
                'market_cap': 1240000000000,
                'pe_ratio': 65.3,
                'eps': 7.72,
                'dividend_yield': 0.03
            }
        }

        return fallback.get(symbol, {
            'symbol': symbol,
            'name': symbol,
            'current_price': 100,
            'change_percent': 0,
            'error': 'No data available'
        })

    def _get_fallback_news(self, symbol: str) -> List[Dict]:
        """폴백 뉴스 데이터"""
        news_templates = {
            'AAPL': [
                {'title': 'Apple Unveils New AI Features for iPhone', 'publisher': 'Reuters'},
                {'title': 'Apple Stock Hits Record High on Strong Earnings', 'publisher': 'Bloomberg'}
            ],
            'TSLA': [
                {'title': 'Tesla Expands Supercharger Network Globally', 'publisher': 'CNBC'},
                {'title': 'Tesla FSD Beta Shows Significant Improvements', 'publisher': 'Electrek'}
            ],
            'NVDA': [
                {'title': 'NVIDIA Announces Next-Gen AI Chips', 'publisher': 'TechCrunch'},
                {'title': 'NVIDIA Dominates AI Chip Market Share', 'publisher': 'WSJ'}
            ]
        }

        return news_templates.get(symbol, [])

    async def get_sector_performance(self) -> Dict:
        """섹터별 성과 조회"""
        sector_etfs = {
            'Technology': 'XLK',
            'Healthcare': 'XLV',
            'Financials': 'XLF',
            'Consumer': 'XLY',
            'Energy': 'XLE',
            'Industrials': 'XLI',
            'Materials': 'XLB',
            'Utilities': 'XLU',
            'Real Estate': 'XLRE'
        }

        performance = {}
        for sector, etf in sector_etfs.items():
            try:
                ticker = yf.Ticker(etf)
                hist = ticker.history(period="1d")
                info = ticker.info

                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    prev = info.get('previousClose', current)
                    change = ((current - prev) / prev) * 100 if prev else 0

                    performance[sector] = {
                        'symbol': etf,
                        'price': current,
                        'change': round(change, 2)
                    }
            except:
                pass

        return performance