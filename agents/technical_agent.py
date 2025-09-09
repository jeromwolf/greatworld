"""
Technical Agent - 기술적 분석 지표 계산 에이전트
주가 데이터를 기반으로 다양한 기술적 지표 계산
"""

import os
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
import yfinance as yf
import pandas as pd
import numpy as np
from agents.price_agent import PriceAgent


@dataclass
class TechnicalIndicators:
    """기술적 지표 데이터 모델"""
    # 이동평균선
    ma5: float      # 5일 이동평균
    ma20: float     # 20일 이동평균
    ma60: float     # 60일 이동평균
    ma120: float    # 120일 이동평균
    
    # 모멘텀 지표
    rsi: float      # RSI (14일)
    macd: float     # MACD
    macd_signal: float  # MACD Signal
    macd_histogram: float  # MACD Histogram
    
    # 변동성 지표
    bollinger_upper: float  # 볼린저밴드 상단
    bollinger_middle: float  # 볼린저밴드 중간
    bollinger_lower: float   # 볼린저밴드 하단
    atr: float              # Average True Range
    
    # 거래량 지표
    obv: float      # On Balance Volume
    volume_ratio: float  # 거래량 비율 (현재/평균)
    
    # 추세 지표
    adx: float      # Average Directional Index
    cci: float      # Commodity Channel Index
    
    # 지지/저항
    pivot: float    # 피벗 포인트
    resistance1: float  # 1차 저항선
    resistance2: float  # 2차 저항선
    support1: float     # 1차 지지선
    support2: float     # 2차 지지선


@dataclass
class TechnicalAnalysis:
    """기술적 분석 결과"""
    indicators: TechnicalIndicators
    trend: str  # "상승", "하락", "횡보"
    momentum: str  # "과매수", "과매도", "중립"
    signal: str  # "매수", "매도", "관망"
    strength: float  # 신호 강도 (0-1)
    key_levels: Dict[str, float]  # 주요 가격대
    patterns: List[str]  # 차트 패턴
    analysis_text: str  # 분석 설명


class TechnicalAgent:
    """기술적 분석 에이전트"""
    
    def __init__(self):
        self.price_agent = None
        
    async def __aenter__(self):
        self.price_agent = PriceAgent()
        await self.price_agent.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.price_agent:
            await self.price_agent.__aexit__(exc_type, exc_val, exc_tb)
            
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not rsi.empty else 50.0
        
    def _calculate_macd(self, prices: pd.Series) -> Tuple[float, float, float]:
        """MACD 계산"""
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        
        return (
            float(macd.iloc[-1]) if not macd.empty else 0.0,
            float(signal.iloc[-1]) if not signal.empty else 0.0,
            float(histogram.iloc[-1]) if not histogram.empty else 0.0
        )
        
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[float, float, float]:
        """볼린저밴드 계산"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return (
            float(upper.iloc[-1]) if not upper.empty else 0.0,
            float(middle.iloc[-1]) if not middle.empty else 0.0,
            float(lower.iloc[-1]) if not lower.empty else 0.0
        )
        
    def _calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        """ATR (Average True Range) 계산"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return float(atr.iloc[-1]) if not atr.empty else 0.0
        
    def _calculate_obv(self, close: pd.Series, volume: pd.Series) -> float:
        """OBV (On Balance Volume) 계산"""
        obv = (volume * ((close > close.shift()).astype(int) * 2 - 1)).cumsum()
        return float(obv.iloc[-1]) if not obv.empty else 0.0
        
    def _calculate_pivot_points(self, high: float, low: float, close: float) -> Dict[str, float]:
        """피벗 포인트 계산"""
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        
        return {
            "pivot": pivot,
            "resistance1": r1,
            "resistance2": r2,
            "support1": s1,
            "support2": s2
        }
        
    def _analyze_trend(self, prices: pd.Series, ma20: float, ma60: float) -> str:
        """추세 분석"""
        current = float(prices.iloc[-1])
        
        if current > ma20 > ma60:
            return "상승"
        elif current < ma20 < ma60:
            return "하락"
        else:
            return "횡보"
            
    def _analyze_momentum(self, rsi: float) -> str:
        """모멘텀 분석"""
        if rsi > 70:
            return "과매수"
        elif rsi < 30:
            return "과매도"
        else:
            return "중립"
            
    def _generate_signal(self, indicators: TechnicalIndicators, trend: str, momentum: str) -> Tuple[str, float]:
        """매매 신호 생성"""
        score = 0.5  # 기본 점수
        
        # RSI 기반
        if indicators.rsi < 30:
            score += 0.2
        elif indicators.rsi > 70:
            score -= 0.2
            
        # MACD 기반
        if indicators.macd > indicators.macd_signal:
            score += 0.15
        else:
            score -= 0.15
            
        # 이동평균선 기반
        if indicators.ma5 > indicators.ma20:
            score += 0.15
        else:
            score -= 0.15
            
        # 신호 결정
        if score > 0.65:
            return "매수", min(score, 1.0)
        elif score < 0.35:
            return "매도", 1.0 - score
        else:
            return "관망", 0.5
            
    async def analyze_technical(self, stock_name: str, period: str = "3mo") -> Dict[str, Any]:
        """
        기술적 분석 수행
        
        Args:
            stock_name: 종목명 또는 티커
            period: 분석 기간
        """
        try:
            # 주가 데이터 조회
            history_result = await self.price_agent.get_price_history(stock_name, period=period)
            
            if history_result["status"] != "success":
                return history_result
                
            # DataFrame 생성
            history_data = history_result["history"]
            df = pd.DataFrame(history_data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # 최신 데이터 확인
            if len(df) < 60:  # 최소 60일 데이터 필요
                return {
                    "status": "error",
                    "message": "기술적 분석을 위한 충분한 데이터가 없습니다.",
                    "data_source": "INSUFFICIENT_DATA"
                }
                
            # 기술적 지표 계산
            close_prices = df['close']
            
            # 이동평균선
            ma5 = float(close_prices.rolling(window=5).mean().iloc[-1])
            ma20 = float(close_prices.rolling(window=20).mean().iloc[-1])
            ma60 = float(close_prices.rolling(window=60).mean().iloc[-1])
            ma120 = float(close_prices.rolling(window=120).mean().iloc[-1]) if len(df) >= 120 else ma60
            
            # RSI
            rsi = self._calculate_rsi(close_prices)
            
            # MACD
            macd, macd_signal, macd_histogram = self._calculate_macd(close_prices)
            
            # 볼린저밴드
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(close_prices)
            
            # ATR
            atr = self._calculate_atr(df['high'], df['low'], df['close'])
            
            # OBV
            obv = self._calculate_obv(df['close'], df['volume'])
            
            # 거래량 비율
            avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
            volume_ratio = df['volume'].iloc[-1] / avg_volume if avg_volume > 0 else 1.0
            
            # 피벗 포인트
            pivot_levels = self._calculate_pivot_points(
                df['high'].iloc[-1],
                df['low'].iloc[-1],
                df['close'].iloc[-1]
            )
            
            # 지표 객체 생성
            indicators = TechnicalIndicators(
                ma5=ma5,
                ma20=ma20,
                ma60=ma60,
                ma120=ma120,
                rsi=rsi,
                macd=macd,
                macd_signal=macd_signal,
                macd_histogram=macd_histogram,
                bollinger_upper=bb_upper,
                bollinger_middle=bb_middle,
                bollinger_lower=bb_lower,
                atr=atr,
                obv=obv,
                volume_ratio=volume_ratio,
                adx=0.0,  # TODO: ADX 구현
                cci=0.0,  # TODO: CCI 구현
                pivot=pivot_levels["pivot"],
                resistance1=pivot_levels["resistance1"],
                resistance2=pivot_levels["resistance2"],
                support1=pivot_levels["support1"],
                support2=pivot_levels["support2"]
            )
            
            # 분석
            trend = self._analyze_trend(close_prices, ma20, ma60)
            momentum = self._analyze_momentum(rsi)
            signal, strength = self._generate_signal(indicators, trend, momentum)
            
            # 분석 텍스트 생성
            analysis_text = self._generate_analysis_text(
                stock_name, indicators, trend, momentum, signal, strength
            )
            
            # 결과 생성
            analysis = TechnicalAnalysis(
                indicators=indicators,
                trend=trend,
                momentum=momentum,
                signal=signal,
                strength=strength,
                key_levels={
                    "resistance2": pivot_levels["resistance2"],
                    "resistance1": pivot_levels["resistance1"],
                    "pivot": pivot_levels["pivot"],
                    "support1": pivot_levels["support1"],
                    "support2": pivot_levels["support2"]
                },
                patterns=[],  # TODO: 패턴 인식 구현
                analysis_text=analysis_text
            )
            
            return {
                "status": "success",
                "data_source": "REAL_DATA",
                "stock_name": stock_name,
                "period": period,
                "analysis": {
                    "indicators": asdict(indicators),
                    "trend": trend,
                    "momentum": momentum,
                    "signal": signal,
                    "strength": strength,
                    "key_levels": analysis.key_levels,
                    "patterns": analysis.patterns,
                    "analysis_text": analysis_text
                },
                "current_price": float(close_prices.iloc[-1]),
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[TECHNICAL ERROR] {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "data_source": "ERROR"
            }
            
    def _generate_analysis_text(self, stock_name: str, indicators: TechnicalIndicators,
                               trend: str, momentum: str, signal: str, strength: float) -> str:
        """분석 설명 텍스트 생성"""
        text = f"### {stock_name} 기술적 분석\n\n"
        
        # 추세 분석
        text += f"**추세**: {trend}\n"
        if indicators.ma5 > indicators.ma20 > indicators.ma60:
            text += "• 단기, 중기, 장기 이동평균선이 정배열 상태입니다.\n"
        elif indicators.ma5 < indicators.ma20 < indicators.ma60:
            text += "• 단기, 중기, 장기 이동평균선이 역배열 상태입니다.\n"
            
        # 모멘텀 분석
        text += f"\n**모멘텀**: {momentum} (RSI: {indicators.rsi:.1f})\n"
        if indicators.rsi > 70:
            text += "• RSI가 70 이상으로 과매수 구간입니다.\n"
        elif indicators.rsi < 30:
            text += "• RSI가 30 이하로 과매도 구간입니다.\n"
            
        # MACD 분석
        text += f"\n**MACD**: {indicators.macd:.2f}\n"
        if indicators.macd > indicators.macd_signal:
            text += "• MACD가 시그널선 위에 있어 상승 모멘텀이 있습니다.\n"
        else:
            text += "• MACD가 시그널선 아래에 있어 하락 모멘텀이 있습니다.\n"
            
        # 거래량 분석
        text += f"\n**거래량**: 평균 대비 {indicators.volume_ratio:.1f}배\n"
        if indicators.volume_ratio > 1.5:
            text += "• 거래량이 평균보다 크게 증가했습니다.\n"
        elif indicators.volume_ratio < 0.5:
            text += "• 거래량이 평균보다 크게 감소했습니다.\n"
            
        # 매매 신호
        text += f"\n**매매 신호**: {signal} (신뢰도: {strength:.0%})\n"
        
        # 주요 가격대
        text += f"\n**주요 가격대**\n"
        text += f"• 2차 저항: {indicators.resistance2:,.0f}원\n"
        text += f"• 1차 저항: {indicators.resistance1:,.0f}원\n"
        text += f"• 피벗: {indicators.pivot:,.0f}원\n"
        text += f"• 1차 지지: {indicators.support1:,.0f}원\n"
        text += f"• 2차 지지: {indicators.support2:,.0f}원\n"
        
        return text


# 테스트 함수
async def test_technical_agent():
    async with TechnicalAgent() as agent:
        # 삼성전자 기술적 분석
        result = await agent.analyze_technical("삼성전자")
        
        if result["status"] == "success":
            print("\n=== 삼성전자 기술적 분석 ===")
            print(result["analysis"]["analysis_text"])
        else:
            print(f"Error: {result['message']}")


if __name__ == "__main__":
    asyncio.run(test_technical_agent())