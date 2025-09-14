"""
네이버 금융 API 연동 에이전트
한국 주식 실시간 데이터, 뉴스, 재무지표 수집
"""

import requests
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import feedparser
import re
from bs4 import BeautifulSoup


class NaverFinanceAgent:
    """네이버 금융 데이터 수집 에이전트"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # 주요 한국 주식 종목 코드 매핑
        self.stock_codes = {
            "삼성전자": "005930",
            "SK하이닉스": "000660",
            "LG에너지솔루션": "373220",
            "삼성바이오로직스": "207940",
            "카카오": "035720",
            "네이버": "035420",
            "현대차": "005380",
            "삼성SDI": "006400",
            "포스코홀딩스": "005490",
            "LG화학": "051910",
            "셀트리온": "068270",
            "KB금융": "105560",
            "신한지주": "055550",
            "하나금융지주": "086790",
            "삼성물산": "028260",
            "LG전자": "066570",
            "SK텔레콤": "017670",
            "KT": "030200",
            "현대모비스": "012330",
            "NAVER": "035420"
        }

    async def get_stock_info(self, stock_name: str) -> Dict:
        """주식 기본 정보 및 실시간 가격 조회"""
        try:
            stock_code = self.stock_codes.get(stock_name)
            if not stock_code:
                return {"status": "error", "message": f"'{stock_name}' 종목 코드를 찾을 수 없습니다"}

            # 네이버 금융 API 호출
            url = f"https://polling.finance.naver.com/api/realtime/domesticstock/stock/{stock_code}"

            response = self.session.get(url)
            if response.status_code != 200:
                return {"status": "error", "message": "데이터 조회 실패"}

            data = response.json()
            stock_data = data.get("datas", [{}])[0] if data.get("datas") else {}

            return {
                "status": "success",
                "data": {
                    "name": stock_name,
                    "code": stock_code,
                    "current_price": int(stock_data.get("nv", 0)),
                    "change": int(stock_data.get("cv", 0)),
                    "change_percent": float(stock_data.get("cr", 0)),
                    "volume": int(stock_data.get("aq", 0)),
                    "trade_value": int(stock_data.get("aa", 0)),
                    "market_cap": int(stock_data.get("ms", 0)),
                    "high": int(stock_data.get("hv", 0)),
                    "low": int(stock_data.get("lv", 0)),
                    "open": int(stock_data.get("ov", 0)),
                    "previous_close": int(stock_data.get("pcv", 0))
                }
            }

        except Exception as e:
            return {"status": "error", "message": f"데이터 수집 오류: {str(e)}"}

    async def get_financial_info(self, stock_name: str) -> Dict:
        """재무 정보 조회 (PER, PBR, ROE 등)"""
        try:
            stock_code = self.stock_codes.get(stock_name)
            if not stock_code:
                return {"status": "error", "message": "종목 코드 없음"}

            # 네이버 금융 투자정보 페이지 크롤링
            url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
            response = self.session.get(url)

            if response.status_code != 200:
                return {"status": "error", "message": "재무정보 조회 실패"}

            soup = BeautifulSoup(response.content, 'html.parser')

            # 재무 지표 추출
            financial_data = {}

            # PER, PBR 추출
            try:
                per_element = soup.find('em', {'id': 'per'})
                financial_data['per'] = float(per_element.text.replace(',', '')) if per_element and per_element.text != 'N/A' else None

                pbr_element = soup.find('em', {'id': 'pbr'})
                financial_data['pbr'] = float(pbr_element.text.replace(',', '')) if pbr_element and pbr_element.text != 'N/A' else None

                # EPS 추출
                eps_element = soup.find('em', {'id': 'eps'})
                financial_data['eps'] = float(eps_element.text.replace(',', '').replace('원', '')) if eps_element and eps_element.text != 'N/A' else None

                # BPS 추출
                bps_element = soup.find('em', {'id': 'bps'})
                financial_data['bps'] = float(bps_element.text.replace(',', '').replace('원', '')) if bps_element and bps_element.text != 'N/A' else None

            except Exception as e:
                print(f"재무지표 파싱 오류: {e}")

            # 52주 최고/최저가 추출
            try:
                high_52w_element = soup.select_one('.tab_con1 .blind dd:nth-child(5)')
                low_52w_element = soup.select_one('.tab_con1 .blind dd:nth-child(6)')

                if high_52w_element:
                    financial_data['high_52w'] = int(high_52w_element.text.replace(',', '').replace('원', ''))
                if low_52w_element:
                    financial_data['low_52w'] = int(low_52w_element.text.replace(',', '').replace('원', ''))

            except Exception as e:
                print(f"52주 최고/최저가 파싱 오류: {e}")

            return {
                "status": "success",
                "data": financial_data
            }

        except Exception as e:
            return {"status": "error", "message": f"재무정보 수집 오류: {str(e)}"}

    async def get_news(self, stock_name: str, limit: int = 10) -> Dict:
        """종목 관련 뉴스 조회"""
        try:
            stock_code = self.stock_codes.get(stock_name)
            if not stock_code:
                return {"status": "error", "message": "종목 코드 없음"}

            # 네이버 금융 뉴스 RSS
            rss_url = f"https://finance.naver.com/item/news_news.naver?code={stock_code}&sm=title_entity_id.basic&clusterId="

            # RSS 피드 파싱
            feed = feedparser.parse(rss_url)

            news_list = []
            for entry in feed.entries[:limit]:
                news_item = {
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.published,
                    "summary": getattr(entry, 'summary', '')[:200] + '...' if hasattr(entry, 'summary') else '',
                    "source": "네이버 금융"
                }
                news_list.append(news_item)

            return {
                "status": "success",
                "data": {
                    "stock_name": stock_name,
                    "news_count": len(news_list),
                    "articles": news_list
                }
            }

        except Exception as e:
            return {"status": "error", "message": f"뉴스 수집 오류: {str(e)}"}

    async def get_analyst_opinions(self, stock_name: str) -> Dict:
        """증권사 분석 의견 조회"""
        try:
            stock_code = self.stock_codes.get(stock_name)
            if not stock_code:
                return {"status": "error", "message": "종목 코드 없음"}

            # 네이버 금융 투자의견 페이지
            url = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}&target=analyst"
            response = self.session.get(url)

            if response.status_code != 200:
                return {"status": "error", "message": "분석 의견 조회 실패"}

            soup = BeautifulSoup(response.content, 'html.parser')

            # 투자의견 테이블 파싱
            opinions = []
            try:
                table = soup.find('table', class_='tb_data1 tb_data1_analyst')
                if table:
                    rows = table.find_all('tr')[1:]  # 헤더 제외

                    for row in rows[:5]:  # 최근 5개
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 6:
                            opinion = {
                                "date": cells[0].text.strip(),
                                "firm": cells[1].text.strip(),
                                "analyst": cells[2].text.strip(),
                                "opinion": cells[3].text.strip(),
                                "target_price": cells[4].text.strip().replace(',', '').replace('원', ''),
                                "current_price": cells[5].text.strip().replace(',', '').replace('원', '')
                            }
                            opinions.append(opinion)
            except Exception as e:
                print(f"분석의견 파싱 오류: {e}")

            return {
                "status": "success",
                "data": {
                    "stock_name": stock_name,
                    "opinions": opinions
                }
            }

        except Exception as e:
            return {"status": "error", "message": f"분석 의견 수집 오류: {str(e)}"}

    async def get_chart_data(self, stock_name: str, period: str = "1M") -> Dict:
        """차트 데이터 조회 (1일, 1주, 1개월, 3개월, 1년)"""
        try:
            stock_code = self.stock_codes.get(stock_name)
            if not stock_code:
                return {"status": "error", "message": "종목 코드 없음"}

            # 기간별 코드 매핑
            period_codes = {
                "1D": "day",
                "1W": "week",
                "1M": "month",
                "3M": "month3",
                "1Y": "year"
            }

            period_code = period_codes.get(period, "month")

            # 네이버 금융 차트 데이터 API
            url = f"https://fchart.stock.naver.com/sise.nhn?symbol={stock_code}&timeframe={period_code}&count=100&requestType=0"

            response = self.session.get(url)
            if response.status_code != 200:
                return {"status": "error", "message": "차트 데이터 조회 실패"}

            # XML 파싱 (네이버 차트는 XML 형식)
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)

            chart_data = []
            for item in root.findall('.//item'):
                data = item.get('data', '').split('|')
                if len(data) >= 5:
                    chart_data.append({
                        "date": data[0],
                        "open": float(data[1]),
                        "high": float(data[2]),
                        "low": float(data[3]),
                        "close": float(data[4]),
                        "volume": int(data[5]) if len(data) > 5 else 0
                    })

            return {
                "status": "success",
                "data": {
                    "stock_name": stock_name,
                    "period": period,
                    "chart_data": chart_data[-30:]  # 최근 30개 데이터
                }
            }

        except Exception as e:
            return {"status": "error", "message": f"차트 데이터 수집 오류: {str(e)}"}

    async def get_comprehensive_analysis(self, stock_name: str) -> Dict:
        """종합 분석 (가격, 재무, 뉴스, 분석의견, 차트)"""
        try:
            # 병렬로 모든 데이터 수집
            results = await asyncio.gather(
                self.get_stock_info(stock_name),
                self.get_financial_info(stock_name),
                self.get_news(stock_name, 5),
                self.get_analyst_opinions(stock_name),
                self.get_chart_data(stock_name, "1M"),
                return_exceptions=True
            )

            stock_info, financial_info, news, opinions, chart_data = results

            # 결과 통합
            analysis = {
                "status": "success",
                "stock_name": stock_name,
                "timestamp": datetime.now().isoformat(),
                "data_sources": ["네이버금융", "실시간API"],
                "stock_info": stock_info.get("data", {}) if stock_info.get("status") == "success" else {},
                "financial_info": financial_info.get("data", {}) if financial_info.get("status") == "success" else {},
                "news": news.get("data", {}) if news.get("status") == "success" else {},
                "analyst_opinions": opinions.get("data", {}) if opinions.get("status") == "success" else {},
                "chart_data": chart_data.get("data", {}) if chart_data.get("status") == "success" else {}
            }

            return analysis

        except Exception as e:
            return {"status": "error", "message": f"종합 분석 오류: {str(e)}"}


# 테스트용 함수
async def test_naver_agent():
    """네이버 금융 에이전트 테스트"""
    agent = NaverFinanceAgent()

    print("=== 삼성전자 종합 분석 테스트 ===")
    result = await agent.get_comprehensive_analysis("삼성전자")

    if result["status"] == "success":
        print(f"✅ 주식정보: {result['stock_info'].get('current_price', '없음')}")
        print(f"✅ PER: {result['financial_info'].get('per', '없음')}")
        print(f"✅ 뉴스 개수: {result['news'].get('news_count', 0)}")
        print(f"✅ 분석의견: {len(result['analyst_opinions'].get('opinions', []))}")
        print(f"✅ 차트데이터: {len(result['chart_data'].get('chart_data', []))}")
    else:
        print(f"❌ 오류: {result['message']}")


if __name__ == "__main__":
    asyncio.run(test_naver_agent())