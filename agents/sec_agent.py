"""
SEC Agent - 미국 공시 데이터 수집 에이전트
SEC EDGAR API를 통한 미국 기업 공시 정보 수집
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
import re


@dataclass
class SECFiling:
    """SEC 공시 데이터 모델"""
    accession_number: str    # 접수번호
    filing_date: str        # 제출일
    form_type: str          # 공시 유형 (10-K, 10-Q, 8-K 등)
    company_name: str       # 회사명
    ticker: str             # 티커
    cik: str                # CIK (Central Index Key)
    filing_url: str         # 공시 URL
    description: str = ""   # 공시 설명


class SECAgent:
    """SEC 공시 데이터 수집 에이전트"""
    
    def __init__(self):
        self.base_url = "https://data.sec.gov"
        self.session = None
        self.headers = {
            "User-Agent": "StockAI/1.0 (contact@stockai.com)"  # SEC 요구사항
        }
        
        # 주요 공시 유형
        self.major_form_types = {
            "10-K": "연간 보고서",
            "10-Q": "분기 보고서",
            "8-K": "주요 사건 보고",
            "DEF 14A": "위임장 권유 신고서",
            "S-1": "증권 신고서",
            "424B": "추가 정보 공시",
            "SC 13G": "5% 이상 지분 보고",
            "4": "내부자 거래 보고"
        }
        
        # 주요 기업 CIK 매핑
        self.company_cik_mapping = {
            "AAPL": "0000320193",  # Apple
            "MSFT": "0000789019",  # Microsoft
            "GOOGL": "0001652044", # Alphabet
            "GOOG": "0001652044",  # Alphabet
            "AMZN": "0001018724",  # Amazon
            "TSLA": "0001318605",  # Tesla
            "META": "0001326801",  # Meta
            "NVDA": "0001045810",  # NVIDIA
            "JPM": "0000019617",   # JPMorgan
            "V": "0001403161"      # Visa
        }
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
            
    async def search_filings(self,
                                ticker: Optional[str] = None,
                                cik: Optional[str] = None,
                                form_type: Optional[str] = None,
                                start_date: Optional[str] = None,
                                end_date: Optional[str] = None,
                                limit: int = 20) -> Dict[str, Any]:
        """
        SEC 공시 검색
        
        Args:
            ticker: 종목 티커
            cik: Central Index Key
            form_type: 공시 유형 (10-K, 10-Q, 8-K 등)
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            limit: 최대 결과 수
        """
        try:
            # 티커로 CIK 찾기
            if ticker and not cik:
                cik = self.company_cik_mapping.get(ticker.upper())
                if not cik:
                    return {
                        "status": "error",
                        "message": f"Ticker '{ticker}'에 대한 CIK를 찾을 수 없습니다"
                    }
                    
            if not cik:
                return {
                    "status": "error",
                    "message": "CIK 또는 ticker가 필요합니다"
                }
                
            # CIK 포맷팅 (10자리로 패딩)
            cik = cik.zfill(10)
            
            # SEC API 호출
            url = f"{self.base_url}/submissions/CIK{cik}.json"
            
            async with self.session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 최근 공시 추출
                    recent_filings = data.get("filings", {}).get("recent", {})
                    
                    filings = []
                    for i in range(min(limit, len(recent_filings.get("accessionNumber", [])))):
                        filing_date = recent_filings["filingDate"][i]
                        
                        # 날짜 필터링
                        if start_date and filing_date < start_date:
                            continue
                        if end_date and filing_date > end_date:
                            continue
                            
                        # 폼 타입 필터링
                        current_form_type = recent_filings["form"][i]
                        if form_type and current_form_type != form_type:
                            continue
                            
                        # 공시 URL 생성
                        accession = recent_filings["accessionNumber"][i].replace("-", "")
                        filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{recent_filings['primaryDocument'][i]}"
                        
                        filing = SECFiling(
                            accession_number=recent_filings["accessionNumber"][i],
                            filing_date=filing_date,
                            form_type=current_form_type,
                            company_name=data.get("name", ""),
                            ticker=ticker or "",
                            cik=cik,
                            filing_url=filing_url,
                            description=self.major_form_types.get(current_form_type, "")
                        )
                        
                        filings.append(asdict(filing))
                        
                    return {
                        "status": "success",
                        "data_source": "REAL_DATA",
                        "company_name": data.get("name", ""),
                        "ticker": ticker or "",
                        "cik": cik,
                        "count": len(filings),
                        "filings": filings
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
            
    async def get_filing_content(self, filing_url: str) -> Dict[str, Any]:
        """
        공시 내용 가져오기
        
        Args:
            filing_url: 공시 문서 URL
        """
        try:
            async with self.session.get(filing_url, headers=self.headers) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # HTML 태그 제거하고 텍스트만 추출
                    text_content = self._extract_text_from_html(content)
                    
                    # 주요 섹션 추출
                    sections = self._extract_key_sections(text_content)
                    
                    return {
                        "status": "success",
                        "data_source": "REAL_DATA",
                        "url": filing_url,
                        "summary": text_content[:1000],  # 첫 1000자
                        "sections": sections
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
            
    def _extract_text_from_html(self, html_content: str) -> str:
        """HTML에서 텍스트 추출"""
        # 간단한 HTML 태그 제거 (실제로는 BeautifulSoup 사용 권장)
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
        
    def _extract_key_sections(self, text: str) -> Dict[str, str]:
        """주요 섹션 추출"""
        sections = {}
        
        # 8-K의 경우 Item 추출
        if "Item" in text:
            items = re.findall(r'Item\s+\d+\.\d+[^\n]*([^Item]*)', text, re.IGNORECASE)
            for i, item in enumerate(items[:5]):  # 최대 5개 아이템
                sections[f"Item {i+1}"] = item[:500].strip()
                
        # 10-K/10-Q의 경우 주요 섹션 추출
        elif "Business" in text or "Financial" in text:
            # Business Overview
            business_match = re.search(r'Business[^\n]*([^Financial]*)', text, re.IGNORECASE)
            if business_match:
                sections["Business Overview"] = business_match.group(1)[:500].strip()
                
            # Financial Data
            financial_match = re.search(r'Financial\s+Data[^\n]*([^Risk]*)', text, re.IGNORECASE)
            if financial_match:
                sections["Financial Data"] = financial_match.group(1)[:500].strip()
                
        return sections
        
    async def get_major_filings(self,
                               ticker: str,
                               days: int = 90) -> Dict[str, Any]:
        """
        특정 종목의 주요 공시만 가져오기
        
        Args:
            ticker: 종목 티커
            days: 조회 기간 (일)
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # 주요 폼 타입만 조회
        major_forms = ["10-K", "10-Q", "8-K", "DEF 14A"]
        all_filings = []
        
        # 모든 공시 가져오기
        result = await self.search_filings(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date
        )
        
        if result["status"] == "success":
            # 주요 공시만 필터링
            for filing in result.get("filings", []):
                if filing["form_type"] in major_forms:
                    all_filings.append(filing)
                    
        return {
            "status": "success",
            "data_source": "REAL_DATA",
            "ticker": ticker,
            "period": f"{start_date} ~ {end_date}",
            "count": len(all_filings),
            "filings": all_filings
        }
        
    async def compare_companies(self,
                               tickers: List[str],
                               form_type: str = "10-K") -> Dict[str, Any]:
        """
        여러 회사의 공시 비교
        
        Args:
            tickers: 비교할 회사들의 티커 리스트
            form_type: 비교할 공시 유형
        """
        comparison = {}
        
        for ticker in tickers:
            result = await self.search_filings(
                ticker=ticker,
                form_type=form_type,
                limit=1
            )
            
            if result["status"] == "success" and result.get("filings"):
                latest_filing = result["filings"][0]
                comparison[ticker] = {
                    "company_name": result["company_name"],
                    "latest_filing_date": latest_filing["filing_date"],
                    "filing_url": latest_filing["filing_url"]
                }
            else:
                comparison[ticker] = {
                    "error": f"No {form_type} found"
                }
                
        return {
            "status": "success",
            "data_source": "REAL_DATA",
            "form_type": form_type,
            "comparison": comparison
        }


# 테스트 함수
async def test_sec_agent():
    """SEC Agent 테스트"""
    print("=== SEC Agent 테스트 ===\\n")
    
    async with SECAgent() as agent:
        # 1. Apple 공시 검색
        print("1. Apple (AAPL) 최근 공시")
        result = await agent.search_filings(ticker="AAPL", limit=5)
        if result["status"] == "success":
            print(f"회사명: {result.get('company_name')}")
            print(f"검색 결과: {result.get('count')}건")
            for filing in result.get("filings", []):
                print(f"- [{filing['filing_date']}] {filing['form_type']}: {filing['description']}")
        else:
            print(f"오류: {result.get('message')}")
            
        print("\\n" + "-" * 50 + "\\n")
        
        # 2. Tesla 8-K 검색
        print("2. Tesla (TSLA) 8-K 공시")
        result = await agent.search_filings(
            ticker="TSLA",
            form_type="8-K",
            limit=3
        )
        if result["status"] == "success":
            print(f"검색 결과: {result.get('count')}건")
            for filing in result.get("filings", []):
                print(f"- [{filing['filing_date']}] {filing['form_type']}")
                print(f"  URL: {filing['filing_url']}")
        else:
            print(f"오류: {result.get('message')}")
            
        print("\\n" + "-" * 50 + "\\n")
        
        # 3. 여러 회사 비교
        print("3. FAANG 주식 최신 10-K 비교")
        result = await agent.compare_companies(
            tickers=["META", "AAPL", "AMZN", "NFLX", "GOOGL"],
            form_type="10-K"
        )
        if result["status"] == "success":
            for ticker, data in result["comparison"].items():
                if "error" not in data:
                    print(f"- {ticker}: {data['company_name']}")
                    print(f"  최신 10-K: {data['latest_filing_date']}")
                else:
                    print(f"- {ticker}: {data['error']}")
                    

if __name__ == "__main__":
    asyncio.run(test_sec_agent())