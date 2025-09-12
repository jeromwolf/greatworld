import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8200/ws/test_client"
    async with websockets.connect(uri) as websocket:
        # 테스트 쿼리 전송
        await websocket.send("삼성전자 분석해줘")
        
        # 응답 대기
        response = await websocket.recv()
        print("Response:", json.dumps(json.loads(response), indent=2, ensure_ascii=False))

asyncio.run(test())
