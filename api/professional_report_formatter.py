"""
전문적인 투자 리포트 포맷터
깔끔하고 읽기 쉬운 형태로 데이터를 정리
"""
from datetime import datetime
from typing import Dict, List

class ProfessionalReportFormatter:
    """투자 분석 리포트를 전문적으로 포맷팅하는 클래스"""
    
    @staticmethod
    def format_sentiment_bar(score: float, length: int = 30) -> str:
        """감성 점수를 시각적 바로 변환"""
        if score > 0:
            filled = int(score * length)
            return "🟩" * filled + "⬜" * (length - filled)
        elif score < 0:
            filled = int(abs(score) * length)
            return "🟥" * filled + "⬜" * (length - filled)
        else:
            return "⬜" * length
    
    @staticmethod
    def format_report(company_name: str, sentiment_result, data_source_info: str, 
                     news_data: Dict, dart_data: Dict, financial_data: str = None,
                     price_data: Dict = None, financial_analysis: Dict = None) -> str:
        """전체 리포트 포맷팅"""
        
        # 데이터 신뢰도 계산
        real_count = 0
        mock_count = 0
        for source_data in sentiment_result.data_sources.values():
            if source_data.get('data_source') == 'REAL_DATA':
                real_count += 1
            else:
                mock_count += 1
        
        reliability_text = "🟢 높음" if mock_count == 0 else "🟡 중간" if real_count > mock_count else "🔴 낮음"
        
        # 헤더
        report = f"""
================================================================================
                    💹 {company_name} 투자 분석 리포트 💹
================================================================================
"""
        
        # 주가 정보 표시 (최상단)
        if price_data and price_data.get("status") == "success":
            price_info = price_data.get("price_data", {})
            current_price = price_info.get("current_price", 0)
            change_percent = price_info.get("change_percent", 0)
            change = price_info.get("change", 0)
            
            # 등락 표시
            if change_percent > 0:
                price_icon = "📈"
                change_str = f"+{change_percent:.2f}%"
            elif change_percent < 0:
                price_icon = "📉"  
                change_str = f"{change_percent:.2f}%"
            else:
                price_icon = "➖"
                change_str = "0.00%"
                
            report += f"\n💰 현재가: {current_price:,.0f}원 {price_icon} {change_str}"
            report += f"\n📊 거래량: {price_info.get('volume', 0):,}"
            report += f"\n📈 52주 최고: {price_info.get('week_52_high', 0):,.0f}원"
            report += f"\n📉 52주 최저: {price_info.get('week_52_low', 0):,.0f}원\n"
            
        report += f"\n📊 데이터 신뢰도: {reliability_text} (실제 데이터 {real_count}개 / 전체 {real_count + mock_count}개)"
        report += f"\n{data_source_info}"
        
        report += f"""

--------------------------------------------------------------------------------
📊 종합 평가
--------------------------------------------------------------------------------
▪️ 시장 감성: {sentiment_result.overall_sentiment:+.2f} ({sentiment_result.sentiment_label})
▪️ 신뢰도: {'⭐' * min(5, int(sentiment_result.confidence * 5))} ({sentiment_result.confidence:.0%})
▪️ 분석일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}

"""
        
        # 핵심 인사이트
        if sentiment_result.key_factors:
            report += "💡 핵심 인사이트\n"
            for factor in sentiment_result.key_factors:
                report += f"  • {factor}\n"
            report += "\n"
        
        # 뉴스 섹션 - 유용한 정보 강조
        if news_data.get("articles"):
            report += "--------------------------------------------------------------------------------\n"
            report += f"📰 최근 뉴스 분석 ({len(news_data['articles'])}건)\n"
            report += "--------------------------------------------------------------------------------\n"
            
            # 카테고리별로 뉴스 분류
            categorized_news = ProfessionalReportFormatter._categorize_news(news_data["articles"])
            
            # 중요도 순으로 표시
            if categorized_news["critical"]:
                report += "\n🚨 **즉시 확인 필요**\n"
                for article in categorized_news["critical"][:3]:
                    report += f"  ▸ {article['title']}\n"
                    if article.get('key_info'):
                        report += f"    [{article['key_info']}]\n"
            
            if categorized_news["important"]:
                report += "\n💡 **주요 뉴스**\n"
                for article in categorized_news["important"][:5]:
                    report += f"  ▸ {article['title']}\n"
                    if article.get('key_info'):
                        report += f"    [{article['key_info']}]\n"
            
            if categorized_news["general"]:
                report += "\n📌 **일반 뉴스**\n"
                for article in categorized_news["general"][:2]:
                    report += f"  ▸ {article['title']}\n"
            
            report += "\n"
        
        # 재무 분석 데이터 (별도 섹션)
        if financial_analysis and financial_analysis.get("status") == "success":
            report += "--------------------------------------------------------------------------------\n"
            report += f"💰 재무 건전성 분석\n"
            report += "--------------------------------------------------------------------------------\n"
            
            # 재무 건전성 점수
            health_score = financial_analysis.get("health_score", {})
            report += f"▫️ 재무 건전성: {health_score.get('grade', 'N/A')} ({health_score.get('grade_text', '')})\n"
            report += f"▫️ 종합 점수: {health_score.get('score', 0)}/{health_score.get('max_score', 100)}점\n"
            report += f"▫️ {health_score.get('evaluation', '')}\n\n"
            
            # 주요 재무 비율
            ratios = financial_analysis.get("ratios", {})
            if ratios:
                report += "📊 주요 재무지표\n"
                report += f"  • ROE: {ratios.get('roe', 0):.1f}% (자기자본수익률)\n"
                report += f"  • ROA: {ratios.get('roa', 0):.1f}% (총자산수익률)\n"
                report += f"  • 영업이익률: {ratios.get('opm', 0):.1f}%\n"
                report += f"  • 부채비율: {ratios.get('debt_ratio', 0):.1f}%\n"
                report += f"  • 유동비율: {ratios.get('current_ratio', 0):.1f}%\n\n"
            
            # 투자 포인트
            investment_points = financial_analysis.get("investment_points", [])
            if investment_points:
                report += "💡 주요 투자 포인트\n"
                for point in investment_points[:4]:
                    report += f"  {point}\n"
                report += "\n"
        
        # 공시 및 재무 데이터
        report += "--------------------------------------------------------------------------------\n"
        report += f"📋 주요 공시 현황\n"
        report += "--------------------------------------------------------------------------------\n"
        
        if dart_data.get("disclosures"):
            # 재무 데이터가 있으면 표시
            if financial_data:
                report += financial_data + "\n"
            
            # 공시 목록
            for disclosure in dart_data["disclosures"][:3]:
                report += f"▫️ {disclosure['report_nm']} ({disclosure['rcept_dt']})\n"
        else:
            # 공시가 없는 경우
            report += "💡 최근 45일간 주요 공시가 없습니다.\n"
            report += "• 정기보고서 시즌이 아니거나 특별한 공시사항이 없는 기간입니다.\n"
            
        report += "\n"
        
        # 감성 분포 차트
        report += "--------------------------------------------------------------------------------\n"
        report += "📊 데이터 소스별 감성 분석\n"
        report += "--------------------------------------------------------------------------------\n"
        
        for source_name, source_data in sentiment_result.data_sources.items():
            score = source_data.get('sentiment', 0.0)
            count = source_data.get('count', 0)
            bar = ProfessionalReportFormatter.format_sentiment_bar(score)
            
            report += f"\n{source_name.upper():<12} [{score:+.2f}] ({count}건)\n"
            report += f"{bar}\n"
        
        # AI 의견
        report += "\n--------------------------------------------------------------------------------\n"
        report += "🤖 AI 투자 의견\n"
        report += "--------------------------------------------------------------------------------\n"
        report += sentiment_result.recommendation
        report += "\n\n================================================================================\n"
        
        return report
    
    @staticmethod
    def _categorize_news(articles: List[Dict]) -> Dict[str, List[Dict]]:
        """
        뉴스를 중요도별로 분류
        
        - critical: 즉시 확인이 필요한 뉴스 (실적 급변, 규제 이슈, 대규모 계약)
        - important: 투자 판단에 중요한 뉴스 (목표가 변경, 신제품, 파트너십)  
        - general: 일반적인 시장 소식
        """
        categorized = {
            "critical": [],
            "important": [],
            "general": []
        }
        
        critical_keywords = [
            "급등", "급락", "폭등", "폭락", "상한가", "하한가",
            "실적 쇼크", "어닝 서프라이즈", "규제", "제재", "조사",
            "리콜", "사고", "논란", "스캔들",
            "plunge", "surge", "crash", "investigation", "scandal"
        ]
        
        important_keywords = [
            "목표가", "상향", "하향", "매수", "매도",
            "신제품", "출시", "계약", "파트너십", "투자",
            "배당", "자사주", "실적", "성장", "혁신",
            "target", "upgrade", "downgrade", "buy", "sell",
            "launch", "partnership", "dividend", "earnings"
        ]
        
        for article in articles:
            title = article.get("title", "").lower()
            
            # Critical 뉴스 체크
            if any(keyword in title for keyword in critical_keywords):
                categorized["critical"].append(article)
            # Important 뉴스 체크
            elif any(keyword in title for keyword in important_keywords):
                categorized["important"].append(article)
            # 나머지는 General
            else:
                categorized["general"].append(article)
        
        return categorized