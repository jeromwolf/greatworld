#!/usr/bin/env python3
"""
해외 주식 테스트 스크립트
"""

import asyncio
import json
from agents.us_stock_client import USStockClient

async def test_foreign_stocks():
    """여러 해외 주식 테스트"""

    client = USStockClient()

    # 테스트할 주식 목록
    test_stocks = [
        "애플",      # 한글명
        "Apple",     # 영문명
        "AAPL",      # 심볼
        "테슬라",
        "TSLA",
        "엔비디아",
        "NVDA",
        "알리바바",
        "BABA"
    ]

    print("=" * 60)
    print("해외 주식 API 테스트")
    print("=" * 60)

    for stock in test_stocks:
        print(f"\n📊 테스트 중: {stock}")
        print("-" * 40)

        try:
            # 주식 데이터 가져오기
            data = await client.get_stock_data(stock)

            if data and 'error' not in data:
                print(f"✅ 성공: {data.get('name', 'Unknown')} ({data.get('symbol', 'N/A')})")
                print(f"   현재가: ${data.get('current_price', 0):.2f}")
                print(f"   변동률: {data.get('change_percent', 0):.2f}%")
                print(f"   시가총액: ${data.get('market_cap', 0)/1e9:.1f}B")
                print(f"   PER: {data.get('pe_ratio', 0):.2f}")
                print(f"   섹터: {data.get('sector', 'N/A')}")

                # 기술적 분석
                technical = data.get('technical', {})
                if technical:
                    print(f"   RSI: {technical.get('rsi', 0):.1f}")
                    print(f"   신호: {technical.get('signal', 'N/A')}")
                    print(f"   추세: {technical.get('trend', 'N/A')}")

                # 애널리스트 의견
                analyst = data.get('analyst', {})
                if analyst:
                    print(f"   목표가: ${analyst.get('target_mean', 0):.2f}")
                    print(f"   상승잠재력: {analyst.get('upside_potential', 0):.1f}%")
                    print(f"   추천: {analyst.get('rating', 'N/A')}")

                # 뉴스
                news = data.get('news', [])
                if news:
                    print(f"   최신 뉴스: {len(news)}건")
                    if news:
                        print(f"   - {news[0].get('title', 'N/A')[:50]}...")
            else:
                print(f"❌ 실패: {stock}")
                if data:
                    print(f"   오류: {data.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ 예외 발생: {str(e)}")

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)

async def test_sector_performance():
    """섹터별 성과 테스트"""
    client = USStockClient()

    print("\n📈 섹터별 성과")
    print("-" * 40)

    try:
        sectors = await client.get_sector_performance()
        for sector, data in sectors.items():
            print(f"{sector:15} {data['symbol']:6} ${data['price']:.2f} ({data['change']:+.2f}%)")
    except Exception as e:
        print(f"섹터 성과 조회 실패: {e}")

async def test_api_endpoint():
    """API 엔드포인트 테스트"""
    import aiohttp

    print("\n🌐 API 엔드포인트 테스트")
    print("-" * 40)

    test_queries = ["Apple", "Tesla", "NVDA"]

    async with aiohttp.ClientSession() as session:
        for query in test_queries:
            try:
                async with session.post(
                    "http://localhost:8200/api/analyze-foreign",
                    json={"message": query}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            stock_data = data.get('data', {})
                            print(f"✅ {query}: {stock_data.get('name')} - {stock_data.get('price')}")
                            print(f"   투자점수: {stock_data.get('analysis_summary', {}).get('investment_score', 0)}/100")
                            print(f"   추천: {stock_data.get('analysis_summary', {}).get('recommendation', 'N/A')}")
                        else:
                            print(f"❌ {query}: {data.get('error')}")
                    else:
                        print(f"❌ {query}: HTTP {response.status}")
            except Exception as e:
                print(f"❌ {query}: {e}")

async def main():
    """메인 테스트 함수"""
    # 1. 기본 주식 데이터 테스트
    await test_foreign_stocks()

    # 2. 섹터별 성과 테스트
    await test_sector_performance()

    # 3. API 엔드포인트 테스트
    await test_api_endpoint()

if __name__ == "__main__":
    asyncio.run(main())