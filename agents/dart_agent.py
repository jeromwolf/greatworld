"""
DART Agent - 한국 공시 데이터 수집 에이전트
금융감독원 DART API를 통한 국내 기업 공시 정보 수집
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
import xml.etree.ElementTree as ET


@dataclass
class DartDisclosure:
    """DART 공시 데이터 모델"""
    rcept_no: str          # 접수번호
    corp_code: str         # 고유번호
    corp_name: str         # 회사명
    report_nm: str         # 보고서명
    rcept_dt: str          # 접수일자
    rm: str                # 비고
    stock_code: str = ""   # 종목코드
    

class DartAgent:
    """DART 공시 데이터 수집 에이전트"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DART_API_KEY", "")
        self.base_url = "https://opendart.fss.or.kr/api"
        self.session = None
        
        # 주요 공시 유형
        self.major_disclosure_types = {
            "A": "정기공시",
            "B": "주요사항보고",
            "C": "발행공시",
            "D": "지분공시",
            "E": "기타공시",
            "F": "외부감사관련",
            "G": "펀드공시",
            "H": "자산유동화",
            "I": "거래소공시",
            "J": "공정위공시"
        }
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
            
    async def search_disclosures(self, 
                               corp_code: Optional[str] = None,
                               stock_code: Optional[str] = None,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None,
                               pblntf_ty: Optional[str] = None,
                               page_no: int = 1,
                               page_count: int = 10) -> Dict[str, Any]:
        """
        공시 검색
        
        Args:
            corp_code: 고유번호
            stock_code: 종목코드
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            pblntf_ty: 공시유형 (A~J)
            page_no: 페이지 번호
            page_count: 페이지당 건수
        """
        if not self.api_key:
            return {"status": "error", "message": "DART API key not configured"}
            
        # 날짜 기본값 설정 (최근 30일)
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            
        params = {
            "crtfc_key": self.api_key,
            "bgn_de": start_date,
            "end_de": end_date,
            "page_no": page_no,
            "page_count": page_count
        }
        
        # 선택적 파라미터 추가
        if corp_code:
            params["corp_code"] = corp_code
        if pblntf_ty:
            params["pblntf_ty"] = pblntf_ty
            
        try:
            async with self.session.get(
                f"{self.base_url}/list.json",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("status") == "000":
                        # 성공
                        disclosures = []
                        for item in data.get("list", []):
                            disclosure = DartDisclosure(
                                rcept_no=item.get("rcept_no", ""),
                                corp_code=item.get("corp_code", ""),
                                corp_name=item.get("corp_name", ""),
                                report_nm=item.get("report_nm", ""),
                                rcept_dt=item.get("rcept_dt", ""),
                                rm=item.get("rm", ""),
                                stock_code=item.get("stock_code", "")
                            )
                            disclosures.append(asdict(disclosure))
                            
                        return {
                            "status": "success",
                            "data_source": "REAL_DATA",
                            "total_count": data.get("total_count", 0),
                            "total_page": data.get("total_page", 0),
                            "disclosures": disclosures
                        }
                    else:
                        return {
                            "status": "error",
                            "message": data.get("message", "Unknown error")
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
            
    async def get_disclosure_detail(self, rcept_no: str) -> Dict[str, Any]:
        """
        공시 상세 정보 조회
        
        Args:
            rcept_no: 접수번호
        """
        if not self.api_key:
            return {"status": "error", "message": "DART API key not configured"}
            
        params = {
            "crtfc_key": self.api_key,
            "rcept_no": rcept_no
        }
        
        try:
            # 문서 다운로드 URL 생성
            viewer_url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"
            
            # XML 형식으로 공시 내용 조회
            async with self.session.get(
                f"{self.base_url}/document.xml",
                params=params
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # 간단한 파싱 (실제로는 더 정교한 파싱 필요)
                    summary = self._parse_disclosure_xml(content)
                    
                    return {
                        "status": "success",
                        "data_source": "REAL_DATA",
                        "rcept_no": rcept_no,
                        "viewer_url": viewer_url,
                        "summary": summary
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
            
    def _parse_disclosure_xml(self, xml_content: str) -> str:
        """XML 공시 내용 파싱 (간단한 요약)"""
        try:
            # 실제로는 더 정교한 파싱이 필요하지만, 
            # 여기서는 간단히 텍스트만 추출
            root = ET.fromstring(xml_content)
            text_content = []
            
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    text_content.append(elem.text.strip())
                    
            # 첫 500자만 요약으로 반환
            summary = " ".join(text_content)[:500]
            return summary if summary else "내용 파싱 실패"
            
        except Exception as e:
            return f"파싱 오류: {str(e)}"
            
    async def search_by_company_name(self, company_name: str) -> Dict[str, Any]:
        """
        회사명으로 공시 검색
        
        Args:
            company_name: 회사명 (예: "삼성전자")
        """
        # 회사명으로 corp_code 검색하는 기능이 필요
        # 실제로는 DART에서 제공하는 고유번호 API를 사용해야 함
        
        # 임시로 주요 기업 매핑
        company_mapping = {
            "삼성전자": "00126380",
            "SK하이닉스": "00164779",
            "LG에너지솔루션": "01251716",
            "현대차": "00164742",
            "카카오": "00256598",
            "네이버": "00226352",
            "포스코": "00123666"
        }
        
        corp_code = company_mapping.get(company_name)
        if not corp_code:
            return {
                "status": "error",
                "message": f"회사 '{company_name}'의 고유번호를 찾을 수 없습니다"
            }
            
        return await self.search_disclosures(corp_code=corp_code)
        
    async def get_major_disclosures(self, 
                                  stock_code: str,
                                  days: int = 30) -> Dict[str, Any]:
        """
        특정 종목의 주요 공시만 가져오기
        
        Args:
            stock_code: 종목코드
            days: 조회 기간 (일)
        """
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        
        # 주요사항보고(B)와 정기공시(A)만 조회
        major_types = ["A", "B"]
        all_disclosures = []
        
        for pblntf_ty in major_types:
            result = await self.search_disclosures(
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                pblntf_ty=pblntf_ty
            )
            
            if result["status"] == "success":
                all_disclosures.extend(result.get("disclosures", []))
                
        # 날짜순 정렬
        all_disclosures.sort(key=lambda x: x["rcept_dt"], reverse=True)
        
        return {
            "status": "success",
            "data_source": "REAL_DATA",
            "stock_code": stock_code,
            "period": f"{start_date} ~ {end_date}",
            "count": len(all_disclosures),
            "disclosures": all_disclosures
        }


# 테스트 함수
async def test_dart_agent():
    """DART Agent 테스트"""
    print("=== DART Agent 테스트 ===\\n")
    
    # API 키 확인
    api_key = os.getenv("DART_API_KEY")
    if not api_key:
        print("⚠️  DART_API_KEY 환경변수가 설정되지 않았습니다.")
        print("테스트를 위한 모의 데이터를 반환합니다.\\n")
        
        # 모의 데이터
        mock_data = {
            "status": "success",
            "data_source": "MOCK_DATA",
            "message": "⚠️ 모의 데이터 - DART API 키가 설정되지 않음",
            "disclosures": [
                {
                    "corp_name": "삼성전자",
                    "report_nm": "분기보고서 (2024.09)",
                    "rcept_dt": "20240810",
                    "summary": "3분기 영업이익 15.8조원, 전년 동기 대비 30% 증가"
                },
                {
                    "corp_name": "삼성전자",
                    "report_nm": "주요사항보고서(자기주식취득신탁계약체결결정)",
                    "rcept_dt": "20240805",
                    "summary": "3조원 규모 자사주 매입 결정"
                }
            ]
        }
        print(json.dumps(mock_data, indent=2, ensure_ascii=False))
        return
        
    async with DartAgent(api_key) as agent:
        # 1. 최근 공시 검색
        print("1. 최근 공시 검색 (전체)")
        result = await agent.search_disclosures(page_count=5)
        print(f"상태: {result.get('status')}")
        print(f"전체 건수: {result.get('total_count', 0)}")
        print("-" * 50)
        
        # 2. 삼성전자 공시 검색
        print("\\n2. 삼성전자 공시 검색")
        result = await agent.search_by_company_name("삼성전자")
        if result["status"] == "success":
            print(f"검색 결과: {len(result.get('disclosures', []))}건")
            for disclosure in result.get('disclosures', [])[:3]:
                print(f"- [{disclosure['rcept_dt']}] {disclosure['report_nm']}")
        else:
            print(f"오류: {result.get('message')}")
            

if __name__ == "__main__":
    asyncio.run(test_dart_agent())