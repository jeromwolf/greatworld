"""
한국 주식 뉴스 수집 에이전트
RSS 피드 기반으로 실시간 뉴스 수집
"""

import feedparser
import requests
from datetime import datetime, timedelta
from typing import Dict, List
import asyncio
import re


class KoreanNewsAgent:
    """한국 주식 뉴스 수집 에이전트"""

    def __init__(self):
        # 한국 주요 경제 뉴스 RSS 피드
        self.news_sources = {
            "한국경제": "https://rss.hankyung.com/new/news_main.xml",
            "매일경제": "https://rss.mk.co.kr/rss/40000001.xml",
            "서울경제": "https://www.sedaily.com/RSS/S11.xml",
            "이데일리": "https://rss.edaily.co.kr/edaily_news.xml",
            "아시아경제": "https://rss.asiae.co.kr/uhtml/rss/economy.xml",
            "파이낸셜뉴스": "https://www.fnnews.com/rss/fn_realnews_economy.xml"
        }

        # 주요 기업 키워드
        self.company_keywords = [
            "삼성전자", "SK하이닉스", "LG에너지솔루션", "카카오", "네이버",
            "현대차", "셀트리온", "삼성바이오로직스", "포스코홀딩스", "LG화학",
            "KB금융", "신한지주", "하나금융지주", "LG전자", "SK텔레콤"
        ]

        # 주식 관련 키워드
        self.stock_keywords = [
            "주가", "상장", "실적", "매출", "영업이익", "순이익", "배당",
            "목표주가", "투자의견", "매수", "매도", "중립", "BUY", "SELL",
            "코스피", "코스닥", "증권", "투자", "펀드"
        ]

    async def collect_news(self, hours: int = 24) -> Dict:
        """최근 뉴스 수집"""
        try:
            all_news = []
            cutoff_time = datetime.now() - timedelta(hours=hours)

            for source_name, rss_url in self.news_sources.items():
                try:
                    print(f"📰 {source_name} 뉴스 수집 중...")
                    feed = feedparser.parse(rss_url)

                    for entry in feed.entries[:10]:  # 각 소스당 최대 10개
                        # 시간 필터링
                        try:
                            pub_time = datetime(*entry.published_parsed[:6])
                            if pub_time < cutoff_time:
                                continue
                        except:
                            pass  # 시간 파싱 실패시 그냥 포함

                        # 주식 관련성 체크
                        title = entry.title
                        summary = getattr(entry, 'summary', '')

                        relevance_score = self._calculate_relevance(title + ' ' + summary)

                        if relevance_score > 0:  # 관련도가 있는 경우만
                            news_item = {
                                "title": title,
                                "link": entry.link,
                                "published": entry.published,
                                "source": source_name,
                                "summary": summary[:200] + '...' if len(summary) > 200 else summary,
                                "relevance_score": relevance_score,
                                "companies": self._extract_companies(title + ' ' + summary)
                            }
                            all_news.append(news_item)

                except Exception as e:
                    print(f"❌ {source_name} 수집 실패: {e}")
                    continue

            # 관련도순으로 정렬
            all_news.sort(key=lambda x: x['relevance_score'], reverse=True)

            return {
                "status": "success",
                "collected_at": datetime.now().isoformat(),
                "total_news": len(all_news),
                "news": all_news[:20]  # 상위 20개만
            }

        except Exception as e:
            return {"status": "error", "message": f"뉴스 수집 오류: {str(e)}"}

    def _calculate_relevance(self, text: str) -> int:
        """뉴스의 주식 관련도 점수 계산"""
        score = 0
        text_lower = text.lower()

        # 기업명 매치 (높은 점수)
        for company in self.company_keywords:
            if company in text:
                score += 5

        # 주식 키워드 매치
        for keyword in self.stock_keywords:
            if keyword in text:
                score += 2

        # 부정적 키워드 (관련도 증가)
        negative_keywords = ["하락", "급락", "폭락", "손실", "적자", "위험"]
        for keyword in negative_keywords:
            if keyword in text:
                score += 3

        # 긍정적 키워드 (관련도 증가)
        positive_keywords = ["상승", "급등", "호재", "수익", "흑자", "성과"]
        for keyword in positive_keywords:
            if keyword in text:
                score += 3

        return score

    def _extract_companies(self, text: str) -> List[str]:
        """텍스트에서 기업명 추출"""
        found_companies = []
        for company in self.company_keywords:
            if company in text:
                found_companies.append(company)
        return found_companies

    async def get_company_news(self, company_name: str, limit: int = 5) -> Dict:
        """특정 기업 관련 뉴스만 필터링"""
        try:
            all_news_result = await self.collect_news(hours=48)  # 48시간치 수집

            if all_news_result["status"] != "success":
                return all_news_result

            # 해당 기업 뉴스만 필터링
            company_news = []
            for news in all_news_result["news"]:
                if company_name in news["companies"] or company_name in news["title"]:
                    company_news.append(news)

            return {
                "status": "success",
                "company": company_name,
                "news_count": len(company_news),
                "news": company_news[:limit]
            }

        except Exception as e:
            return {"status": "error", "message": f"기업 뉴스 수집 오류: {str(e)}"}

    async def get_market_summary(self) -> Dict:
        """시장 전체 요약 뉴스"""
        try:
            all_news_result = await self.collect_news(hours=12)  # 12시간치

            if all_news_result["status"] != "success":
                return all_news_result

            # 카테고리별 분류
            categories = {
                "시장전반": [],
                "개별기업": [],
                "정책/규제": [],
                "해외영향": []
            }

            market_keywords = ["코스피", "코스닥", "증시", "시장", "지수"]
            policy_keywords = ["정부", "정책", "규제", "법안", "금리"]
            international_keywords = ["미국", "중국", "일본", "달러", "환율"]

            for news in all_news_result["news"][:15]:
                title_summary = news["title"] + " " + news.get("summary", "")

                if any(kw in title_summary for kw in market_keywords):
                    categories["시장전반"].append(news)
                elif any(kw in title_summary for kw in policy_keywords):
                    categories["정책/규제"].append(news)
                elif any(kw in title_summary for kw in international_keywords):
                    categories["해외영향"].append(news)
                elif news["companies"]:
                    categories["개별기업"].append(news)

            return {
                "status": "success",
                "summary_time": datetime.now().isoformat(),
                "categories": categories,
                "total_articles": sum(len(cat_news) for cat_news in categories.values())
            }

        except Exception as e:
            return {"status": "error", "message": f"시장 요약 오류: {str(e)}"}


# 테스트 함수
async def test_news_agent():
    """뉴스 에이전트 테스트"""
    agent = KoreanNewsAgent()

    print("=== 한국 경제 뉴스 수집 테스트 ===")

    # 전체 뉴스 수집 테스트
    result = await agent.collect_news(hours=24)
    if result["status"] == "success":
        print(f"✅ 총 {result['total_news']}개 뉴스 수집 성공")
        print("상위 3개 뉴스:")
        for i, news in enumerate(result["news"][:3], 1):
            print(f"{i}. {news['title']} (관련도: {news['relevance_score']})")
    else:
        print(f"❌ 뉴스 수집 실패: {result['message']}")

    print("\n=== 삼성전자 뉴스 테스트 ===")

    # 삼성전자 뉴스 테스트
    samsung_result = await agent.get_company_news("삼성전자", limit=3)
    if samsung_result["status"] == "success":
        print(f"✅ 삼성전자 관련 뉴스 {samsung_result['news_count']}개")
        for i, news in enumerate(samsung_result["news"], 1):
            print(f"{i}. {news['title']}")
    else:
        print(f"❌ 삼성전자 뉴스 실패: {samsung_result['message']}")


if __name__ == "__main__":
    asyncio.run(test_news_agent())