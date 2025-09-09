"""
StockAI 데이터 수집 기간 설정
데이터별 특성을 고려한 최적 기간 정의
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class PeriodConfig:
    """데이터 소스별 최적 수집 기간 설정"""
    
    # 뉴스 데이터 (빠른 전파, 단기 영향)
    NEWS_PERIOD_DAYS = 14  # 2주 - 뉴스 영향이 주가에 반영되는 적정 시간
    
    # 공시 데이터 (공식적, 중장기 영향) 
    DISCLOSURE_PERIOD_DAYS = 45  # 1.5개월 - 공시 영향의 적절한 기간
    
    # 소셜 데이터 (실시간성, 높은 변동성)
    SOCIAL_PERIOD_DAYS = 7  # 1주 - 소셜 트렌드 빠른 변화 주기
    
    # 재무 데이터 (분기별, 장기 영향)
    FINANCIAL_PERIOD_DAYS = 90  # 3개월 - 분기 재무제표 기준
    
    @classmethod
    def get_all_periods(cls) -> Dict[str, int]:
        """모든 기간 설정을 딕셔너리로 반환"""
        return {
            'news': cls.NEWS_PERIOD_DAYS,
            'disclosure': cls.DISCLOSURE_PERIOD_DAYS,
            'social': cls.SOCIAL_PERIOD_DAYS,
            'financial': cls.FINANCIAL_PERIOD_DAYS
        }
    
    @classmethod
    def get_period_rationale(cls) -> Dict[str, str]:
        """각 기간 설정의 근거 설명"""
        return {
            'news': f"{cls.NEWS_PERIOD_DAYS}일 - 뉴스 영향이 주가에 완전히 반영되는 시간",
            'disclosure': f"{cls.DISCLOSURE_PERIOD_DAYS}일 - 공시 내용의 시장 해석 및 반응 기간",
            'social': f"{cls.SOCIAL_PERIOD_DAYS}일 - 소셜 미디어 트렌드의 유효 생명주기",
            'financial': f"{cls.FINANCIAL_PERIOD_DAYS}일 - 분기별 재무제표 발표 주기"
        }


# 시간 가중치 설정
@dataclass 
class TimeWeightConfig:
    """시간 경과에 따른 가중치 감쇠 설정"""
    
    # 데이터별 감쇠율 (높을수록 빠르게 감쇠)
    NEWS_DECAY_RATE = 0.15      # 뉴스는 빠르게 영향력 감소
    DISCLOSURE_DECAY_RATE = 0.05 # 공시는 천천히 감쇠  
    SOCIAL_DECAY_RATE = 0.25    # 소셜은 매우 빠르게 감쇠
    FINANCIAL_DECAY_RATE = 0.02  # 재무는 가장 천천히 감쇠
    
    @classmethod
    def get_decay_rates(cls) -> Dict[str, float]:
        """데이터별 감쇠율 반환"""
        return {
            'news': cls.NEWS_DECAY_RATE,
            'disclosure': cls.DISCLOSURE_DECAY_RATE, 
            'social': cls.SOCIAL_DECAY_RATE,
            'financial': cls.FINANCIAL_DECAY_RATE
        }


# 투자 스타일별 조정 (추후 확장용)
@dataclass
class InvestmentStylePeriods:
    """투자 스타일별 기간 조정"""
    
    # 단기 투자자 (1주-1개월)
    SHORT_TERM = {
        'news': 7,
        'disclosure': 21, 
        'social': 5,
        'financial': 60
    }
    
    # 중기 투자자 (1-6개월) - 기본값
    MEDIUM_TERM = {
        'news': 14,
        'disclosure': 45,
        'social': 7, 
        'financial': 90
    }
    
    # 장기 투자자 (6개월+)
    LONG_TERM = {
        'news': 21,
        'disclosure': 60,
        'social': 10,
        'financial': 180
    }