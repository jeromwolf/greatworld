"""
Financial Agent - 재무 데이터 분석 에이전트
DART 재무제표 파싱 및 재무 지표 계산
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
import pandas as pd
from bs4 import BeautifulSoup


@dataclass
class FinancialStatement:
    """재무제표 데이터 모델"""
    # 기본 정보
    corp_code: str          # 기업 고유번호
    corp_name: str          # 기업명
    stock_code: str         # 종목코드
    report_code: str        # 보고서 코드 (11011: 사업보고서, 11012: 반기보고서, 11013: 1분기보고서, 11014: 3분기보고서)
    report_year: str        # 보고 년도
    
    # 재무상태표 (단위: 백만원)
    total_assets: float              # 총자산
    total_liabilities: float         # 총부채
    total_equity: float              # 자본총계
    current_assets: float            # 유동자산
    current_liabilities: float       # 유동부채
    non_current_assets: float        # 비유동자산
    non_current_liabilities: float   # 비유동부채
    
    # 손익계산서 (단위: 백만원)
    revenue: float                   # 매출액
    operating_income: float          # 영업이익
    net_income: float               # 당기순이익
    gross_profit: float             # 매출총이익
    ebit: float                     # 세전이익
    
    # 현금흐름표 (단위: 백만원)
    operating_cash_flow: float       # 영업활동현금흐름
    investing_cash_flow: float       # 투자활동현금흐름
    financing_cash_flow: float       # 재무활동현금흐름
    
    # 주당 지표
    eps: float                      # 주당순이익
    bps: float                      # 주당순자산


@dataclass
class FinancialRatios:
    """재무 비율 데이터 모델"""
    # 수익성 지표
    roe: float              # 자기자본수익률
    roa: float              # 총자산수익률
    npm: float              # 순이익률
    opm: float              # 영업이익률
    gross_margin: float     # 매출총이익률
    
    # 안정성 지표
    debt_ratio: float       # 부채비율
    current_ratio: float    # 유동비율
    quick_ratio: float      # 당좌비율
    equity_ratio: float     # 자기자본비율
    
    # 성장성 지표
    revenue_growth: float   # 매출성장률
    profit_growth: float    # 이익성장률
    asset_growth: float     # 자산성장률
    
    # 활동성 지표
    asset_turnover: float   # 총자산회전율
    inventory_turnover: float # 재고자산회전율


class FinancialAgent:
    """재무 데이터 분석 에이전트"""
    
    def __init__(self, dart_api_key: Optional[str] = None):
        self.dart_api_key = dart_api_key or os.getenv("DART_API_KEY")
        self.dart_base_url = "https://opendart.fss.or.kr/api"
        self.session = None
        
        # 보고서 코드 매핑
        self.report_codes = {
            "annual": "11011",      # 사업보고서
            "half": "11012",        # 반기보고서
            "quarter1": "11013",    # 1분기보고서
            "quarter3": "11014"     # 3분기보고서
        }
        
        # 계정과목 코드 매핑 (DART API 표준)
        self.account_codes = {
            # 재무상태표
            "total_assets": "ifrs_TotalAssets",
            "total_liabilities": "ifrs_TotalLiabilities", 
            "total_equity": "ifrs_TotalEquity",
            "current_assets": "ifrs_CurrentAssets",
            "current_liabilities": "ifrs_CurrentLiabilities",
            
            # 손익계산서
            "revenue": "ifrs-full_Revenue",
            "operating_income": "dart_OperatingIncomeLoss",
            "net_income": "ifrs-full_ProfitLoss"
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    def _get_latest_report_info(self, report_type: str = "annual") -> Dict[str, str]:
        """최신 보고서 정보 계산"""
        now = datetime.now()
        
        if report_type == "annual":
            # 사업보고서는 3월말 제출
            if now.month <= 3:
                year = str(now.year - 2)
            else:
                year = str(now.year - 1)
            report_code = "11011"
        elif report_type == "half":
            # 반기보고서는 8월 제출
            if now.month <= 8:
                year = str(now.year - 1)
            else:
                year = str(now.year)
            report_code = "11012"
        elif report_type == "quarter1":
            # 1분기보고서는 5월 제출
            if now.month <= 5:
                year = str(now.year - 1)
            else:
                year = str(now.year)
            report_code = "11013"
        elif report_type == "quarter3":
            # 3분기보고서는 11월 제출
            if now.month <= 11:
                year = str(now.year - 1)
            else:
                year = str(now.year)
            report_code = "11014"
            
        return {"year": year, "report_code": report_code}
        
    async def get_financial_statements(self, 
                                     corp_code: str,
                                     report_type: str = "annual",
                                     year: Optional[str] = None) -> Dict[str, Any]:
        """
        재무제표 조회
        
        Args:
            corp_code: 기업 고유번호
            report_type: 보고서 유형 (annual, half, quarter1, quarter3)
            year: 보고 년도 (없으면 최신)
        """
        if not self.dart_api_key:
            return {"status": "error", "message": "DART API key not configured"}
            
        # 최신 보고서 정보 가져오기
        if not year:
            report_info = self._get_latest_report_info(report_type)
            year = report_info["year"]
            report_code = report_info["report_code"]
        else:
            report_code = self.report_codes.get(report_type, "11011")
            
        try:
            # 단일회사 재무제표 API 호출
            url = f"{self.dart_base_url}/fnlttSinglAcnt.json"
            params = {
                "crtfc_key": self.dart_api_key,
                "corp_code": corp_code,
                "bsns_year": year,
                "reprt_code": report_code,
                "fs_div": "CFS"  # CFS: 연결재무제표, OFS: 개별재무제표
            }
            
            print(f"[FINANCIAL] Fetching statements for corp_code: {corp_code}, year: {year}, report: {report_type}")
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("status") == "000":
                        # 재무데이터 파싱
                        statements = self._parse_financial_data(data.get("list", []))
                        
                        return {
                            "status": "success",
                            "data_source": "REAL_DATA",
                            "corp_code": corp_code,
                            "year": year,
                            "report_type": report_type,
                            "statements": statements
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"DART API error: {data.get('message', 'Unknown error')}"
                        }
                else:
                    return {
                        "status": "error",
                        "message": f"HTTP error: {response.status}"
                    }
                    
        except Exception as e:
            print(f"[FINANCIAL ERROR] {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "data_source": "ERROR"
            }
            
    def _parse_financial_data(self, data_list: List[Dict]) -> Dict[str, Any]:
        """DART API 데이터를 재무제표 형식으로 파싱"""
        parsed = {
            "balance_sheet": {},  # 재무상태표
            "income_statement": {},  # 손익계산서
            "cash_flow": {}  # 현금흐름표
        }
        
        for item in data_list:
            account_nm = item.get("account_nm", "")
            thstrm_amount = item.get("thstrm_amount", "0")
            
            # 금액 변환 (문자열 -> 숫자, 단위: 원 -> 백만원)
            try:
                amount = float(thstrm_amount.replace(",", "")) / 1_000_000
            except:
                amount = 0
                
            # 재무상태표 항목
            if "자산총계" in account_nm:
                parsed["balance_sheet"]["total_assets"] = amount
            elif "부채총계" in account_nm:
                parsed["balance_sheet"]["total_liabilities"] = amount
            elif "자본총계" in account_nm:
                parsed["balance_sheet"]["total_equity"] = amount
            elif "유동자산" in account_nm and "비유동" not in account_nm:
                parsed["balance_sheet"]["current_assets"] = amount
            elif "유동부채" in account_nm and "비유동" not in account_nm:
                parsed["balance_sheet"]["current_liabilities"] = amount
                
            # 손익계산서 항목
            elif "매출액" in account_nm or "수익" in account_nm:
                parsed["income_statement"]["revenue"] = amount
            elif "영업이익" in account_nm:
                parsed["income_statement"]["operating_income"] = amount
            elif "당기순이익" in account_nm:
                parsed["income_statement"]["net_income"] = amount
            elif "매출총이익" in account_nm:
                parsed["income_statement"]["gross_profit"] = amount
                
            # 현금흐름표 항목
            elif "영업활동" in account_nm and "현금흐름" in account_nm:
                parsed["cash_flow"]["operating_cash_flow"] = amount
            elif "투자활동" in account_nm and "현금흐름" in account_nm:
                parsed["cash_flow"]["investing_cash_flow"] = amount
            elif "재무활동" in account_nm and "현금흐름" in account_nm:
                parsed["cash_flow"]["financing_cash_flow"] = amount
                
        return parsed
        
    def calculate_financial_ratios(self, statements: Dict[str, Any]) -> FinancialRatios:
        """재무 비율 계산"""
        bs = statements.get("balance_sheet", {})
        is_ = statements.get("income_statement", {})
        
        # 기본값 설정
        total_assets = bs.get("total_assets", 1)  # 0으로 나누기 방지
        total_equity = bs.get("total_equity", 1)
        total_liabilities = bs.get("total_liabilities", 0)
        current_assets = bs.get("current_assets", 0)
        current_liabilities = bs.get("current_liabilities", 1)
        
        revenue = is_.get("revenue", 1)
        operating_income = is_.get("operating_income", 0)
        net_income = is_.get("net_income", 0)
        
        # 수익성 지표
        roe = (net_income / total_equity) * 100 if total_equity > 0 else 0
        roa = (net_income / total_assets) * 100 if total_assets > 0 else 0
        npm = (net_income / revenue) * 100 if revenue > 0 else 0
        opm = (operating_income / revenue) * 100 if revenue > 0 else 0
        
        # 안정성 지표
        debt_ratio = (total_liabilities / total_equity) * 100 if total_equity > 0 else 0
        current_ratio = (current_assets / current_liabilities) * 100 if current_liabilities > 0 else 0
        equity_ratio = (total_equity / total_assets) * 100 if total_assets > 0 else 0
        
        # 활동성 지표
        asset_turnover = revenue / total_assets if total_assets > 0 else 0
        
        return FinancialRatios(
            roe=round(roe, 2),
            roa=round(roa, 2),
            npm=round(npm, 2),
            opm=round(opm, 2),
            gross_margin=0,  # 추후 계산
            
            debt_ratio=round(debt_ratio, 2),
            current_ratio=round(current_ratio, 2),
            quick_ratio=0,  # 추후 계산
            equity_ratio=round(equity_ratio, 2),
            
            revenue_growth=0,  # 전년 대비 필요
            profit_growth=0,   # 전년 대비 필요
            asset_growth=0,    # 전년 대비 필요
            
            asset_turnover=round(asset_turnover, 2),
            inventory_turnover=0  # 추후 계산
        )
        
    async def analyze_financial_health(self, corp_code: str) -> Dict[str, Any]:
        """기업 재무 건전성 종합 분석"""
        # 최근 재무제표 조회
        annual_result = await self.get_financial_statements(corp_code, "annual")
        
        if annual_result["status"] != "success":
            return annual_result
            
        statements = annual_result["statements"]
        ratios = self.calculate_financial_ratios(statements)
        
        # 재무 건전성 평가
        health_score = self._calculate_health_score(ratios)
        
        # 투자 포인트 도출
        investment_points = self._generate_investment_points(statements, ratios)
        
        return {
            "status": "success",
            "data_source": "REAL_DATA",
            "corp_code": corp_code,
            "statements": statements,
            "ratios": asdict(ratios),
            "health_score": health_score,
            "investment_points": investment_points
        }
        
    def _calculate_health_score(self, ratios: FinancialRatios) -> Dict[str, Any]:
        """재무 건전성 점수 계산"""
        score = 0
        max_score = 100
        
        # 수익성 평가 (40점)
        if ratios.roe > 15:
            score += 20
        elif ratios.roe > 10:
            score += 15
        elif ratios.roe > 5:
            score += 10
        elif ratios.roe > 0:
            score += 5
            
        if ratios.opm > 15:
            score += 20
        elif ratios.opm > 10:
            score += 15
        elif ratios.opm > 5:
            score += 10
        elif ratios.opm > 0:
            score += 5
            
        # 안정성 평가 (40점)
        if ratios.debt_ratio < 100:
            score += 20
        elif ratios.debt_ratio < 150:
            score += 15
        elif ratios.debt_ratio < 200:
            score += 10
        elif ratios.debt_ratio < 300:
            score += 5
            
        if ratios.current_ratio > 200:
            score += 20
        elif ratios.current_ratio > 150:
            score += 15
        elif ratios.current_ratio > 100:
            score += 10
        elif ratios.current_ratio > 50:
            score += 5
            
        # 효율성 평가 (20점)
        if ratios.asset_turnover > 1.0:
            score += 20
        elif ratios.asset_turnover > 0.8:
            score += 15
        elif ratios.asset_turnover > 0.5:
            score += 10
        elif ratios.asset_turnover > 0.3:
            score += 5
            
        # 등급 판정
        if score >= 80:
            grade = "A"
            grade_text = "매우 우수"
        elif score >= 60:
            grade = "B"
            grade_text = "우수"
        elif score >= 40:
            grade = "C"
            grade_text = "보통"
        elif score >= 20:
            grade = "D"
            grade_text = "주의"
        else:
            grade = "E"
            grade_text = "위험"
            
        return {
            "score": score,
            "max_score": max_score,
            "grade": grade,
            "grade_text": grade_text,
            "evaluation": self._get_health_evaluation(score, ratios)
        }
        
    def _get_health_evaluation(self, score: int, ratios: FinancialRatios) -> str:
        """재무 건전성 평가 메시지"""
        if score >= 80:
            return "재무구조가 매우 건전하며 수익성도 우수합니다. 장기투자에 적합한 기업입니다."
        elif score >= 60:
            return "안정적인 재무구조와 양호한 수익성을 보이고 있습니다."
        elif score >= 40:
            return "재무구조는 평균적이나 일부 개선이 필요한 부분이 있습니다."
        elif score >= 20:
            return "재무건전성에 주의가 필요하며, 투자시 신중한 판단이 요구됩니다."
        else:
            return "재무구조가 취약하여 높은 리스크가 존재합니다."
            
    def _generate_investment_points(self, 
                                  statements: Dict[str, Any],
                                  ratios: FinancialRatios) -> List[str]:
        """투자 포인트 생성"""
        points = []
        
        # 수익성 포인트
        if ratios.roe > 15:
            points.append(f"✅ 높은 ROE ({ratios.roe}%): 우수한 자본 효율성")
        if ratios.opm > 15:
            points.append(f"✅ 높은 영업이익률 ({ratios.opm}%): 강한 본업 경쟁력")
            
        # 안정성 포인트
        if ratios.debt_ratio < 100:
            points.append(f"✅ 낮은 부채비율 ({ratios.debt_ratio}%): 안정적인 재무구조")
        if ratios.current_ratio > 200:
            points.append(f"✅ 높은 유동비율 ({ratios.current_ratio}%): 단기 지급능력 우수")
            
        # 주의 포인트
        if ratios.roe < 5:
            points.append(f"⚠️ 낮은 ROE ({ratios.roe}%): 수익성 개선 필요")
        if ratios.debt_ratio > 200:
            points.append(f"⚠️ 높은 부채비율 ({ratios.debt_ratio}%): 재무 리스크 존재")
            
        return points


# 테스트 함수
async def test_financial_agent():
    async with FinancialAgent() as agent:
        # 삼성전자 재무제표 조회
        result = await agent.analyze_financial_health("00126380")  # 삼성전자 corp_code
        
        if result["status"] == "success":
            print("\n=== 삼성전자 재무 분석 ===")
            print(f"재무 건전성 점수: {result['health_score']['score']}/{result['health_score']['max_score']}")
            print(f"등급: {result['health_score']['grade']} ({result['health_score']['grade_text']})")
            print("\n투자 포인트:")
            for point in result['investment_points']:
                print(f"  {point}")
        else:
            print(f"Error: {result['message']}")


if __name__ == "__main__":
    asyncio.run(test_financial_agent())