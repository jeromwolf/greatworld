"""
Price Agent - 실시간 주가 데이터 수집 에이전트
Yahoo Finance API를 통한 주가 정보 수집
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
import yfinance as yf
from cache.price_cache import cache_price_data


@dataclass
class StockPrice:
    """주가 데이터 모델"""
    symbol: str                 # 종목 심볼
    name: str                  # 종목명
    current_price: float       # 현재가
    previous_close: float      # 전일 종가
    change: float             # 등락액
    change_percent: float     # 등락률
    volume: int               # 거래량
    market_cap: float         # 시가총액
    day_high: float           # 당일 최고가
    day_low: float            # 당일 최저가
    week_52_high: float       # 52주 최고가
    week_52_low: float        # 52주 최저가
    updated_at: str           # 업데이트 시간


class PriceAgent:
    """실시간 주가 데이터 수집 에이전트"""
    
    def __init__(self):
        self.session = None
        # 한국 주식 종목코드 매핑
        self.kr_stock_mapping = {
            "삼성전자": "005930.KS",
            "SK하이닉스": "000660.KS",
            "네이버": "035420.KS",
            "카카오": "035720.KS",
            "LG에너지솔루션": "373220.KS",
            "현대차": "005380.KS",
            "기아": "000270.KS",
            "포스코": "005490.KS",
            "더본코리아": "354200.KQ",  # KOSDAQ은 .KQ
            "CJ": "001040.KS",
            "롯데": "004990.KS",
            "신세계": "004170.KS",
            "현대백화점": "069960.KS",
            "이마트": "139480.KS"
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    def _convert_to_yahoo_symbol(self, stock_name: str) -> str:
        """한국 주식명을 야후 파이낸스 심볼로 변환"""
        # 이미 심볼인 경우 (.KS, .KQ가 포함된 경우)
        if ".KS" in stock_name or ".KQ" in stock_name:
            return stock_name
            
        # 한국 주식명인 경우
        if stock_name in self.kr_stock_mapping:
            return self.kr_stock_mapping[stock_name]
            
        # 미국 주식 심볼인 경우 그대로 반환
        return stock_name.upper()
    
    @cache_price_data(data_type="realtime")
    async def get_stock_price(self, stock_name: str) -> Dict[str, Any]:
        """
        주식의 현재 가격 정보 조회
        
        Args:
            stock_name: 종목명 또는 심볼 (예: "삼성전자", "AAPL")
            
        Returns:
            주가 정보 딕셔너리
        """
        try:
            # 야후 파이낸스 심볼로 변환
            symbol = self._convert_to_yahoo_symbol(stock_name)
            print(f"[PRICE] Fetching price data for {stock_name} (symbol: {symbol})")
            
            # yfinance로 데이터 조회
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 실시간 가격 정보 (fast_info 사용)
            fast_info = ticker.fast_info
            
            # 추가 재무 지표 수집
            financial_info = {
                'pe_ratio': info.get('trailingPE', info.get('forwardPE', 0)),
                'pb_ratio': info.get('priceToBook', 0),
                'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
                'profit_margin': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0,
                'debt_to_equity': info.get('debtToEquity', 0),
                'current_ratio': info.get('currentRatio', 0),
                'beta': info.get('beta', 0),
                'eps': info.get('trailingEps', 0),
                'book_value': info.get('bookValue', 0)
            }
            
            # 주가 데이터 생성
            price_data = StockPrice(
                symbol=symbol,
                name=info.get('longName', stock_name),
                current_price=fast_info.get('lastPrice', 0),
                previous_close=fast_info.get('previousClose', 0),
                change=fast_info.get('lastPrice', 0) - fast_info.get('previousClose', 0),
                change_percent=((fast_info.get('lastPrice', 0) - fast_info.get('previousClose', 0)) / 
                               fast_info.get('previousClose', 1) * 100) if fast_info.get('previousClose', 0) > 0 else 0,
                volume=fast_info.get('lastVolume', 0),
                market_cap=fast_info.get('marketCap', 0),
                day_high=fast_info.get('dayHigh', 0),
                day_low=fast_info.get('dayLow', 0),
                week_52_high=fast_info.get('fiftyTwoWeekHigh', 0),
                week_52_low=fast_info.get('fiftyTwoWeekLow', 0),
                updated_at=datetime.now().isoformat()
            )
            
            return {
                "status": "success",
                "data_source": "REAL_DATA",
                "stock_name": stock_name,
                "price_data": asdict(price_data),
                "financial_info": financial_info
            }
            
        except Exception as e:
            print(f"[PRICE ERROR] Failed to fetch price for {stock_name}: {str(e)}")
            # 모의 데이터 반환
            return await self._get_mock_price(stock_name)
            
    async def _get_mock_price(self, stock_name: str) -> Dict[str, Any]:
        """모의 주가 데이터 반환"""
        import random
        
        base_price = random.randint(50000, 150000) if any(char >= '가' and char <= '힣' for char in stock_name) else random.randint(50, 300)
        change_percent = random.uniform(-3, 3)
        
        mock_data = StockPrice(
            symbol=stock_name,
            name=stock_name,
            current_price=base_price,
            previous_close=base_price / (1 + change_percent/100),
            change=base_price * change_percent / 100,
            change_percent=change_percent,
            volume=random.randint(1000000, 10000000),
            market_cap=base_price * random.randint(10000000, 100000000),
            day_high=base_price * 1.02,
            day_low=base_price * 0.98,
            week_52_high=base_price * 1.3,
            week_52_low=base_price * 0.7,
            updated_at=datetime.now().isoformat()
        )
        
        return {
            "status": "success",
            "data_source": "MOCK_DATA",
            "stock_name": stock_name,
            "price_data": asdict(mock_data),
            "warning": "⚠️ 실시간 주가 데이터를 가져올 수 없어 모의 데이터를 표시합니다."
        }
    
    async def get_price_history(self, 
                               stock_name: str, 
                               period: str = "1mo",
                               interval: str = "1d") -> Dict[str, Any]:
        """
        주가 히스토리 데이터 조회
        
        Args:
            stock_name: 종목명 또는 심볼
            period: 기간 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: 간격 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        """
        try:
            symbol = self._convert_to_yahoo_symbol(stock_name)
            ticker = yf.Ticker(symbol)
            
            # 히스토리 데이터 조회
            hist = ticker.history(period=period, interval=interval)
            
            # DataFrame을 딕셔너리 리스트로 변환
            history_data = []
            for date, row in hist.iterrows():
                history_data.append({
                    "date": date.isoformat(),
                    "open": row['Open'],
                    "high": row['High'],
                    "low": row['Low'],
                    "close": row['Close'],
                    "volume": row['Volume']
                })
            
            return {
                "status": "success",
                "data_source": "REAL_DATA",
                "stock_name": stock_name,
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "history": history_data
            }
            
        except Exception as e:
            print(f"[PRICE ERROR] Failed to fetch history for {stock_name}: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "data_source": "ERROR"
            }


# 테스트 함수
async def test_price_agent():
    async with PriceAgent() as agent:
        # 한국 주식 테스트
        kr_result = await agent.get_stock_price("삼성전자")
        print("\n=== 삼성전자 주가 정보 ===")
        print(json.dumps(kr_result, ensure_ascii=False, indent=2))
        
        # 미국 주식 테스트
        us_result = await agent.get_stock_price("AAPL")
        print("\n=== Apple 주가 정보 ===")
        print(json.dumps(us_result, ensure_ascii=False, indent=2))
        
        # 히스토리 테스트
        hist_result = await agent.get_price_history("삼성전자", period="1mo")
        print(f"\n=== 삼성전자 1개월 주가 히스토리 ({len(hist_result.get('history', []))}개 데이터) ===")
        

if __name__ == "__main__":
    asyncio.run(test_price_agent())