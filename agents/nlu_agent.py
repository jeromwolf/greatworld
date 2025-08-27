"""
NLU (Natural Language Understanding) Agent for StockAI
자연어 쿼리를 파싱하고 의도를 분류하는 에이전트
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageHeader, MessageType


class NLUAgent(BaseAgent):
    """자연어 이해 에이전트"""
    
    def __init__(self, agent_id: str = "nlu_agent"):
        super().__init__(agent_id)
        self.intent_patterns = self._init_intent_patterns()
        self.entity_patterns = self._init_entity_patterns()
        
    def _init_intent_patterns(self) -> Dict[str, List[str]]:
        """의도 분류를 위한 패턴 초기화"""
        return {
            "analyze_stock": [
                r"분석.*해.*줘",
                r"어때\?*$",
                r"알려.*줘",
                r"보여.*줘",
                r"설명.*해",
                r"analyze",
                r"tell me about",
                r"show me"
            ],
            "compare_stocks": [
                r"비교.*해",
                r"뭐.*좋",
                r"vs",
                r"compare",
                r"versus",
                r"차이"
            ],
            "get_sentiment": [
                r"분위기",
                r"감성",
                r"sentiment",
                r"mood",
                r"버즈",
                r"여론"
            ],
            "get_financials": [
                r"재무",
                r"실적",
                r"매출",
                r"이익",
                r"financials",
                r"earnings",
                r"revenue"
            ],
            "get_news": [
                r"뉴스",
                r"소식",
                r"공시",
                r"news",
                r"announcement",
                r"최근.*소식"
            ]
        }
    
    def _init_entity_patterns(self) -> Dict[str, str]:
        """엔티티 추출을 위한 패턴 초기화"""
        return {
            # 한국 주식
            "korean_stocks": r"(삼성전자|SK하이닉스|LG에너지솔루션|현대차|카카오|네이버|셀트리온|삼성바이오로직스)",
            # 미국 주식  
            "us_stocks": r"(AAPL|Apple|MSFT|Microsoft|GOOGL|Google|AMZN|Amazon|TSLA|Tesla|META|Meta|NVDA|Nvidia)",
            # 기간
            "period": r"(오늘|어제|이번.*주|지난.*주|이번.*달|지난.*달|최근|[0-9]+일|[0-9]+주|[0-9]+개월|[0-9]+년)",
            # 티커 심볼
            "ticker": r"\b[A-Z]{1,5}\b"
        }
        
    async def process_message(self, message: A2AMessage) -> Optional[A2AMessage]:
        """메시지 처리"""
        try:
            if message.body.get("action") == "analyze_query":
                query = message.body.get("payload", {}).get("query", "")
                result = await self.analyze_query(query)
                
                return A2AMessage.create_response(
                    original_message=message,
                    sender_id=self.agent_id,
                    result=result,
                    success=True
                )
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return None
            
    async def analyze_query(self, query: str) -> Dict:
        """쿼리 분석 메인 함수"""
        # 1. 의도 분류
        intent = self._classify_intent(query)
        
        # 2. 엔티티 추출
        entities = self._extract_entities(query)
        
        # 3. 기간 파싱
        period_info = self._parse_period(entities.get("period"))
        
        # 4. 언어 감지
        language = self._detect_language(query)
        
        # 5. 정규화된 쿼리 생성
        normalized_query = self._normalize_query(query)
        
        return {
            "original_query": query,
            "normalized_query": normalized_query,
            "intent": intent,
            "entities": entities,
            "period": period_info,
            "language": language,
            "confidence": self._calculate_confidence(intent, entities)
        }
        
    def _classify_intent(self, query: str) -> str:
        """쿼리의 의도를 분류"""
        query_lower = query.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent
                    
        # 기본값은 주식 분석
        return "analyze_stock"
        
    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """쿼리에서 엔티티 추출"""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                entities[entity_type] = list(set(matches))
                
        # 주식명 통합
        stocks = []
        if "korean_stocks" in entities:
            stocks.extend(entities["korean_stocks"])
        if "us_stocks" in entities:
            stocks.extend(entities["us_stocks"]) 
        if "ticker" in entities:
            stocks.extend(entities["ticker"])
            
        if stocks:
            entities["stocks"] = stocks
            
        return entities
        
    def _parse_period(self, period_str: Optional[List[str]]) -> Dict[str, datetime]:
        """기간 문자열을 파싱하여 시작/종료 날짜 반환"""
        if not period_str:
            # 기본값: 최근 1개월
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
        else:
            period = period_str[0]
            end_date = datetime.now()
            
            # 한국어 기간 처리
            if "오늘" in period:
                start_date = end_date.replace(hour=0, minute=0, second=0)
            elif "어제" in period:
                start_date = end_date - timedelta(days=1)
                end_date = start_date
            elif "주" in period:
                weeks = int(re.findall(r"(\d+)주", period)[0]) if re.findall(r"(\d+)주", period) else 1
                start_date = end_date - timedelta(weeks=weeks)
            elif "개월" in period or "달" in period:
                months = int(re.findall(r"(\d+)개월", period)[0]) if re.findall(r"(\d+)개월", period) else 1
                start_date = end_date - timedelta(days=30*months)
            elif "년" in period:
                years = int(re.findall(r"(\d+)년", period)[0]) if re.findall(r"(\d+)년", period) else 1
                start_date = end_date - timedelta(days=365*years)
            else:
                # 기본값
                start_date = end_date - timedelta(days=30)
                
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "period_days": (end_date - start_date).days
        }
        
    def _detect_language(self, query: str) -> str:
        """쿼리 언어 감지"""
        korean_chars = re.findall(r'[가-힣]', query)
        english_chars = re.findall(r'[a-zA-Z]', query)
        
        if len(korean_chars) > len(english_chars):
            return "ko"
        else:
            return "en"
            
    def _normalize_query(self, query: str) -> str:
        """쿼리 정규화"""
        # 여러 공백을 하나로
        normalized = re.sub(r'\s+', ' ', query)
        # 앞뒤 공백 제거
        normalized = normalized.strip()
        # 물음표 여러개를 하나로
        normalized = re.sub(r'\?+', '?', normalized)
        
        return normalized
        
    def _calculate_confidence(self, intent: str, entities: Dict) -> float:
        """분석 결과의 신뢰도 계산"""
        confidence = 0.5  # 기본값
        
        # 의도가 명확하면 +0.2
        if intent != "analyze_stock":
            confidence += 0.2
            
        # 엔티티가 추출되면 +0.3
        if "stocks" in entities and entities["stocks"]:
            confidence += 0.3
            
        # 기간이 명시되면 +0.1
        if "period" in entities:
            confidence += 0.1
            
        return min(confidence, 1.0)


# 테스트를 위한 메인 함수
async def test_nlu_agent():
    agent = NLUAgent()
    
    test_queries = [
        "삼성전자 최근 실적 어때?",
        "애플이랑 마이크로소프트 비교해줘",
        "테슬라 요즘 분위기 어때?",
        "NVDA 지난 3개월 재무제표 보여줘",
        "카카오 최근 뉴스 알려줘"
    ]
    
    for query in test_queries:
        result = await agent.analyze_query(query)
        print(f"\n쿼리: {query}")
        print(f"결과: {json.dumps(result, ensure_ascii=False, indent=2)}")
        

if __name__ == "__main__":
    asyncio.run(test_nlu_agent())