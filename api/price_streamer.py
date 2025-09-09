"""
실시간 주가 스트리밍 서비스
WebSocket을 통한 실시간 주가 업데이트
"""

import asyncio
import json
from typing import Dict, Set
from datetime import datetime
from agents.price_agent import PriceAgent


class PriceStreamManager:
    """실시간 주가 스트리밍 관리자"""
    
    def __init__(self):
        self.active_streams: Dict[str, Set] = {}  # stock: {websockets}
        self.streaming_tasks: Dict[str, asyncio.Task] = {}
        
    async def add_stream(self, stock: str, websocket):
        """스트리밍 추가"""
        if stock not in self.active_streams:
            self.active_streams[stock] = set()
            # 새 종목이면 스트리밍 태스크 시작
            task = asyncio.create_task(self._stream_price(stock))
            self.streaming_tasks[stock] = task
            
        self.active_streams[stock].add(websocket)
        
    async def remove_stream(self, stock: str, websocket):
        """스트리밍 제거"""
        if stock in self.active_streams:
            self.active_streams[stock].discard(websocket)
            
            # 해당 종목을 보는 클라이언트가 없으면 태스크 중지
            if not self.active_streams[stock]:
                del self.active_streams[stock]
                if stock in self.streaming_tasks:
                    self.streaming_tasks[stock].cancel()
                    del self.streaming_tasks[stock]
                    
    async def _stream_price(self, stock: str):
        """특정 종목의 실시간 가격 스트리밍"""
        async with PriceAgent() as agent:
            while stock in self.active_streams:
                try:
                    # 주가 데이터 조회
                    price_data = await agent.get_stock_price(stock)
                    
                    if price_data["status"] == "success":
                        # 모든 구독자에게 전송
                        message = json.dumps({
                            "type": "price_update",
                            "stock": stock,
                            "data": price_data["price_data"],
                            "timestamp": datetime.now().isoformat()
                        }, ensure_ascii=False)
                        
                        # 연결 끊어진 websocket 제거
                        dead_websockets = set()
                        for ws in self.active_streams[stock]:
                            try:
                                await ws.send_text(message)
                            except:
                                dead_websockets.add(ws)
                                
                        # 끊어진 연결 정리
                        for ws in dead_websockets:
                            await self.remove_stream(stock, ws)
                    
                    # 10초마다 업데이트 (API 제한 고려)
                    await asyncio.sleep(10)
                    
                except Exception as e:
                    print(f"[STREAM ERROR] {stock}: {str(e)}")
                    await asyncio.sleep(30)  # 오류 시 30초 대기
                    
    async def broadcast_price(self, stock: str, price_data: Dict):
        """특정 종목 가격을 모든 구독자에게 브로드캐스트"""
        if stock in self.active_streams:
            message = json.dumps({
                "type": "price_broadcast",
                "stock": stock,
                "data": price_data,
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False)
            
            for ws in self.active_streams[stock]:
                try:
                    await ws.send_text(message)
                except:
                    pass


# 전역 스트리밍 매니저
price_stream_manager = PriceStreamManager()