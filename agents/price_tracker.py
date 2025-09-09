"""
52주 최고/최저 추적 및 기술적 지표 계산
주가 트렌드 분석 기능
"""

import asyncio
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import pandas as pd
from agents.price_agent import PriceAgent


class PriceTracker:
    """주가 추적 및 분석 클래스"""
    
    def __init__(self):
        self.price_agent = None
        
    async def __aenter__(self):
        self.price_agent = PriceAgent()
        await self.price_agent.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.price_agent:
            await self.price_agent.__aexit__(exc_type, exc_val, exc_tb)
            
    async def analyze_52week_position(self, stock_name: str) -> Dict[str, any]:
        """
        52주 최고/최저 대비 현재 위치 분석
        
        Returns:
            - position_percent: 52주 범위 내 현재가 위치 (0-100%)
            - distance_from_high: 52주 최고 대비 하락률
            - distance_from_low: 52주 최저 대비 상승률
            - trend: 추세 판단
        """
        # 현재가 정보
        price_data = await self.price_agent.get_stock_price(stock_name)
        if price_data["status"] != "success":
            return {"status": "error", "message": "Failed to get price data"}
            
        price_info = price_data["price_data"]
        current = price_info["current_price"]
        high_52w = price_info["week_52_high"]
        low_52w = price_info["week_52_low"]
        
        # 52주 범위 내 위치 계산 (%)
        if high_52w != low_52w:
            position_percent = ((current - low_52w) / (high_52w - low_52w)) * 100
        else:
            position_percent = 50.0
            
        # 최고/최저 대비 거리
        distance_from_high = ((current - high_52w) / high_52w) * 100 if high_52w > 0 else 0
        distance_from_low = ((current - low_52w) / low_52w) * 100 if low_52w > 0 else 0
        
        # 추세 판단
        if position_percent >= 80:
            trend = "52주 신고가 근접 🚀"
            trend_score = 5
        elif position_percent >= 60:
            trend = "상승 추세 📈"
            trend_score = 4
        elif position_percent >= 40:
            trend = "중립 구간 ➖"
            trend_score = 3
        elif position_percent >= 20:
            trend = "하락 추세 📉"
            trend_score = 2
        else:
            trend = "52주 신저가 근접 ⚠️"
            trend_score = 1
            
        return {
            "status": "success",
            "stock_name": stock_name,
            "current_price": current,
            "week_52_high": high_52w,
            "week_52_low": low_52w,
            "position_percent": round(position_percent, 2),
            "distance_from_high": round(distance_from_high, 2),
            "distance_from_low": round(distance_from_low, 2),
            "trend": trend,
            "trend_score": trend_score,
            "analysis": {
                "bullish_signals": [],
                "bearish_signals": [],
                "recommendation": ""
            }
        }
        
    async def calculate_moving_averages(self, 
                                      stock_name: str,
                                      periods: List[int] = [5, 20, 60, 120]) -> Dict[str, any]:
        """
        이동평균선 계산
        
        Args:
            stock_name: 종목명
            periods: 이동평균 기간 리스트 (기본: 5일, 20일, 60일, 120일)
        """
        try:
            # 최대 기간보다 많은 데이터 조회
            max_period = max(periods)
            history = await self.price_agent.get_price_history(
                stock_name, 
                period=f"{max_period + 30}d",
                interval="1d"
            )
            
            if history["status"] != "success":
                return {"status": "error", "message": "Failed to get history"}
                
            # DataFrame 변환
            df = pd.DataFrame(history["history"])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # 이동평균 계산
            ma_data = {}
            current_price = df['close'].iloc[-1]
            
            for period in periods:
                ma_value = df['close'].rolling(window=period).mean().iloc[-1]
                ma_data[f"MA{period}"] = {
                    "value": round(ma_value, 2),
                    "position": "above" if current_price > ma_value else "below",
                    "distance_percent": round(((current_price - ma_value) / ma_value) * 100, 2)
                }
                
            # 골든크로스/데드크로스 체크
            if "MA20" in ma_data and "MA60" in ma_data:
                if ma_data["MA20"]["value"] > ma_data["MA60"]["value"]:
                    cross_signal = "골든크로스 ✨"
                else:
                    cross_signal = "데드크로스 ⚠️"
            else:
                cross_signal = "신호 없음"
                
            return {
                "status": "success",
                "stock_name": stock_name,
                "current_price": round(current_price, 2),
                "moving_averages": ma_data,
                "cross_signal": cross_signal,
                "trend_strength": self._calculate_trend_strength(ma_data, current_price)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    def _calculate_trend_strength(self, ma_data: Dict, current_price: float) -> str:
        """추세 강도 계산"""
        above_count = sum(1 for ma in ma_data.values() if ma["position"] == "above")
        total_ma = len(ma_data)
        
        if above_count == total_ma:
            return "매우 강한 상승 추세 💪"
        elif above_count >= total_ma * 0.75:
            return "강한 상승 추세 📈"
        elif above_count >= total_ma * 0.5:
            return "약한 상승 추세 📊"
        elif above_count >= total_ma * 0.25:
            return "약한 하락 추세 📉"
        else:
            return "강한 하락 추세 ⚠️"
            
    async def find_support_resistance(self, 
                                    stock_name: str,
                                    period: str = "3mo") -> Dict[str, any]:
        """
        지지선/저항선 찾기
        
        최근 고점/저점을 기반으로 주요 가격대 식별
        """
        try:
            history = await self.price_agent.get_price_history(stock_name, period=period)
            
            if history["status"] != "success":
                return {"status": "error", "message": "Failed to get history"}
                
            df = pd.DataFrame(history["history"])
            
            # 최근 고점들 (저항선)
            highs = df.nlargest(5, 'high')['high'].tolist()
            
            # 최근 저점들 (지지선)  
            lows = df.nsmallest(5, 'low')['low'].tolist()
            
            current_price = df['close'].iloc[-1]
            
            # 가장 가까운 지지/저항 찾기
            nearest_support = max([p for p in lows if p < current_price], default=None)
            nearest_resistance = min([p for p in highs if p > current_price], default=None)
            
            return {
                "status": "success",
                "stock_name": stock_name,
                "current_price": round(current_price, 2),
                "support_levels": [round(p, 2) for p in sorted(lows)],
                "resistance_levels": [round(p, 2) for p in sorted(highs, reverse=True)],
                "nearest_support": round(nearest_support, 2) if nearest_support else None,
                "nearest_resistance": round(nearest_resistance, 2) if nearest_resistance else None,
                "support_distance": round(((current_price - nearest_support) / current_price) * 100, 2) if nearest_support else None,
                "resistance_distance": round(((nearest_resistance - current_price) / current_price) * 100, 2) if nearest_resistance else None
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}