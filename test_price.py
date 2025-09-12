import yfinance as yf
import json

# 테스트 종목들
stocks = {
    "AAPL": "Apple",
    "005930.KS": "Samsung Electronics"
}

for symbol, name in stocks.items():
    print(f"\n=== Testing {name} ({symbol}) ===")
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        fast_info = ticker.fast_info
        
        print(f"Current Price: ${fast_info.get('lastPrice', 'N/A')}")
        print(f"Previous Close: ${fast_info.get('previousClose', 'N/A')}")
        print(f"Market Cap: ${fast_info.get('marketCap', 'N/A'):,.0f}" if fast_info.get('marketCap') else "Market Cap: N/A")
        print(f"52 Week High: ${fast_info.get('fiftyTwoWeekHigh', 'N/A')}")
        print(f"52 Week Low: ${fast_info.get('fiftyTwoWeekLow', 'N/A')}")
    except Exception as e:
        print(f"Error: {e}")
