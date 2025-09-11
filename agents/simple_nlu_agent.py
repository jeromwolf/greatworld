"""
간단한 NLU (Natural Language Understanding) Agent
StockAI용 자연어 쿼리 파싱 및 의도 분류
"""

import re
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class SimpleNLUAgent:
    """간단한 자연어 이해 에이전트"""
    
    def __init__(self):
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
        # 주요 해외주식 티커 및 회사명 (확장된 버전)
        us_stocks_pattern = "|".join([
            # Tech Giants (FAANG+)
            "AAPL|Apple|애플", "MSFT|Microsoft|마이크로소프트", "GOOGL|GOOG|Google|구글", 
            "AMZN|Amazon|아마존", "META|Meta|Facebook|페이스북|메타", "NVDA|Nvidia|엔비디아",
            
            # Electric Vehicles & Energy
            "TSLA|Tesla|테슬라", "NIO|Nio", "RIVN|Rivian", "LCID|Lucid",
            
            # Streaming & Entertainment  
            "NFLX|Netflix|넷플릭스", "DIS|Disney|디즈니", "SPOT|Spotify|스포티파이",
            
            # Semiconductors
            "AMD|Advanced Micro Devices", "INTC|Intel|인텔", "TSM|TSMC|Taiwan Semiconductor",
            "AVGO|Broadcom", "QCOM|Qualcomm|퀄컴", "MU|Micron",
            
            # Traditional Finance
            "JPM|JPMorgan|JP Morgan", "BAC|Bank of America", "WFC|Wells Fargo",
            "GS|Goldman Sachs|골드만삭스", "MS|Morgan Stanley",
            
            # Healthcare & Pharma
            "JNJ|Johnson & Johnson|존슨앤존슨", "PFE|Pfizer|화이자", "MRNA|Moderna|모더나",
            "UNH|UnitedHealth", "ABT|Abbott",
            
            # Consumer & Retail
            "KO|Coca Cola|코카콜라", "PEP|Pepsi|펩시", "WMT|Walmart|월마트",
            "HD|Home Depot", "MCD|McDonald\'s|맥도날드", "SBUX|Starbucks|스타벅스",
            
            # Communication & Social
            "SNAP|Snapchat|스냅챗", "TWTR|Twitter|트위터", "PINS|Pinterest",
            "UBER|우버", "LYFT|리프트",
            
            # Industrial & Aerospace
            "BA|Boeing|보잉", "GE|General Electric", "CAT|Caterpillar",
            
            # Energy & Oil
            "XOM|ExxonMobil|엑손모빌", "CVX|Chevron|쉐브론",
            
            # Crypto & Fintech
            "COIN|Coinbase|코인베이스", "SQ|Block|Square", "PYPL|PayPal|페이팔",
            
            # Chinese ADRs
            "BABA|Alibaba|알리바바", "JD|JD.com", "PDD|PinDuoDuo", "BIDU|Baidu|바이두"
        ])
        
        return {
            # 한국 주식 (정확한 매칭)
            "korean_stocks": r"(삼성전자|SK하이닉스|sk하이닉스|하이닉스|에스케이하이닉스|SK|에스케이|LG에너지솔루션|현대차|카카오|네이버|셀트리온|삼성바이오로직스|포스코|KB금융|신한금융|더본코리아|더본|CJ|롯데|신세계|현대백화점|이마트)",
            # 한국 주식 (일반적인 한글 패턴 - 알려지지 않은 종목 포착)
            "unknown_korean_stock": r"([가-힣]{2,8}(?:전자|화학|바이오|제약|건설|유통|식품|통신|금융|보험|증권|카드|코리아|그룹|홀딩스|플러스|산업|엔터|게임|테크|미디어))",
            # 미국 주식 (대폭 확장된 버전) - 한글 지원을 위해 단어 경계 제거
            "us_stocks": rf"({us_stocks_pattern})",
            # 기간
            "period": r"(오늘|어제|이번.*주|지난.*주|이번.*달|지난.*달|최근|[0-9]+일|[0-9]+주|[0-9]+개월|[0-9]+년)",
            # 티커 심볼 (정교화된 버전)
            "ticker": self._build_ticker_pattern(),
            # Stop words (확장된 버전)
            "stop_words": self._build_stop_words_pattern(),
            # 인덱스 및 ETF (새로 추가)
            "index_etf": r"\b(SPY|QQQ|IWM|VTI|VOO|VEA|VWO|GLD|SLV|TLT|BTC|ETH|ARKK|SOXL|TQQQ|SPXL)\b",
            # 암호화폐 관련
            "crypto": r"\b(Bitcoin|BTC|비트코인|Ethereum|ETH|이더리움|Dogecoin|DOGE|도지코인)\b"
        }
        
    def _build_ticker_pattern(self) -> str:
        """정교화된 티커 패턴 생성"""
        # 공식 티커 목록 (무작위 대문자 조합 방지)
        official_tickers = {
            # Tech & Growth
            "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA", 
            "NFLX", "AMD", "INTC", "TSM", "AVGO", "QCOM", "MU", "CRM", "ORCL", "ADBE",
            
            # Finance
            "JPM", "BAC", "WFC", "GS", "MS", "C", "USB", "TFC", "PNC", "BLK", "AXP",
            
            # Healthcare
            "JNJ", "PFE", "UNH", "ABT", "TMO", "DHR", "CVS", "ABBV", "MRK", "LLY", "MRNA",
            
            # Consumer
            "KO", "PEP", "WMT", "HD", "MCD", "SBUX", "NKE", "COST", "LOW", "TJX",
            
            # Communication & Social
            "DIS", "CMCSA", "VZ", "T", "NFLX", "SPOT", "SNAP", "PINS", "TWTR", "MTCH",
            
            # Industrial
            "BA", "CAT", "GE", "HON", "UPS", "FDX", "LMT", "RTX", "MMM", "DE",
            
            # Energy
            "XOM", "CVX", "COP", "EOG", "SLB", "PSX", "VLO", "MPC", "KMI", "OKE",
            
            # Transport & Mobility
            "UBER", "LYFT", "F", "GM", "RACE", "HMC", "TM",
            
            # Fintech & Crypto
            "COIN", "SQ", "PYPL", "V", "MA", "AFRM", "HOOD",
            
            # Chinese ADRs
            "BABA", "JD", "PDD", "BIDU", "NIO", "XPEV", "LI", "TME", "BILI",
            
            # EV & Clean Energy
            "RIVN", "LCID", "CHPT", "QS", "PLUG", "ENPH", "SEDG", "FSLR", "RUN"
        }
        
        return f"\\b({'|'.join(sorted(official_tickers))})\\b"
    
    def _build_stop_words_pattern(self) -> str:
        """확장된 Stop Words 패턴 생성"""
        stop_words_list = {
            # 일반 단어
            "stock", "stocks", "share", "shares", "equity", "securities",
            "analysis", "analyze", "analytical", "report", "research",
            "show", "tell", "give", "provide", "find", "search",
            "me", "you", "we", "they", "us", "them",
            "how", "what", "when", "where", "why", "which", "who",
            "is", "are", "was", "were", "being", "been", "be",
            "do", "does", "did", "doing", "done",
            "have", "has", "had", "having",
            "will", "would", "could", "should", "might", "may",
            "the", "a", "an", "and", "or", "but", "so", "if", "then",
            "to", "for", "of", "in", "on", "at", "by", "with", "from",
            "up", "down", "out", "off", "over", "under", "again",
            "further", "then", "once", "here", "there", "when", "where",
            
            # 금융 관련 일반 단어
            "performance", "data", "information", "details",
            "please", "thanks", "thank", "hello", "hi", "hey",
            "about", "regarding", "concerning", "related",
            "sentiment", "news", "latest", "recent", "current",
            "compare", "comparison", "vs", "versus", "against",
            "price", "prices", "pricing", "cost", "value", "worth",
            "market", "markets", "trading", "trade", "investment",
            "financial", "finance", "money", "cash", "profit", "loss",
            "buy", "sell", "hold", "purchase", "acquire",
            "good", "bad", "best", "worst", "better", "worse",
            "high", "low", "higher", "lower", "increase", "decrease",
            
            # 시간 관련
            "today", "yesterday", "tomorrow", "now", "currently",
            "this", "that", "these", "those", "last", "next", "first",
            "year", "month", "week", "day", "time", "period",
            
            # 부사/형용사
            "very", "really", "quite", "pretty", "rather", "too", "so",
            "more", "most", "less", "least", "much", "many", "few", "little",
            "some", "any", "all", "every", "each", "both", "either", "neither",
            "other", "another", "same", "different", "new", "old", "own",
            
            # 한글 stop words
            "주식", "종목", "기업", "회사", "주가", "시세", "가격",
            "분석", "예측", "전망", "보고서", "연구",
            "보여줘", "알려줘", "가르쳐줘", "찾아줘",
            "어떻게", "뭔가", "누가", "언제", "어디", "왜", "어느",
            "이것", "그것", "저것", "여기", "저기", "거기",
            "좋은", "나쁜", "최고", "최악", "더", "덜",
            "높은", "낮은", "상승", "하락", "오른", "떨어진",
            "오늘", "어제", "내일", "지금", "현재", "최근",
            "이번", "지난", "다음", "올해", "작년", "내년"
        }
        
        return f"\\b({'|'.join(sorted(stop_words_list))})\\b"
        
    def _build_alias_mapping(self) -> Dict[str, str]:
        """동의어/별명 매핑 생성"""
        return {
            # 한국 주식 동의어
            "삼성": "삼성전자",
            "삼성전자주식": "삼성전자",
            "SAMSUNG": "삼성전자",
            "sk하이닉스": "SK하이닉스",
            "에스케이하이닉스": "SK하이닉스",
            "하이닉스": "SK하이닉스",
            "SK메모리": "SK하이닉스",
            "네이버주식": "네이버",
            "NAVER": "네이버",
            "카카오주식": "카카오",
            "KAKAO": "카카오",
            "카카오뱅크": "카카오",
            "현대자동차": "현대차",
            "현대모비스": "현대차",
            "기아자동차": "기아",
            
            # 미국 주식 동의어 (영어 -> 한글 정규화)
            "apple": "Apple",
            "APPLE": "Apple",
            "애플주식": "Apple",
            "microsoft": "Microsoft",
            "MICROSOFT": "Microsoft", 
            "마이크로소프트주식": "Microsoft",
            "마이크로소프트회사": "Microsoft",
            "google": "Google",
            "GOOGLE": "Google",
            "구글주식": "Google",
            "구글회사": "Google",
            "amazon": "Amazon",
            "AMAZON": "Amazon",
            "아마존주식": "Amazon",
            "아마존닷컴": "Amazon",
            "tesla": "Tesla",
            "TESLA": "Tesla",
            "테슬라주식": "Tesla",
            "테슬라모터스": "Tesla",
            "netflix": "Netflix",
            "NETFLIX": "Netflix",
            "넷플릭스주식": "Netflix",
            "meta": "META",
            "META": "META",
            "facebook": "META",
            "Facebook": "META",
            "FACEBOOK": "META",
            "페이스북주식": "META",
            "메타주식": "META",
            "nvidia": "Nvidia",
            "NVIDIA": "Nvidia",
            "엔비디아주식": "Nvidia",
            
            # 티커 -> 회사명 매핑
            "AAPL": "Apple",
            "MSFT": "Microsoft",
            "GOOGL": "Google",
            "GOOG": "Google", 
            "AMZN": "Amazon",
            "TSLA": "Tesla",
            "NFLX": "Netflix",
            "NVDA": "Nvidia",
            "AMD": "AMD",
            "INTC": "Intel",
            "JPM": "JPMorgan",
            "BAC": "Bank of America",
            "WFC": "Wells Fargo",
            "GS": "Goldman Sachs",
            "JNJ": "Johnson & Johnson",
            "PFE": "Pfizer",
            "KO": "Coca Cola",
            "WMT": "Walmart",
            "HD": "Home Depot",
            "MCD": "McDonald's",
            "SBUX": "Starbucks",
            "DIS": "Disney",
            "SPOT": "Spotify",
            "UBER": "Uber",
            "COIN": "Coinbase",
            "SQ": "Square",
            "PYPL": "PayPal",
            "BABA": "Alibaba",
            
            # 특별 별명
            "도지코인": "Dogecoin",
            "비트코인": "Bitcoin",
            "이더리움": "Ethereum",
            "공기업": "Boeing",
            "보잉항공": "Boeing",
            "맥도날드": "McDonald's",
            "스타벅스커피": "Starbucks",
            "코카콜라": "Coca Cola",
            "코카콜라회사": "Coca Cola",
            "월마트": "Walmart",
            "월마트마트": "Walmart",
            "넷플릭스": "Netflix",
            "스포티파이": "Spotify",
            "우버": "Uber",
            "코인베이스": "Coinbase",
            "페이팔": "PayPal",
            "알리바바": "Alibaba",
            "디즈니": "Disney",
            "화이자": "Pfizer",
            "존슨앤존슨": "Johnson & Johnson",
            "인텔": "Intel",
            "골드만삭스": "Goldman Sachs",
            
            # 상용 표현
            "주가": "주식",
            "시가총액": "market cap",
            "감정분석": "sentiment",
            "주가분석": "stock analysis",
            "전망": "outlook",
            "수익률": "return",
            "매출": "revenue",
            "영업이익": "operating income"
        }
        
    def _normalize_entities(self, entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """동의어/별명을 정규화"""
        alias_map = self._build_alias_mapping()
        normalized_entities = {}
        
        for entity_type, entity_list in entities.items():
            if entity_type == "stocks":
                normalized_stocks = []
                seen = set()
                
                for stock in entity_list:
                    # 별명 매핑 적용
                    normalized = alias_map.get(stock, stock)
                    normalized_upper = normalized.upper()
                    
                    # 중복 제거
                    if normalized_upper not in seen:
                        seen.add(normalized_upper)
                        normalized_stocks.append(normalized)
                
                normalized_entities[entity_type] = normalized_stocks
            else:
                # 다른 엔티티 타입도 정규화
                normalized_list = []
                for entity in entity_list:
                    normalized = alias_map.get(entity, entity)
                    normalized_list.append(normalized)
                normalized_entities[entity_type] = normalized_list
        
        return normalized_entities
        
    def analyze_query(self, query: str) -> Dict:
        """쿼리 분석 메인 함수"""
        # 1. 의도 분류
        intent = self._classify_intent(query)
        
        # 2. 엔티티 추출
        entities = self._extract_entities(query)
        
        # 3. 동의어/별명 정규화
        entities = self._normalize_entities(entities)
        
        # 4. 기간 파싱
        period_info = self._parse_period(entities.get("period"))
        
        # 5. 언어 감지
        language = self._detect_language(query)
        
        # 6. 정규화된 쿼리 생성
        normalized_query = self._normalize_query(query)
        
        return {
            "original_query": query,
            "normalized_query": normalized_query,
            "intent": intent,
            "entities": entities,
            "period": period_info,
            "language": language,
            "confidence": self._calculate_confidence(intent, entities, query)
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
        
        # Stop words 먼저 추출
        stop_words = set()
        if "stop_words" in self.entity_patterns:
            stop_matches = re.findall(self.entity_patterns["stop_words"], query, re.IGNORECASE)
            stop_words = set([word.lower() for word in stop_matches])
        
        for entity_type, pattern in self.entity_patterns.items():
            if entity_type == "stop_words":  # stop words는 별도 처리
                continue
                
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                # Stop words 필터링
                filtered_matches = []
                for match in matches:
                    if isinstance(match, tuple):  # 그룹이 있는 경우
                        match = [m for m in match if m][0]  # 빈 문자열이 아닌 첫 번째 그룹
                    if match.lower() not in stop_words and len(match.strip()) > 1:
                        filtered_matches.append(match)
                
                if filtered_matches:
                    entities[entity_type] = list(set(filtered_matches))
                
        # 주식명 통합 및 정제
        stocks = []
        if "korean_stocks" in entities:
            stocks.extend(entities["korean_stocks"])
        if "us_stocks" in entities:
            # US stocks에서 stop words 및 일반 단어 추가 필터링
            us_stocks_filtered = []
            for stock in entities["us_stocks"]:
                if stock.lower() not in stop_words and not re.match(r'^(stock|analysis|data|performance|news)$', stock.lower()):
                    us_stocks_filtered.append(stock)
            stocks.extend(us_stocks_filtered)
        if "ticker" in entities:
            # 티커는 이미 화이트리스트 방식으로 정제됨
            stocks.extend(entities["ticker"])
        if "unknown_korean_stock" in entities:
            # 알려지지 않은 한국 종목 추가
            stocks.extend(entities["unknown_korean_stock"])
        if "index_etf" in entities:
            # 인덱스/ETF 추가
            stocks.extend(entities["index_etf"])
        if "crypto" in entities:
            # 암호화폐 추가
            stocks.extend(entities["crypto"])
            
        if stocks:
            # 중복 제거 및 최종 정제
            unique_stocks = []
            seen = set()
            for stock in stocks:
                stock_clean = stock.strip()
                stock_upper = stock_clean.upper()
                if (stock_upper not in seen and 
                    len(stock_clean) > 1 and 
                    stock_clean.lower() not in stop_words and
                    not re.match(r'^(STOCK|ANALYSIS|DATA|PERFORMANCE|NEWS|SENTIMENT)$', stock_upper)):
                    seen.add(stock_upper)
                    unique_stocks.append(stock_clean)
            entities["stocks"] = unique_stocks
            
        return entities
        
    def _parse_period(self, period_str: Optional[List[str]]) -> Dict[str, str]:
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
                # "지난주", "이번주", "3주" 등 처리
                if "이번" in period:
                    # 이번 주 시작 (월요일)
                    start_date = end_date - timedelta(days=end_date.weekday())
                elif "지난" in period:
                    # 지난주 전체
                    start_date = end_date - timedelta(days=end_date.weekday() + 7)
                    end_date = start_date + timedelta(days=6)
                else:
                    # N주
                    weeks = 1
                    week_match = re.findall(r"(\d+)주", period)
                    if week_match:
                        weeks = int(week_match[0])
                    start_date = end_date - timedelta(weeks=weeks)
            elif "개월" in period or "달" in period:
                months = 1
                if "이번" in period:
                    # 이번달 1일부터
                    start_date = end_date.replace(day=1)
                elif "지난" in period:
                    # 지난달 전체
                    if end_date.month == 1:
                        start_date = end_date.replace(year=end_date.year-1, month=12, day=1)
                    else:
                        start_date = end_date.replace(month=end_date.month-1, day=1)
                    end_date = start_date.replace(day=28)  # 간단히 28일로
                else:
                    # N개월
                    month_match = re.findall(r"(\d+)개월", period)
                    if month_match:
                        months = int(month_match[0])
                    start_date = end_date - timedelta(days=30*months)
            elif "년" in period:
                years = 1
                year_match = re.findall(r"(\d+)년", period)
                if year_match:
                    years = int(year_match[0])
                start_date = end_date - timedelta(days=365*years)
            else:
                # 기본값
                start_date = end_date - timedelta(days=30)
                
        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "period_days": (end_date - start_date).days + 1
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
        
    def _calculate_confidence(self, intent: str, entities: Dict, query: str = "") -> float:
        """고도화된 신뢰도 계산 알고리즘"""
        confidence = 0.3  # 기본 신뢰도 낮춤
        
        # 1. 의도 분류 정확도 (0.0 ~ 0.4)
        intent_confidence = self._get_intent_confidence(intent, query)
        confidence += intent_confidence
        
        # 2. 엔티티 추출 품질 (0.0 ~ 0.4)
        entity_confidence = self._get_entity_confidence(entities, query)
        confidence += entity_confidence
        
        # 3. 쿼리 전체적 일관성 (0.0 ~ 0.2)
        consistency_bonus = self._get_consistency_bonus(intent, entities, query)
        confidence += consistency_bonus
        
        return min(max(confidence, 0.0), 1.0)  # 0.0 ~ 1.0 범위
        
    def _get_intent_confidence(self, intent: str, query: str) -> float:
        """의도 분류의 신뢰도 계산"""
        query_lower = query.lower()
        
        # 명확한 키워드가 있는 경우
        intent_keywords = {
            "analyze_stock": ["분석", "analyze", "알려줘", "보여줘", "tell", "show"],
            "compare_stocks": ["비교", "compare", "vs", "versus", "차이"],
            "get_sentiment": ["감성", "sentiment", "버즈", "여론", "분위기"],
            "get_news": ["뉴스", "news", "소식", "최신", "latest", "공시"],
            "get_financials": ["재무", "financial", "실적", "매출", "revenue", "이익"]
        }
        
        if intent in intent_keywords:
            matched_keywords = sum(1 for keyword in intent_keywords[intent] if keyword in query_lower)
            if matched_keywords > 0:
                return 0.3 + (matched_keywords - 1) * 0.05  # 최대 0.4
        
        # 기본 의도 (analyze_stock)인 경우 낮은 점수
        return 0.1 if intent == "analyze_stock" else 0.2
        
    def _get_entity_confidence(self, entities: Dict, query: str) -> float:
        """엔티티 추출의 신뢰도 계산"""
        entity_score = 0.0
        
        # 주식명 추출 품질
        if "stocks" in entities and entities["stocks"]:
            stocks = entities["stocks"]
            stock_count = len(stocks)
            
            # 주식 개수에 따른 기본 점수
            if stock_count == 1:
                entity_score += 0.25  # 단일 주식 - 높은 신뢰도
            elif stock_count == 2:
                entity_score += 0.3   # 비교 분석 - 예상됨
            else:
                entity_score += 0.15  # 3개 이상 - 소음 떨어짐
            
            # 주식명 타입별 추가 점수
            for stock in stocks:
                if self._is_well_known_stock(stock):
                    entity_score += 0.05  # 유명 주식 보너스
                if self._is_ticker_format(stock):
                    entity_score += 0.03  # 티커 형식 보너스
        else:
            # 주식명이 없으면 신뢰도 매우 낮음
            entity_score -= 0.2
        
        # 기간 정보 보너스
        if "period" in entities:
            entity_score += 0.05
            
        # ETF/인덱스 보너스
        if "index_etf" in entities:
            entity_score += 0.08
            
        # 암호화폐 보너스
        if "crypto" in entities:
            entity_score += 0.06
            
        return min(entity_score, 0.4)  # 최대 0.4
        
    def _get_consistency_bonus(self, intent: str, entities: Dict, query: str) -> float:
        """쿼리 전체의 일관성 보너스"""
        bonus = 0.0
        
        # 비교 의도 + 2개 주식
        if intent == "compare_stocks" and "stocks" in entities and len(entities["stocks"]) == 2:
            bonus += 0.1
            
        # 감성 분석 의도 + 감성 관련 키워드
        if intent == "get_sentiment" and any(word in query.lower() for word in ["감성", "sentiment", "분위기"]):
            bonus += 0.08
            
        # 뉴스 의도 + 뉴스 관련 키워드
        if intent == "get_news" and any(word in query.lower() for word in ["뉴스", "news", "최신", "latest"]):
            bonus += 0.08
            
        # 질문 형식의 자연스러움
        if any(word in query for word in ["?", "어떻게", "어떨", "how", "what"]):
            bonus += 0.05
            
        # 정중한 말투 (예의)
        if any(word in query.lower() for word in ["부탁", "please", "주세요", "알려주세요"]):
            bonus += 0.03
            
        return min(bonus, 0.2)  # 최대 0.2
        
    def _is_well_known_stock(self, stock: str) -> bool:
        """유명 주식 여부 판단"""
        well_known = {
            # 한국
            "삼성전자", "SK하이닉스", "네이버", "카카오", "현대차",
            # 미국
            "Apple", "Microsoft", "Google", "Amazon", "Tesla", "Netflix", "Meta",
            "Nvidia", "AMD", "Intel", "Disney", "Coca Cola", "McDonald's"
        }
        return stock in well_known
        
    def _is_ticker_format(self, stock: str) -> bool:
        """티커 형식 여부 판단"""
        return len(stock) <= 5 and stock.isupper() and stock.isalpha()


# 테스트 함수
def test_simple_nlu():
    nlu = SimpleNLUAgent()
    
    test_queries = [
        "삼성전자 최근 실적 어때?",
        "애플이랑 마이크로소프트 비교해줘",
        "테슬라 요즘 분위기 어때?",
        "NVDA 지난 3개월 재무제표 보여줘",
        "카카오 최근 뉴스 알려줘",
        "LG에너지솔루션 이번주 주가 분석해줘",
        "Tell me about Google's sentiment",
        "최근 한달간 현대차 공시 내용 정리해줘",
        "포스코랑 현대차 뭐가 더 좋아?",
        "엔비디아 작년 실적 보여줘"
    ]
    
    print("=== StockAI Simple NLU Agent 테스트 ===\n")
    
    for query in test_queries:
        result = nlu.analyze_query(query)
        
        print(f"입력: {query}")
        print(f"의도: {result['intent']}")
        print(f"추출된 주식: {result['entities'].get('stocks', [])}")
        print(f"기간: {result['period']['start_date']} ~ {result['period']['end_date']} ({result['period']['period_days']}일)")
        print(f"언어: {result['language']}")
        print(f"신뢰도: {result['confidence']:.2f}")
        print("-" * 60)
        print()
        

if __name__ == "__main__":
    test_simple_nlu()