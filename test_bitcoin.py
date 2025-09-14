#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')
from agents.crypto_agent import CryptoAgent

async def test_bitcoin():
    try:
        print("Testing Bitcoin analysis...")
        async with CryptoAgent() as agent:
            print("CryptoAgent created, calling analyze_crypto...")
            result = await agent.analyze_crypto('Bitcoin')
            print(f"Bitcoin result status: {result.get('status', 'unknown')}")
            if result.get('status') == 'error':
                print(f"Error: {result.get('message', 'unknown error')}")
            else:
                print("Success!")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bitcoin())