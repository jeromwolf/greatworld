#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys

async def test_stock_query(stock_name="삼성전자"):
    """대시보드 WebSocket 테스트"""
    uri = "ws://localhost:8200/ws/test_client_dashboard"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"[연결됨] WebSocket connected to {uri}")
            
            # 초기 연결 메시지 받기
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"[서버] {welcome_data['message']}")
            
            # 쿼리 전송
            query = f"{stock_name} 분석해줘"
            print(f"\n[전송] {query}")
            await websocket.send(query)
            
            # 응답 대기 (여러 메시지 올 수 있음)
            timeout_count = 0
            while timeout_count < 3:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    data = json.loads(response)
                    
                    # 시스템 메시지
                    if data.get("type") == "system":
                        print(f"[시스템] {data.get('message')}")
                    
                    # 대시보드 데이터
                    elif "stock_name" in data:
                        print(f"\n===== 분석 결과 =====")
                        print(f"종목명: {data.get('stock_name')}")
                        print(f"현재가: {data.get('price')}")
                        print(f"변동률: {data.get('change')}")
                        print(f"감성점수: {data.get('sentiment')} ({data.get('sentiment_label')})")
                        print(f"추천사항: {data.get('sentiment_reason')}")
                        
                        if data.get('news'):
                            print(f"\n뉴스 ({len(data['news'])}건):")
                            for news in data['news'][:3]:
                                if isinstance(news, dict):
                                    print(f"  - {news.get('title', news)}")
                                else:
                                    print(f"  - {news}")
                        
                        if data.get('insights'):
                            print(f"\nAI 인사이트:")
                            for insight in data['insights']:
                                print(f"  - {insight}")
                        
                        print("====================\n")
                        break  # 데이터 받았으면 종료
                    
                    # 기타 메시지
                    else:
                        print(f"[응답] {json.dumps(data, ensure_ascii=False, indent=2)}")
                        
                except asyncio.TimeoutError:
                    timeout_count += 1
                    print(f"[대기중] Waiting for response... ({timeout_count}/3)")
                    
    except Exception as e:
        print(f"[오류] {e}")
        return False
    
    return True

if __name__ == "__main__":
    stock = sys.argv[1] if len(sys.argv) > 1 else "삼성전자"
    print(f"StockAI Dashboard Test - Testing: {stock}")
    print("="*50)
    
    success = asyncio.run(test_stock_query(stock))
    
    if success:
        print("\n✅ 테스트 성공!")
    else:
        print("\n❌ 테스트 실패!")