import sys
import os
os.environ["PYTHONUNBUFFERED"] = "1"

# Add project root to path
sys.path.insert(0, '/Users/blockmeta/Desktop/blockmeta/project/stock-ai')

from agents.simple_nlu_agent import SimpleNLUAgent

# Test NLU
nlu = SimpleNLUAgent()
result = nlu.analyze_query("애플 분석해줘")
print("NLU Result:", result)

# Check entities
if result["entities"].get("stocks"):
    stock = result["entities"]["stocks"][0]
    print(f"Stock detected: {stock}")
    print(f"Is US stock: {stock in result['entities'].get('us_stocks', [])}")
    print(f"Is Korean stock: {stock in result['entities'].get('korean_stocks', [])}")
