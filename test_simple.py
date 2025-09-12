import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8200/ws/simple_test"
    async with websockets.connect(uri) as ws:
        # Receive welcome
        welcome = await ws.recv()
        print("Welcome:", json.loads(welcome)["message"])
        
        # Send query
        await ws.send("애플 분석")
        print("Sent: 애플 분석")
        
        # Receive responses
        for i in range(10):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(msg)
                print(f"Response {i+1}:", data.get("type"), "-", 
                      data.get("message", "")[:100] if data.get("message") else data)
            except asyncio.TimeoutError:
                break
            except Exception as e:
                print(f"Error: {e}")
                break

asyncio.run(test())
