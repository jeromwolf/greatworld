"""NLU Agent 테스트 스크립트"""

import asyncio
import sys
sys.path.append('.')

from agents.nlu_agent import NLUAgent

async def main():
    # NLU Agent 초기화
    nlu = NLUAgent()
    
    # 테스트 쿼리들
    test_queries = [
        "삼성전자 최근 실적 어때?",
        "애플이랑 마이크로소프트 비교해줘", 
        "테슬라 요즘 분위기 어때?",
        "NVDA 지난 3개월 재무제표 보여줘",
        "카카오 최근 뉴스 알려줘",
        "LG에너지솔루션 이번주 주가 분석해줘",
        "Tell me about Google's sentiment",
        "최근 한달간 현대차 공시 내용 정리해줘"
    ]
    
    print("=== StockAI NLU Agent 테스트 ===\n")
    
    for query in test_queries:
        print(f"입력: {query}")
        result = await nlu.analyze_query(query)
        
        print(f"의도: {result['intent']}")
        print(f"추출된 주식: {result['entities'].get('stocks', [])}")
        print(f"기간: {result['period']['period_days']}일")
        print(f"언어: {result['language']}")
        print(f"신뢰도: {result['confidence']:.2f}")
        print("-" * 50)
        
if __name__ == "__main__":
    asyncio.run(main())