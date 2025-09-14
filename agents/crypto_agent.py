"""
Crypto Agent - 암호화폐 데이터 수집 및 분석 에이전트
CoinGecko API를 활용한 실시간 암호화폐 가격 및 정보 수집
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
import aiohttp
from agents.sentiment_agent import SentimentAgent

@dataclass
class CryptoData:
    """암호화폐 데이터 모델"""
    symbol: str
    name: str
    current_price_usd: float
    current_price_krw: float
    market_cap_usd: float
    market_cap_krw: float
    market_cap_rank: int
    price_change_24h_usd: float
    price_change_24h_krw: float
    price_change_percentage_24h: float
    price_change_percentage_7d: float
    price_change_percentage_30d: float
    circulating_supply: float
    total_supply: float
    max_supply: float
    volume_24h_usd: float
    volume_24h_krw: float
    high_24h_usd: float
    high_24h_krw: float
    low_24h_usd: float
    low_24h_krw: float
    ath_usd: float
    ath_krw: float
    ath_date: str
    atl_usd: float
    atl_krw: float
    atl_date: str
    last_updated: str

class CryptoAgent:
    """암호화폐 데이터 수집 에이전트"""
    
    def __init__(self):
        self.session = None
        self.coingecko_url = "https://api.coingecko.com/api/v3"
        
        # 한글명 -> 심볼 매핑
        self.crypto_mapping = {
            "비트코인": "bitcoin",
            "이더리움": "ethereum", 
            "도지코인": "dogecoin",
            "리플": "ripple",
            "에이다": "cardano",
            "체인링크": "chainlink",
            "라이트코인": "litecoin",
            "솔라나": "solana",
            "바이낸스": "binancecoin",
            "폴리곤": "polygon",
            "아발란체": "avalanche"
        }
        
        # 심볼 -> ID 매핑
        self.symbol_to_id = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "DOGE": "dogecoin", 
            "XRP": "ripple",
            "ADA": "cardano",
            "LINK": "chainlink",
            "LTC": "litecoin",
            "SOL": "solana",
            "BNB": "binancecoin",
            "MATIC": "polygon",
            "AVAX": "avalanche"
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def normalize_crypto_name(self, crypto_name: str) -> str:
        """암호화폐 이름/심볼을 CoinGecko ID로 변환"""
        crypto_name = crypto_name.strip().lower()
        
        # 한글명 매핑
        if crypto_name in self.crypto_mapping:
            return self.crypto_mapping[crypto_name]
            
        # 심볼 매핑
        upper_name = crypto_name.upper()
        if upper_name in self.symbol_to_id:
            return self.symbol_to_id[upper_name]
            
        # 영문명 직접 매핑
        english_names = {
            "bitcoin": "bitcoin",
            "ethereum": "ethereum", 
            "dogecoin": "dogecoin",
            "ripple": "ripple",
            "cardano": "cardano",
            "chainlink": "chainlink",
            "litecoin": "litecoin",
            "solana": "solana",
            "binance coin": "binancecoin",
            "polygon": "polygon",
            "avalanche": "avalanche"
        }
        
        return english_names.get(crypto_name, crypto_name)
    
    async def get_crypto_data(self, crypto_name: str) -> Dict[str, Any]:
        """
        암호화폐 실시간 데이터 조회
        
        Args:
            crypto_name: 암호화폐명 또는 심볼
            
        Returns:
            암호화폐 데이터 딕셔너리
        """
        try:
            coin_id = self.normalize_crypto_name(crypto_name)
            print(f"[CRYPTO] Fetching data for {crypto_name} (coin_id: {coin_id})", flush=True)
            
            # CoinGecko API 호출
            url = f"{self.coingecko_url}/coins/{coin_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false"
            }
            
            print(f"[CRYPTO] API URL: {url}", flush=True)
            async with self.session.get(url, params=params) as response:
                print(f"[CRYPTO] Response status: {response.status}", flush=True)
                if response.status == 200:
                    data = await response.json()
                    print(f"[CRYPTO] Data received successfully", flush=True)
                    return self._parse_crypto_data(data, crypto_name)
                else:
                    # API 실패 시 모의 데이터 반환
                    text = await response.text()
                    print(f"[CRYPTO] API failed with status {response.status}: {text[:200]}", flush=True)
                    return await self._get_mock_crypto_data(crypto_name)
                    
        except Exception as e:
            print(f"[CRYPTO] Error fetching data for {crypto_name}: {e}", flush=True)
            return await self._get_mock_crypto_data(crypto_name)
    
    def _parse_crypto_data(self, data: dict, original_name: str) -> Dict[str, Any]:
        """CoinGecko API 응답 파싱 - USD와 KRW 모두 파싱"""
        market_data = data.get("market_data", {})
        
        crypto_info = CryptoData(
            symbol=data.get("symbol", "").upper(),
            name=data.get("name", original_name),
            current_price_usd=market_data.get("current_price", {}).get("usd", 0),
            current_price_krw=market_data.get("current_price", {}).get("krw", 0),
            market_cap_usd=market_data.get("market_cap", {}).get("usd", 0),
            market_cap_krw=market_data.get("market_cap", {}).get("krw", 0),
            market_cap_rank=market_data.get("market_cap_rank", 0),
            price_change_24h_usd=market_data.get("price_change_24h", 0),
            price_change_24h_krw=market_data.get("price_change_24h_in_currency", {}).get("krw", 0),
            price_change_percentage_24h=market_data.get("price_change_percentage_24h", 0),
            price_change_percentage_7d=market_data.get("price_change_percentage_7d", 0),
            price_change_percentage_30d=market_data.get("price_change_percentage_30d", 0),
            circulating_supply=market_data.get("circulating_supply", 0),
            total_supply=market_data.get("total_supply", 0),
            max_supply=market_data.get("max_supply", 0),
            volume_24h_usd=market_data.get("total_volume", {}).get("usd", 0),
            volume_24h_krw=market_data.get("total_volume", {}).get("krw", 0),
            high_24h_usd=market_data.get("high_24h", {}).get("usd", 0),
            high_24h_krw=market_data.get("high_24h", {}).get("krw", 0),
            low_24h_usd=market_data.get("low_24h", {}).get("usd", 0),
            low_24h_krw=market_data.get("low_24h", {}).get("krw", 0),
            ath_usd=market_data.get("ath", {}).get("usd", 0),
            ath_krw=market_data.get("ath", {}).get("krw", 0),
            ath_date=market_data.get("ath_date", {}).get("usd", ""),
            atl_usd=market_data.get("atl", {}).get("usd", 0),
            atl_krw=market_data.get("atl", {}).get("krw", 0),
            atl_date=market_data.get("atl_date", {}).get("usd", ""),
            last_updated=market_data.get("last_updated", datetime.now().isoformat())
        )
        
        return {
            "status": "success",
            "crypto_name": original_name,
            "data_source": "REAL_DATA",
            "crypto_data": asdict(crypto_info),
            "message": f"CoinGecko에서 {original_name} 데이터 수집 완료"
        }
    
    async def _get_mock_crypto_data(self, crypto_name: str) -> Dict[str, Any]:
        """API 실패 시 모의 암호화폐 데이터 반환"""
        # 기본 가격 설정
        base_prices = {
            "bitcoin": 45000,
            "ethereum": 3000,
            "dogecoin": 0.08,
            "ripple": 0.6,
            "cardano": 0.5,
            "chainlink": 15,
            "litecoin": 70,
            "solana": 100,
            "binancecoin": 300,
            "polygon": 0.9,
            "avalanche": 25
        }
        
        coin_id = self.normalize_crypto_name(crypto_name)
        base_price = base_prices.get(coin_id, 1.0)
        
        # 대략적인 USD-KRW 환율 (1400원)
        usd_to_krw = 1400
        
        mock_crypto = CryptoData(
            symbol=coin_id.upper()[:4] if coin_id else "UNKN",
            name=crypto_name,
            current_price_usd=base_price,
            current_price_krw=base_price * usd_to_krw,
            market_cap_usd=base_price * 19000000,
            market_cap_krw=base_price * 19000000 * usd_to_krw,
            market_cap_rank=1,
            price_change_24h_usd=base_price * 0.02,
            price_change_24h_krw=base_price * 0.02 * usd_to_krw,
            price_change_percentage_24h=2.1,
            price_change_percentage_7d=5.3,
            price_change_percentage_30d=-1.2,
            circulating_supply=19000000,
            total_supply=21000000,
            max_supply=21000000,
            volume_24h_usd=base_price * 500000,
            volume_24h_krw=base_price * 500000 * usd_to_krw,
            high_24h_usd=base_price * 1.05,
            high_24h_krw=base_price * 1.05 * usd_to_krw,
            low_24h_usd=base_price * 0.95,
            low_24h_krw=base_price * 0.95 * usd_to_krw,
            ath_usd=base_price * 3,
            ath_krw=base_price * 3 * usd_to_krw,
            ath_date="2021-11-10T00:00:00.000Z",
            atl_usd=base_price * 0.1,
            atl_krw=base_price * 0.1 * usd_to_krw,
            atl_date="2020-03-20T00:00:00.000Z",
            last_updated=datetime.now().isoformat()
        )
        
        return {
            "status": "success",
            "crypto_name": crypto_name,
            "data_source": "MOCK_DATA", 
            "crypto_data": asdict(mock_crypto),
            "message": f"⚠️ 모의 데이터 - CoinGecko API 연결 실패"
        }
    
    async def get_crypto_price_history(self, crypto_name: str, days: int = 7) -> Dict[str, Any]:
        """
        암호화폐 가격 히스토리 조회
        
        Args:
            crypto_name: 암호화폐명
            days: 조회 일수
        """
        try:
            coin_id = self.normalize_crypto_name(crypto_name)
            
            url = f"{self.coingecko_url}/coins/{coin_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": str(days),
                "interval": "hourly" if days <= 1 else "daily"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    prices = data.get("prices", [])
                    
                    # 시간별 가격 데이터 변환
                    price_history = []
                    for timestamp, price in prices:
                        price_history.append({
                            "timestamp": timestamp,
                            "date": datetime.fromtimestamp(timestamp/1000).strftime("%Y-%m-%d %H:%M"),
                            "price": price
                        })
                    
                    return {
                        "status": "success",
                        "crypto_name": crypto_name,
                        "period_days": days,
                        "data_source": "REAL_DATA",
                        "history": price_history[-50:],  # 최근 50개 데이터포인트
                        "message": f"{crypto_name} {days}일 가격 히스토리"
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"가격 히스토리 조회 실패: {response.status}"
                    }
                    
        except Exception as e:
            return {
                "status": "error", 
                "message": f"가격 히스토리 조회 중 오류: {str(e)}"
            }
    
    async def analyze_crypto(self, crypto_name: str) -> Dict[str, Any]:
        """
        암호화폐 종합 분석
        
        Args:
            crypto_name: 암호화폐명
        """
        # 기본 데이터 조회
        crypto_result = await self.get_crypto_data(crypto_name)
        
        if crypto_result["status"] != "success":
            return crypto_result
            
        crypto_data = crypto_result["crypto_data"]
        
        # 감성 분석 (뉴스 기반)
        try:
            async with SentimentAgent() as sentiment_agent:
                sentiment_result = await sentiment_agent.analyze_sentiment(
                    f"{crypto_name} crypto cryptocurrency", 
                    is_korean=False
                )
        except Exception as e:
            sentiment_result = {
                "overall_sentiment": 0.0,
                "sentiment_label": "중립적",
                "recommendation": "관망"
            }
        
        # 기술적 지표 계산
        technical_signals = self._calculate_crypto_signals(crypto_data)
        
        return {
            "status": "success",
            "crypto_name": crypto_name,
            "data_source": crypto_result["data_source"],
            "crypto_data": crypto_data,
            "sentiment": sentiment_result,
            "technical_signals": technical_signals,
            "analysis": self._generate_crypto_analysis(crypto_data, sentiment_result, technical_signals),
            "updated_at": datetime.now().isoformat()
        }
    
    def _calculate_crypto_signals(self, crypto_data: Dict[str, Any]) -> Dict[str, Any]:
        """암호화폐 기술적 신호 계산"""
        current_price = crypto_data.get("current_price", 0)
        high_24h = crypto_data.get("high_24h", current_price)
        low_24h = crypto_data.get("low_24h", current_price)
        change_24h = crypto_data.get("price_change_percentage_24h", 0)
        change_7d = crypto_data.get("price_change_percentage_7d", 0)
        
        # RSI 모사 (변동률 기반)
        rsi = 50 + (change_24h * 2)  # 간단한 RSI 추정
        rsi = max(0, min(100, rsi))
        
        # 볼린저 밴드 모사
        price_range = high_24h - low_24h
        bollinger_upper = current_price + (price_range * 0.5)
        bollinger_lower = current_price - (price_range * 0.5)
        
        # 매매 신호 생성
        if change_24h > 5 and change_7d > 10:
            signal = "강한매수"
        elif change_24h > 2 and change_7d > 5:
            signal = "매수"
        elif change_24h < -5 and change_7d < -10:
            signal = "강한매도" 
        elif change_24h < -2 and change_7d < -5:
            signal = "매도"
        else:
            signal = "관망"
        
        return {
            "rsi": rsi,
            "bollinger_upper": bollinger_upper,
            "bollinger_lower": bollinger_lower,
            "signal": signal,
            "trend": "상승" if change_7d > 0 else "하락" if change_7d < -2 else "횡보",
            "momentum": "과매수" if rsi > 70 else "과매도" if rsi < 30 else "중립"
        }
    
    def _generate_crypto_analysis(self, crypto_data: Dict[str, Any], sentiment: Dict[str, Any], technical: Dict[str, Any]) -> str:
        """암호화폐 종합 분석 텍스트 생성"""
        name = crypto_data.get("name", "")
        current_price = crypto_data.get("current_price", 0)
        change_24h = crypto_data.get("price_change_percentage_24h", 0)
        change_7d = crypto_data.get("price_change_percentage_7d", 0)
        market_cap_rank = crypto_data.get("market_cap_rank", 0)
        
        analysis_parts = []
        
        # 기본 정보
        analysis_parts.append(f"{name}은(는) 현재 시가총액 {market_cap_rank}위의 암호화폐입니다.")
        
        # 가격 동향
        if change_24h > 0:
            analysis_parts.append(f"24시간 동안 {change_24h:.2f}% 상승했습니다.")
        else:
            analysis_parts.append(f"24시간 동안 {abs(change_24h):.2f}% 하락했습니다.")
            
        # 기술적 분석
        analysis_parts.append(f"기술적 지표: RSI {technical.get('rsi', 50):.1f}, 추세 {technical.get('trend', '횡보')}")
        
        # 매매 신호
        signal = technical.get('signal', '관망')
        analysis_parts.append(f"현재 매매신호는 '{signal}'입니다.")
        
        # 감성 분석
        sentiment_label = sentiment.get('sentiment_label', '중립적')
        analysis_parts.append(f"시장 감성은 {sentiment_label}입니다.")
        
        return " ".join(analysis_parts)


# 사용 예시
async def main():
    """테스트 함수"""
    async with CryptoAgent() as agent:
        result = await agent.analyze_crypto("비트코인")
        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())