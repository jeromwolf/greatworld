"""
Data Normalizer - 데이터 정규화 및 표준화 유틸리티
다양한 소스의 데이터를 통일된 형식으로 변환
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date
import re
from dataclasses import dataclass, asdict
import json


@dataclass
class NormalizedStockData:
    """표준화된 주식 데이터"""
    # 기본 정보
    ticker: str              # 종목 코드/심볼
    name: str               # 종목명
    market: str             # 시장 (KOSPI, KOSDAQ, NYSE, NASDAQ)
    country: str            # 국가 (KR, US)
    
    # 가격 정보
    current_price: float    # 현재가
    previous_close: float   # 전일 종가
    change: float          # 변동액
    change_percent: float  # 변동률
    volume: int           # 거래량
    market_cap: float     # 시가총액
    
    # 시간 정보
    updated_at: str       # 업데이트 시간 (ISO format)
    timezone: str         # 시간대
    

@dataclass  
class NormalizedNewsData:
    """표준화된 뉴스 데이터"""
    title: str              # 제목
    description: str        # 요약/설명
    source: str            # 출처
    url: str              # URL
    published_at: str      # 발행 시간 (ISO format)
    language: str          # 언어 (ko, en)
    sentiment_score: Optional[float] = None  # 감성 점수
    relevance_score: Optional[float] = None  # 관련성 점수
    

@dataclass
class NormalizedFinancialData:
    """표준화된 재무 데이터"""
    # 기간 정보
    fiscal_year: int       # 회계연도
    fiscal_quarter: Optional[int]  # 분기 (없으면 연간)
    report_type: str       # 보고서 유형 (annual, quarterly)
    
    # 재무 데이터 (백만원/백만달러 단위)
    revenue: Optional[float] = None              # 매출액
    operating_income: Optional[float] = None     # 영업이익
    net_income: Optional[float] = None          # 순이익
    total_assets: Optional[float] = None        # 총자산
    total_liabilities: Optional[float] = None   # 총부채
    total_equity: Optional[float] = None        # 자본총계
    
    # 주요 비율
    operating_margin: Optional[float] = None    # 영업이익률
    net_margin: Optional[float] = None         # 순이익률
    roe: Optional[float] = None               # ROE
    debt_ratio: Optional[float] = None        # 부채비율
    
    # 통화 정보
    currency: str = "KRW"  # 통화 (KRW, USD)
    

class DataNormalizer:
    """데이터 정규화 클래스"""
    
    def __init__(self):
        # 시장 코드 매핑
        self.market_mapping = {
            # 한국
            "KS": "KOSPI",
            "KQ": "KOSDAQ", 
            "KOSPI": "KOSPI",
            "KOSDAQ": "KOSDAQ",
            # 미국
            "NYSE": "NYSE",
            "NASDAQ": "NASDAQ",
            "AMEX": "AMEX"
        }
        
        # 통화 심볼
        self.currency_symbols = {
            "₩": "KRW",
            "원": "KRW", 
            "$": "USD",
            "달러": "USD"
        }
        
    def normalize_stock_data(self, raw_data: Dict[str, Any], source: str = "unknown") -> NormalizedStockData:
        """
        주식 데이터 정규화
        
        Args:
            raw_data: 원본 데이터
            source: 데이터 소스 (yahoo, dart, etc.)
            
        Returns:
            NormalizedStockData 객체
        """
        # 소스별 매핑
        if source == "yahoo":
            return self._normalize_yahoo_stock_data(raw_data)
        elif source == "dart":
            return self._normalize_dart_stock_data(raw_data)
        else:
            return self._normalize_generic_stock_data(raw_data)
            
    def _normalize_yahoo_stock_data(self, data: Dict) -> NormalizedStockData:
        """Yahoo Finance 데이터 정규화"""
        price_data = data.get("price_data", {})
        
        # 심볼에서 시장 추출
        symbol = price_data.get("symbol", "")
        if "." in symbol:
            ticker, market_code = symbol.split(".")
            market = self.market_mapping.get(market_code, market_code)
            country = "KR" if market_code in ["KS", "KQ"] else "US"
        else:
            ticker = symbol
            market = "UNKNOWN"
            country = "US"  # 기본값
            
        return NormalizedStockData(
            ticker=ticker,
            name=price_data.get("name", ticker),
            market=market,
            country=country,
            current_price=float(price_data.get("current_price", 0)),
            previous_close=float(price_data.get("previous_close", 0)),
            change=float(price_data.get("change", 0)),
            change_percent=float(price_data.get("change_percent", 0)),
            volume=int(price_data.get("volume", 0)),
            market_cap=float(price_data.get("market_cap", 0)),
            updated_at=price_data.get("updated_at", datetime.now().isoformat()),
            timezone="Asia/Seoul" if country == "KR" else "America/New_York"
        )
        
    def _normalize_dart_stock_data(self, data: Dict) -> NormalizedStockData:
        """DART 데이터 정규화"""
        # DART는 주로 공시 데이터이므로 기본값 사용
        return NormalizedStockData(
            ticker=data.get("stock_code", ""),
            name=data.get("corp_name", ""),
            market=data.get("market", "KOSPI"),
            country="KR",
            current_price=0.0,  # DART는 가격정보 없음
            previous_close=0.0,
            change=0.0,
            change_percent=0.0,
            volume=0,
            market_cap=0.0,
            updated_at=datetime.now().isoformat(),
            timezone="Asia/Seoul"
        )
        
    def _normalize_generic_stock_data(self, data: Dict) -> NormalizedStockData:
        """일반 주식 데이터 정규화"""
        return NormalizedStockData(
            ticker=data.get("ticker", data.get("symbol", "")),
            name=data.get("name", data.get("company_name", "")),
            market=data.get("market", "UNKNOWN"),
            country=data.get("country", "US"),
            current_price=self._parse_number(data.get("price", data.get("current_price", 0))),
            previous_close=self._parse_number(data.get("prev_close", data.get("previous_close", 0))),
            change=self._parse_number(data.get("change", 0)),
            change_percent=self._parse_number(data.get("change_pct", data.get("change_percent", 0))),
            volume=int(self._parse_number(data.get("volume", 0))),
            market_cap=self._parse_number(data.get("market_cap", 0)),
            updated_at=self._parse_datetime(data.get("updated_at", data.get("timestamp", ""))),
            timezone=data.get("timezone", "UTC")
        )
        
    def normalize_news_data(self, raw_data: Dict[str, Any], source: str = "unknown") -> NormalizedNewsData:
        """
        뉴스 데이터 정규화
        
        Args:
            raw_data: 원본 데이터
            source: 데이터 소스 (naver, google, reddit, etc.)
            
        Returns:
            NormalizedNewsData 객체
        """
        # 소스별 처리
        if source == "naver":
            return self._normalize_naver_news(raw_data)
        elif source == "google":
            return self._normalize_google_news(raw_data)
        elif source == "reddit":
            return self._normalize_reddit_post(raw_data)
        else:
            return self._normalize_generic_news(raw_data)
            
    def _normalize_naver_news(self, data: Dict) -> NormalizedNewsData:
        """네이버 뉴스 정규화"""
        return NormalizedNewsData(
            title=self._clean_html(data.get("title", "")),
            description=self._clean_html(data.get("description", "")),
            source=data.get("source", "Naver News"),
            url=data.get("link", ""),
            published_at=self._parse_datetime(data.get("pubDate", "")),
            language="ko",
            sentiment_score=data.get("sentiment_score"),
            relevance_score=data.get("relevance_score")
        )
        
    def _normalize_google_news(self, data: Dict) -> NormalizedNewsData:
        """Google 뉴스 정규화"""
        return NormalizedNewsData(
            title=data.get("title", ""),
            description=data.get("description", data.get("summary", "")),
            source=data.get("source", {}).get("name", "Google News"),
            url=data.get("url", ""),
            published_at=self._parse_datetime(data.get("publishedAt", "")),
            language=data.get("language", "en"),
            sentiment_score=data.get("sentiment_score"),
            relevance_score=data.get("relevance_score")
        )
        
    def _normalize_reddit_post(self, data: Dict) -> NormalizedNewsData:
        """Reddit 포스트 정규화"""
        return NormalizedNewsData(
            title=data.get("title", ""),
            description=data.get("selftext", "")[:200],  # 본문 일부만
            source=f"r/{data.get('subreddit', 'unknown')}",
            url=data.get("url", ""),
            published_at=self._unix_to_iso(data.get("created_utc", 0)),
            language="en",  # Reddit은 주로 영어
            sentiment_score=data.get("sentiment_score"),
            relevance_score=data.get("score", 0) / 100  # 업보트를 관련성으로
        )
        
    def _normalize_generic_news(self, data: Dict) -> NormalizedNewsData:
        """일반 뉴스 정규화"""
        return NormalizedNewsData(
            title=data.get("title", data.get("headline", "")),
            description=data.get("description", data.get("summary", data.get("content", "")))[:500],
            source=data.get("source", data.get("provider", "Unknown")),
            url=data.get("url", data.get("link", "")),
            published_at=self._parse_datetime(
                data.get("published_at", data.get("publishedAt", data.get("pubDate", "")))
            ),
            language=data.get("language", "en"),
            sentiment_score=data.get("sentiment_score"),
            relevance_score=data.get("relevance_score")
        )
        
    def normalize_financial_data(self, raw_data: Dict[str, Any], source: str = "unknown") -> NormalizedFinancialData:
        """
        재무 데이터 정규화
        
        Args:
            raw_data: 원본 데이터
            source: 데이터 소스 (dart, sec, etc.)
            
        Returns:
            NormalizedFinancialData 객체
        """
        if source == "dart":
            return self._normalize_dart_financial(raw_data)
        elif source == "sec":
            return self._normalize_sec_financial(raw_data)
        else:
            return self._normalize_generic_financial(raw_data)
            
    def _normalize_dart_financial(self, data: Dict) -> NormalizedFinancialData:
        """DART 재무데이터 정규화"""
        statements = data.get("statements", {})
        bs = statements.get("balance_sheet", {})
        is_ = statements.get("income_statement", {})
        
        # 비율 계산
        revenue = is_.get("revenue", 0)
        operating_margin = (is_.get("operating_income", 0) / revenue * 100) if revenue > 0 else None
        net_margin = (is_.get("net_income", 0) / revenue * 100) if revenue > 0 else None
        
        total_equity = bs.get("total_equity", 0)
        total_assets = bs.get("total_assets", 0)
        roe = (is_.get("net_income", 0) / total_equity * 100) if total_equity > 0 else None
        debt_ratio = (bs.get("total_liabilities", 0) / total_equity * 100) if total_equity > 0 else None
        
        return NormalizedFinancialData(
            fiscal_year=int(data.get("year", datetime.now().year)),
            fiscal_quarter=self._extract_quarter(data.get("report_type", "")),
            report_type="quarterly" if self._extract_quarter(data.get("report_type", "")) else "annual",
            revenue=is_.get("revenue"),
            operating_income=is_.get("operating_income"),
            net_income=is_.get("net_income"),
            total_assets=bs.get("total_assets"),
            total_liabilities=bs.get("total_liabilities"),
            total_equity=bs.get("total_equity"),
            operating_margin=operating_margin,
            net_margin=net_margin,
            roe=roe,
            debt_ratio=debt_ratio,
            currency="KRW"
        )
        
    def _normalize_sec_financial(self, data: Dict) -> NormalizedFinancialData:
        """SEC 재무데이터 정규화"""
        # SEC 데이터는 다양한 형식이므로 기본 구조만
        return NormalizedFinancialData(
            fiscal_year=int(data.get("fiscal_year", datetime.now().year)),
            fiscal_quarter=data.get("fiscal_quarter"),
            report_type=data.get("form_type", "10-K"),
            revenue=self._parse_number(data.get("revenues", 0)) / 1_000_000,  # 백만 단위로
            operating_income=self._parse_number(data.get("operating_income", 0)) / 1_000_000,
            net_income=self._parse_number(data.get("net_income", 0)) / 1_000_000,
            total_assets=self._parse_number(data.get("total_assets", 0)) / 1_000_000,
            total_liabilities=self._parse_number(data.get("total_liabilities", 0)) / 1_000_000,
            total_equity=self._parse_number(data.get("stockholders_equity", 0)) / 1_000_000,
            currency="USD"
        )
        
    def _normalize_generic_financial(self, data: Dict) -> NormalizedFinancialData:
        """일반 재무데이터 정규화"""
        return NormalizedFinancialData(
            fiscal_year=int(data.get("year", data.get("fiscal_year", datetime.now().year))),
            fiscal_quarter=data.get("quarter"),
            report_type=data.get("report_type", "unknown"),
            revenue=self._parse_number(data.get("revenue", data.get("sales", 0))),
            operating_income=self._parse_number(data.get("operating_income", 0)),
            net_income=self._parse_number(data.get("net_income", data.get("earnings", 0))),
            total_assets=self._parse_number(data.get("assets", data.get("total_assets", 0))),
            total_liabilities=self._parse_number(data.get("liabilities", data.get("total_debt", 0))),
            total_equity=self._parse_number(data.get("equity", data.get("shareholders_equity", 0))),
            currency=self._detect_currency(data)
        )
        
    def _parse_number(self, value: Any) -> float:
        """숫자 파싱 (다양한 형식 지원)"""
        if isinstance(value, (int, float)):
            return float(value)
            
        if isinstance(value, str):
            # 쉼표, 통화 기호 제거
            cleaned = re.sub(r'[^\d.-]', '', value)
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
                
        return 0.0
        
    def _parse_datetime(self, value: Any) -> str:
        """날짜/시간 파싱"""
        if not value:
            return datetime.now().isoformat()
            
        if isinstance(value, datetime):
            return value.isoformat()
            
        if isinstance(value, str):
            # 다양한 날짜 형식 시도
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%Y년 %m월 %d일"
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
                    
        return datetime.now().isoformat()
        
    def _unix_to_iso(self, timestamp: Union[int, float]) -> str:
        """Unix timestamp를 ISO format으로 변환"""
        try:
            return datetime.fromtimestamp(timestamp).isoformat()
        except:
            return datetime.now().isoformat()
            
    def _clean_html(self, text: str) -> str:
        """HTML 태그 제거"""
        return re.sub(r'<[^>]+>', '', text)
        
    def _extract_quarter(self, report_type: str) -> Optional[int]:
        """보고서 타입에서 분기 추출"""
        if "1분기" in report_type or "Q1" in report_type:
            return 1
        elif "반기" in report_type or "2분기" in report_type or "Q2" in report_type:
            return 2
        elif "3분기" in report_type or "Q3" in report_type:
            return 3
        elif "4분기" in report_type or "Q4" in report_type:
            return 4
        return None
        
    def _detect_currency(self, data: Dict) -> str:
        """데이터에서 통화 감지"""
        # 명시적 통화 필드 확인
        if "currency" in data:
            return data["currency"]
            
        # 텍스트에서 통화 심볼 찾기
        text = json.dumps(data)
        for symbol, currency in self.currency_symbols.items():
            if symbol in text:
                return currency
                
        # 기본값
        return "USD"
        
    def to_dict(self, normalized_data: Union[NormalizedStockData, NormalizedNewsData, NormalizedFinancialData]) -> Dict:
        """정규화된 데이터를 딕셔너리로 변환"""
        return asdict(normalized_data)


# 테스트 함수
def test_normalizer():
    normalizer = DataNormalizer()
    
    # Yahoo 데이터 테스트
    yahoo_data = {
        "price_data": {
            "symbol": "005930.KS",
            "name": "Samsung Electronics",
            "current_price": 65000,
            "previous_close": 64000,
            "change": 1000,
            "change_percent": 1.56,
            "volume": 15000000,
            "market_cap": 400000000000000
        }
    }
    
    normalized = normalizer.normalize_stock_data(yahoo_data, "yahoo")
    print("\n=== Normalized Stock Data ===")
    print(json.dumps(normalizer.to_dict(normalized), indent=2, ensure_ascii=False))
    
    # 뉴스 데이터 테스트
    news_data = {
        "title": "삼성전자, 역대 최고 실적 달성",
        "description": "삼성전자가 3분기 매출 100조원을 돌파했다.",
        "link": "https://example.com/news/1",
        "pubDate": "2024-10-20 09:30:00"
    }
    
    normalized_news = normalizer.normalize_news_data(news_data, "naver")
    print("\n=== Normalized News Data ===")
    print(json.dumps(normalizer.to_dict(normalized_news), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    test_normalizer()