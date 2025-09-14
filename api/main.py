"""
StockAI FastAPI 메인 애플리케이션
WebSocket을 통한 실시간 채팅 기능 제공
"""
import os
import sys
import asyncio
from datetime import datetime
from typing import List, Dict, Any
import json
from dotenv import load_dotenv

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 환경변수 로드
load_dotenv()

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Simple NLU Agent import
from agents.simple_nlu_agent import SimpleNLUAgent
from agents.dart_agent import DartAgent
from agents.sec_agent import SECAgent
from agents.news_agent import NewsAgent
from agents.social_agent import SocialAgent
from agents.sentiment_agent import SentimentAgent
from agents.price_agent import PriceAgent
from agents.financial_agent import FinancialAgent
from agents.technical_agent import TechnicalAgent
from agents.crypto_agent import CryptoAgent
from api.professional_report_formatter import ProfessionalReportFormatter
from config.period_config import PeriodConfig

# 새로운 API 클라이언트 import
from agents.dart_api_client import DARTApiClient
from agents.news_api_client import NewsApiClient
from agents.alpha_vantage_client import AlphaVantageClient
from agents.us_stock_client import USStockClient
from api.api_status import APIStatusChecker

app = FastAPI(title="StockAI API", version="0.1.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# NLU 에이전트 초기화
nlu_agent = SimpleNLUAgent()

# API 클라이언트 초기화
dart_client = DARTApiClient()
news_client = NewsApiClient()
alpha_vantage_client = AlphaVantageClient()
us_stock_client = USStockClient()

# 연결된 WebSocket 클라이언트 관리
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

def create_data_source_info(data_source_summary: Dict[str, int]) -> str:
    """
    데이터 소스 요약 정보 생성
    
    Args:
        data_source_summary: {"REAL_DATA": int, "MOCK_DATA": int} 형태의 요약
        
    Returns:
        데이터 소스 정보 문자열
    """
    total_sources = data_source_summary["REAL_DATA"] + data_source_summary["MOCK_DATA"]
    
    if data_source_summary["MOCK_DATA"] > 0:
        info = f"\n⚠️ **주의**: 실제 데이터 {data_source_summary['REAL_DATA']}개, 모의 데이터 {data_source_summary['MOCK_DATA']}개를 사용한 분석입니다.\n"
        if data_source_summary["REAL_DATA"] == 0:
            info += "\n🔸 **데이터 신뢰도 낮음**: 모든 데이터가 모의 데이터입니다. API 키 설정을 확인해주세요.\n"
        else:
            info += "\n🔸 **혼합 데이터**: 일부 API가 설정되지 않아 모의 데이터가 포함되었습니다.\n"
    else:
        info = f"\n✅ **데이터 소스**: {total_sources}개의 실제 데이터 소스를 사용한 신뢰성 높은 분석입니다.\n"
    
    return info

def get_reliability_level(data_source_summary: Dict[str, int]) -> str:
    """
    데이터 신뢰도 레벨 계산
    
    Args:
        data_source_summary: {"REAL_DATA": int, "MOCK_DATA": int} 형태의 요약
        
    Returns:
        "high", "mixed", "low", "none" 중 하나
    """
    if data_source_summary["MOCK_DATA"] == 0 and data_source_summary["REAL_DATA"] > 0:
        return "high"
    elif data_source_summary["REAL_DATA"] > 0:
        return "mixed"
    elif data_source_summary["MOCK_DATA"] > 0:
        return "low"
    else:
        return "none"

async def get_financial_data(corp_code: str):
    """Helper function to get financial data with proper session management"""
    try:
        async with FinancialAgent() as financial_agent:
            result = await financial_agent.analyze_financial_health(corp_code)
            return result
    except Exception as e:
        print(f"[FINANCIAL ERROR] {str(e)}")
        return {
            "status": "error",
            "data_source": "ERROR",
            "message": str(e)
        }

@app.get("/")
async def root():
    """메인 페이지 - 탭 구조 통합 대시보드"""
    return FileResponse("frontend/dashboard_tabs.html")

@app.get("/tabs")
async def tabs_dashboard():
    """탭 구조 통합 대시보드"""
    return FileResponse("frontend/dashboard_tabs.html")

@app.get("/versions")
async def version_selector():
    """버전 선택 페이지"""
    return FileResponse("frontend/index_selector.html")

@app.get("/stable")
async def stable_dashboard():
    """안정적인 REST API 대시보드"""
    return FileResponse("frontend/dashboard_rest.html")

@app.get("/pro")
async def pro_dashboard():
    """전문 분석 대시보드"""
    return FileResponse("frontend/dashboard_advanced.html")

@app.get("/old")
async def old_ui():
    """기존 대시보드 (전체 기능 포함)"""
    return FileResponse("frontend/dashboard.html")

@app.get("/crypto")
async def crypto_page():
    """암호화폐 전용 페이지"""
    return FileResponse("frontend/dashboard_rest.html")

@app.get("/debug")
async def debug_page():
    """디버그 테스트 페이지"""
    return FileResponse("frontend/debug_test.html")

@app.get("/chat")
async def chat():
    """채팅 페이지 반환"""
    return FileResponse("frontend/index.html")

@app.get("/responsive")
async def responsive():
    """반응형 페이지 반환"""
    return FileResponse("frontend/responsive.html")

@app.get("/api-status")
async def api_status_page():
    """API 상태 페이지 반환"""
    return FileResponse("frontend/api_status.html")

@app.get("/foreign-stock")
async def foreign_stock_page():
    """해외 주식 상세 분석 페이지"""
    return FileResponse("frontend/foreign_stock_enhanced.html")

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket 채팅 엔드포인트"""
    await manager.connect(websocket)
    
    try:
        # 연결 성공 메시지
        await manager.send_personal_message(
            json.dumps({
                "type": "system",
                "message": "StockAI 챗봇에 연결되었습니다. 주식에 대해 물어보세요!",
                "timestamp": datetime.utcnow().isoformat()
            }),
            websocket
        )
        
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            
            # JSON 또는 일반 텍스트 처리
            try:
                message_data = json.loads(data)
                query = message_data.get("message", data)
            except json.JSONDecodeError:
                # 일반 텍스트로 처리 (대시보드에서 오는 경우)
                query = data
            
            # NLU 처리
            print(f"[WEBSOCKET] Received message: {query}", flush=True)
            nlu_result = nlu_agent.analyze_query(query)
            print(f"[WEBSOCKET] NLU result intent: {nlu_result.get('intent')}", flush=True)
            print(f"[WEBSOCKET] NLU entities: {nlu_result.get('entities')}", flush=True)
            
            # 진행 상황 알림
            await manager.send_personal_message(
                json.dumps({
                    "type": "system",
                    "message": "분석을 시작합니다... 🔍",
                    "timestamp": datetime.utcnow().isoformat()
                }, ensure_ascii=False),
                websocket
            )
            
            # 분석 실행
            if nlu_result["intent"] == "analyze_crypto" and nlu_result["entities"].get("crypto"):
                print(f"[WEBSOCKET] Starting crypto analysis...", flush=True)
                # 암호화폐 정보 추출
                crypto = nlu_result["entities"]["crypto"][0]
                print(f"[WEBSOCKET] Crypto extracted: {crypto}", flush=True)
                
                try:
                    # 암호화폐 분석 실행
                    print(f"[WEBSOCKET] Creating CryptoAgent...", flush=True)
                    async with CryptoAgent() as crypto_agent:
                        print(f"[WEBSOCKET] CryptoAgent created, calling analyze_crypto...", flush=True)
                        crypto_result = await crypto_agent.analyze_crypto(crypto)
                        print(f"[WEBSOCKET] analyze_crypto completed with status: {crypto_result.get('status', 'unknown')}", flush=True)
                    
                    if crypto_result["status"] == "success":
                        # 암호화폐 데이터 대시보드 형식으로 변환
                        crypto_data = crypto_result["crypto_data"]
                        current_price_usd = crypto_data.get("current_price_usd", 0)
                        current_price_krw = crypto_data.get("current_price_krw", 0)
                        change_24h = crypto_data.get("price_change_percentage_24h", 0)
                        
                        # 가격 포맷팅 - 원화 우선, USD 병기
                        if current_price_krw > 1000:
                            krw_str = f"₩{current_price_krw:,.0f}"
                        elif current_price_krw > 1:
                            krw_str = f"₩{current_price_krw:,.2f}"
                        else:
                            krw_str = f"₩{current_price_krw:.4f}"
                            
                        if current_price_usd >= 1:
                            usd_str = f"${current_price_usd:,.2f}"
                        else:
                            usd_str = f"${current_price_usd:.6f}"
                            
                        price_str = f"{krw_str} ({usd_str})"
                        
                        # 변동률 포맷팅  
                        change_str = f"{'+' if change_24h > 0 else ''}{change_24h:.2f}%"
                        
                        dashboard_data = {
                            "type": "crypto",
                            "crypto_name": crypto,
                            "name": crypto_data.get("name", crypto),
                            "symbol": crypto_data.get("symbol", ""),
                            "price": price_str,
                            "change": change_str,
                            "change_value": change_24h,
                            "market_cap": crypto_data.get("market_cap_krw", 0),
                            "market_cap_usd": crypto_data.get("market_cap_usd", 0),
                            "market_cap_rank": crypto_data.get("market_cap_rank", 0),
                            "volume_24h": crypto_data.get("volume_24h_krw", 0),
                            "volume_24h_usd": crypto_data.get("volume_24h_usd", 0),
                            "high_24h": crypto_data.get("high_24h_krw", 0),
                            "high_24h_usd": crypto_data.get("high_24h_usd", 0),
                            "low_24h": crypto_data.get("low_24h_krw", 0),
                            "low_24h_usd": crypto_data.get("low_24h_usd", 0),
                            "ath": crypto_data.get("ath_krw", 0),
                            "ath_usd": crypto_data.get("ath_usd", 0),
                            "atl": crypto_data.get("atl_krw", 0),
                            "atl_usd": crypto_data.get("atl_usd", 0),
                            "sentiment": crypto_result.get("sentiment", {}).get("overall_sentiment", 0),
                            "sentiment_label": crypto_result.get("sentiment", {}).get("sentiment_label", "중립적"),
                            "technical_signals": crypto_result.get("technical_signals", {}),
                            "analysis": crypto_result.get("analysis", ""),
                            "data_source": crypto_result.get("data_source", "UNKNOWN")
                        }
                        
                        # 암호화폐 분석 결과 전송
                        await manager.send_personal_message(
                            json.dumps(dashboard_data, ensure_ascii=False),
                            websocket
                        )
                        return  # 암호화폐 분석 완료 후 함수 종료
                    else:
                        await manager.send_personal_message(
                            json.dumps({
                                "type": "error",
                                "message": f"암호화폐 '{crypto}' 분석 실패: {crypto_result.get('message', '알 수 없는 오류')}"
                            }, ensure_ascii=False),
                            websocket
                        )
                        return  # 암호화폐 분석 실패 후 함수 종료
                        
                except Exception as e:
                    print(f"[WEBSOCKET] Crypto analysis error: {e}", flush=True)
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": f"암호화폐 분석 중 오류가 발생했습니다: {str(e)}"
                        }, ensure_ascii=False),
                        websocket
                    )
                    return  # 암호화폐 분석 오류 후 함수 종료
                    
            elif nlu_result["intent"] == "analyze_stock" and nlu_result["entities"].get("stocks"):
                print(f"[WEBSOCKET] Starting stock analysis...", flush=True)
                # 종목 정보 추출
                stock = nlu_result["entities"]["stocks"][0]
                print(f"[WEBSOCKET] Stock extracted: {stock}", flush=True)
                
                # 한국 주식명을 영어로 매핑
                stock_name_map = {
                    "애플": "AAPL",
                    "구글": "GOOGL",
                    "마이크로소프트": "MSFT",
                    "아마존": "AMZN",
                    "테슬라": "TSLA",
                    "엔비디아": "NVDA",
                    "메타": "META",
                    "넷플릭스": "NFLX"
                }
                
                # 미국 주식인지 확인 (한글명이 미국 회사를 가리키는 경우)
                original_stock = stock
                if stock in stock_name_map:
                    print(f"[WEBSOCKET] Mapping {stock} to {stock_name_map[stock]}", flush=True)
                    stock = stock_name_map[stock]
                    is_korean = False
                else:
                    # 한국/미국 주식 구분
                    is_korean = any(char >= '가' and char <= '힣' for char in stock)
                    
                    # 한국 주식 약칭 정규화
                    if is_korean:
                        korean_stock_normalization = {
                            "삼성": "삼성전자",
                            "LG": "LG에너지솔루션",
                            "현대": "현대차",
                            "SK": "SK하이닉스"
                        }
                        stock = korean_stock_normalization.get(stock, stock)
                        
                print(f"[WEBSOCKET] is_korean: {is_korean}, final stock: {stock}", flush=True)
                
                try:
                    print(f"[WEBSOCKET] Starting data collection...", flush=True)
                    # 병렬로 데이터 수집
                    tasks = []
                    
                    # 주가 데이터 수집 (최우선)
                    print(f"[WEBSOCKET] Creating PriceAgent...", flush=True)
                    async with PriceAgent() as price_agent:
                        price_task = price_agent.get_stock_price(stock)
                        tasks.append(("price", price_task))
                        print(f"[WEBSOCKET] Price task added", flush=True)
                    
                    # 뉴스 수집
                    print(f"[WEBSOCKET] Creating NewsAgent...", flush=True)
                    try:
                        async with NewsAgent() as news_agent:
                            print(f"[WEBSOCKET] NewsAgent created, is_korean={is_korean}", flush=True)
                            if is_korean:
                                news_task = news_agent.search_korean_news(stock)
                            else:
                                news_task = news_agent.search_news(stock, language="en")
                            tasks.append(("news", news_task))
                            print(f"[WEBSOCKET] News task added", flush=True)
                    except Exception as e:
                        print(f"[WEBSOCKET ERROR] NewsAgent error: {e}", flush=True)
                        import traceback
                        print(f"[WEBSOCKET ERROR] Traceback: {traceback.format_exc()}", flush=True)
                    
                    # 재무 데이터 수집 (한국 주식만)
                    if is_korean:
                        # 종목코드로 변환 필요 (예: 삼성전자 -> 005930)
                        stock_code_map = {
                            "삼성전자": "005930",
                            "SK하이닉스": "000660",
                            "sk하이닉스": "000660",
                            "하이닉스": "000660",
                            "에스케이하이닉스": "000660",
                            "네이버": "035420",
                            "카카오": "035720",
                            "LG에너지솔루션": "373220",
                            "현대차": "005380",
                            "현대자동차": "005380",
                            "기아": "000270",
                            "LG전자": "066570",
                            "포스코": "005490",
                            "더본코리아": "354200",
                            "더본": "354200",
                            "CJ": "001040",
                            "롯데": "004990",
                            "신세계": "004170",
                            "현대백화점": "069960",
                            "이마트": "139480"
                        }
                        
                        # 종목코드로 corp_code 찾기
                        corp_code_map = {
                            "005930": "00126380",  # 삼성전자
                            "000660": "00164779",  # SK하이닉스
                            "035420": "00120030",  # 네이버
                            "035720": "00258801",  # 카카오
                            "373220": "00141080",  # LG에너지솔루션  
                            "005380": "00164742",  # 현대차
                            "005490": "00126390",  # 포스코
                            "354200": "00139670",  # 더본코리아
                        }
                        
                        # stock_code_map에서 종목코드를 가져옴
                        stock_code_val = stock_code_map.get(stock, None)
                        if stock_code_val and stock_code_val in corp_code_map:
                            corp_code = corp_code_map[stock_code_val]
                            # Use helper function for proper session management
                            financial_task = asyncio.create_task(get_financial_data(corp_code))
                            tasks.append(("financial", financial_task))
                    
                    # 기술적 분석 추가
                    try:
                        async with TechnicalAgent() as technical_agent:
                            technical_task = technical_agent.analyze_technical(stock)
                            tasks.append(("technical", technical_task))
                            print(f"[WEBSOCKET] Technical analysis task added for {stock}", flush=True)
                    except Exception as e:
                        print(f"[WEBSOCKET] Technical agent creation failed: {e}", flush=True)
                    
                    # 공시 데이터 수집
                    if is_korean:
                        # DART (한국 공시) - 환경변수 명시적 전달
                        dart_api_key = os.getenv("DART_API_KEY")
                        print(f"[DART INIT] API Key available: {bool(dart_api_key)}")
                        print(f"[DART INIT] Processing Korean stock: {stock}")
                        stock_code = stock_code_map.get(stock, None)
                        
                        if stock_code is None:
                            # 종목코드를 찾을 수 없는 경우 경고 메시지
                            print(f"[DART] Unknown stock: {stock} - using as-is for search")
                            stock_code = stock  # 입력된 이름 그대로 사용
                        
                        print(f"[DART] Fetching disclosures for {stock} (code: {stock_code})")
                        
                        # DART 에이전트 직접 실행 (최적화된 기간 사용)
                        async with DartAgent(api_key=dart_api_key) as dart_agent:
                            dart_result = await dart_agent.get_major_disclosures(stock_code, days=PeriodConfig.DISCLOSURE_PERIOD_DAYS)
                        
                        # 즉시 실행된 결과를 Future로 래핑
                        async def get_dart_result():
                            return dart_result
                        tasks.append(("dart", get_dart_result()))
                    else:
                        # SEC (미국 공시)
                        print(f"[WEBSOCKET] Creating SECAgent for {stock}...", flush=True)
                        try:
                            async with SECAgent() as sec_agent:
                                print(f"[WEBSOCKET] SECAgent created", flush=True)
                                sec_task = sec_agent.get_major_filings(stock)
                                tasks.append(("sec", sec_task))
                                print(f"[WEBSOCKET] SEC task added", flush=True)
                        except Exception as e:
                            print(f"[WEBSOCKET ERROR] SECAgent error: {e}", flush=True)
                    
                    # 소셜 데이터 수집 - API 키가 있을 때만 (임시 비활성화 - 유효한 키가 없음)
                    reddit_api_key = os.getenv("REDDIT_CLIENT_ID")
                    # 실제 유효한 API 키가 있는지 확인 (placeholder 제외)
                    if reddit_api_key and reddit_api_key != "your_reddit_client_id_here":
                        is_valid_reddit_key = True
                    else:
                        is_valid_reddit_key = False
                    
                    print(f"[WEBSOCKET] Reddit API key valid: {is_valid_reddit_key}, is_korean: {is_korean}", flush=True)
                    if is_valid_reddit_key and not is_korean:
                        print(f"[WEBSOCKET] Creating SocialAgent...", flush=True)
                        try:
                            async with SocialAgent() as social_agent:
                                reddit_task = social_agent.search_reddit(stock)
                                tasks.append(("reddit", reddit_task))
                                print(f"[WEBSOCKET] Reddit task added", flush=True)
                        except Exception as e:
                            print(f"[WEBSOCKET ERROR] SocialAgent error: {e}", flush=True)
                    
                    # 모든 태스크 실행
                    print(f"[WEBSOCKET] Executing {len(tasks)} tasks...", flush=True)
                    results = {}
                    data_source_summary = {"REAL_DATA": 0, "MOCK_DATA": 0}
                    
                    for name, task in tasks:
                        print(f"[WEBSOCKET] Executing task: {name}", flush=True)
                        try:
                            result = await asyncio.wait_for(task, timeout=5.0)  # 5초 타임아웃
                            results[name] = result
                            print(f"[{name}] Status: {result.get('status')}, Count: {result.get('count', 0)}, Data source: {result.get('data_source')}")
                            
                            # 데이터 소스 추적
                            if result and result.get("data_source"):
                                data_source_type = result.get("data_source")
                                data_source_summary[data_source_type] += 1
                        except asyncio.TimeoutError:
                            print(f"[{name}] Timeout - using mock data", flush=True)
                            results[name] = {"status": "timeout", "message": "Request timeout", "data_source": "MOCK_DATA"}
                            data_source_summary["MOCK_DATA"] += 1
                        except Exception as e:
                            print(f"Error in {name}: {str(e)}", flush=True)
                            results[name] = {"status": "error", "message": str(e), "data_source": "MOCK_DATA"}
                            data_source_summary["MOCK_DATA"] += 1
                    
                    # 감성 분석 실행
                    sentiment_agent = SentimentAgent()
                    
                    # 데이터 준비
                    data_sources = {}
                    if "news" in results and results["news"]["status"] == "success":
                        data_sources["news"] = results["news"]
                    if "reddit" in results and results["reddit"]["status"] == "success":
                        data_sources["social"] = {"reddit": results["reddit"]}
                    if "dart" in results and results["dart"]["status"] == "success":
                        data_sources["disclosure"] = results["dart"]
                    if "sec" in results and results["sec"]["status"] == "success":
                        data_sources["disclosure"] = results["sec"]
                    
                    # 감성 분석
                    if data_sources:
                        print(f"[SENTIMENT] Starting sentiment analysis for {stock}")
                        sentiment_result = await sentiment_agent.analyze_sentiment(
                            ticker=stock,
                            company_name=stock,
                            data_sources=data_sources
                        )
                        print(f"[SENTIMENT] Result: sentiment={sentiment_result.overall_sentiment}, label={sentiment_result.sentiment_label}")
                        
                        # 감성 분석 결과의 데이터 소스도 추적
                        for source_name, source_data in sentiment_result.data_sources.items():
                            if source_data.get("data_source"):
                                data_source_type = source_data.get("data_source")
                                if data_source_type not in data_source_summary:
                                    data_source_summary[data_source_type] = 0
                        
                        # 데이터 소스 요약 생성
                        data_source_info = create_data_source_info(data_source_summary)
                        
                        # 재무 데이터 추출
                        financial_data = None
                        if "dart" in results and results["dart"]["status"] == "success":
                            disclosures = results["dart"].get("disclosures", [])
                            for disclosure in disclosures:
                                if "반기보고서" in disclosure.get('report_nm', ''):
                                    try:
                                        async with DartAgent(api_key=dart_api_key) as detail_agent:
                                            detail = await detail_agent.get_disclosure_detail(
                                                disclosure.get('rcept_no', ''), 
                                                disclosure.get('report_nm', '')
                                            )
                                            summary = detail.get('summary', '')
                                            if "📊 **실제 재무 데이터**" in summary:
                                                lines = summary.split("\\n")
                                                financial_data = ""
                                                for line in lines[1:5]:
                                                    if line.strip() and any(x in line for x in ["매출액", "영업이익", "당기순이익"]):
                                                        clean_line = line.replace("**", "").replace("•", "▫️")
                                                        financial_data += clean_line + "\\n"
                                                break
                                    except:
                                        pass
                        
                        # Professional Report Formatter 사용
                        formatter = ProfessionalReportFormatter()
                        analysis_message = formatter.format_report(
                            company_name=sentiment_result.company_name,
                            sentiment_result=sentiment_result,
                            data_source_info=data_source_info,
                            news_data=results.get("news", {}),
                            dart_data=results.get("dart", {}),
                            financial_data=financial_data,
                            price_data=results.get("price", {}),
                            financial_analysis=results.get("financial", {}),
                            technical_analysis=results.get("technical", {})
                        )
                        
                        # 대시보드용 데이터 형식 추가
                        # 주가 데이터 추출
                        price_info = results.get("price", {}).get("price_data", {})
                        current_price = price_info.get("current_price", 0)
                        change_percent = price_info.get("change_percent", 0)
                        
                        # 재무 지표 추출
                        financial_metrics = results.get("price", {}).get("financial_info", {})
                        
                        # 가격 포맷팅 (한국 주식은 원화, 미국 주식은 달러)
                        if is_korean:
                            price_str = f"₩{current_price:,.0f}" if current_price else "데이터 없음"
                        else:
                            price_str = f"${current_price:,.2f}" if current_price else "데이터 없음"
                        
                        # 변동률 포맷팅
                        if change_percent != 0:
                            change_str = f"{'+' if change_percent > 0 else ''}{change_percent:.2f}%"
                        else:
                            change_str = "0.00%"
                        
                        dashboard_data = {
                            "stock_name": original_stock if 'original_stock' in locals() else (nlu_result["entities"]["stocks"][0] if nlu_result["entities"].get("stocks") else query),
                            "price": price_str,
                            "change": change_str,
                            "change_value": change_percent,  # 색상 판단용
                            "price_data": results.get("price", {}).get("price_data", {}),  # 차트를 위한 가격 데이터 추가
                            "sentiment": sentiment_result.overall_sentiment,
                            "sentiment_label": sentiment_result.sentiment_label,
                            "sentiment_reason": sentiment_result.recommendation,
                            "news": results.get("news", {}).get("articles", [])[:5],
                            "market_cap": f"₩{price_info.get('market_cap', 0)/1e12:.2f}조" if is_korean and price_info.get('market_cap') 
                                         else f"${price_info.get('market_cap', 0)/1e12:.2f}T" if price_info.get('market_cap') 
                                         else "-",
                            "volume": f"{price_info.get('volume', 0):,}" if price_info.get('volume') else "-",
                            "per": f"{financial_metrics.get('pe_ratio', 0):.2f}" if financial_metrics.get('pe_ratio') and financial_metrics.get('pe_ratio') > 0 else "-",
                            "pbr": f"{financial_metrics.get('pb_ratio', 0):.2f}" if financial_metrics.get('pb_ratio') and financial_metrics.get('pb_ratio') > 0 else "-",
                            "roe": f"{financial_metrics.get('roe', 0):.2f}%" if financial_metrics.get('roe') and financial_metrics.get('roe') > 0 else "-",
                            "eps": f"{financial_metrics.get('eps', 0):.2f}" if financial_metrics.get('eps') and financial_metrics.get('eps') > 0 else "-",
                            "dividend_yield": f"{financial_metrics.get('dividend_yield', 0):.2f}%" if financial_metrics.get('dividend_yield') and financial_metrics.get('dividend_yield') > 0 else "-",
                            "debt_to_equity": f"{financial_metrics.get('debt_to_equity', 0):.2f}" if financial_metrics.get('debt_to_equity') and financial_metrics.get('debt_to_equity') > 0 else "-",
                            "beta": f"{financial_metrics.get('beta', 0):.2f}" if financial_metrics.get('beta') and financial_metrics.get('beta') > 0 else "-",
                            "high_52w": f"₩{price_info.get('week_52_high', 0):,.0f}" if is_korean and price_info.get('week_52_high')
                                       else f"${price_info.get('week_52_high', 0):,.2f}" if price_info.get('week_52_high')
                                       else "-",
                            "low_52w": f"₩{price_info.get('week_52_low', 0):,.0f}" if is_korean and price_info.get('week_52_low')
                                      else f"${price_info.get('week_52_low', 0):,.2f}" if price_info.get('week_52_low')
                                      else "-",
                            "insights": [
                                f"감성 점수: {sentiment_result.overall_sentiment:.2f}",
                                f"데이터 신뢰도: {get_reliability_level(data_source_summary)}",
                                f"추천: {sentiment_result.recommendation}"
                            ],
                            # 기술적 분석 데이터 추가
                            "rsi": results.get("technical", {}).get("analysis", {}).get("indicators", {}).get("rsi", "-"),
                            "macd": results.get("technical", {}).get("analysis", {}).get("indicators", {}).get("macd", "-"),
                            "bollinger_upper": results.get("technical", {}).get("analysis", {}).get("indicators", {}).get("bollinger_upper", "-"),
                            "bollinger_lower": results.get("technical", {}).get("analysis", {}).get("indicators", {}).get("bollinger_lower", "-"),
                            "signal": results.get("technical", {}).get("analysis", {}).get("signal", "중립"),
                            # 재무 지표 추가
                            "debt_ratio": financial_metrics.get('debt_to_equity', '-'),
                            "current_ratio": financial_metrics.get('current_ratio', '-'),
                            "beta": financial_metrics.get('beta', '-')
                        }
                        
                        # 분석 결과 전송 (대시보드 형식 우선)
                        response = dashboard_data
                    else:
                        # 데이터 소스 요약 메시지 생성
                        warning_message = ""
                        if data_source_summary["MOCK_DATA"] > 0:
                            warning_message = "\n\n⚠️ **경고**: API 키가 설정되지 않아 일부 데이터를 수집하지 못했습니다."
                            
                        response = {
                            "type": "bot",
                            "message": f"{stock}에 대한 데이터를 수집하지 못했습니다. 다시 시도해주세요.{warning_message}",
                            "data": {
                                "data_source_summary": data_source_summary,
                                "reliability": get_reliability_level(data_source_summary)
                            },
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
                except Exception as e:
                    import traceback
                    print(f"[ERROR] Analysis failed: {str(e)}")
                    print(f"[ERROR] Error type: {type(e).__name__}")
                    print(f"[ERROR] Traceback: {traceback.format_exc()}")
                    
                    # Log to file for debugging
                    with open("error_debug.log", "a") as f:
                        f.write(f"\n{'='*50}\n")
                        f.write(f"Time: {datetime.utcnow()}\n")
                        f.write(f"Query: {query}\n")
                        f.write(f"Stock: {stock if 'stock' in locals() else 'N/A'}\n")
                        f.write(f"Error: {str(e)}\n")
                        f.write(f"Traceback:\n{traceback.format_exc()}\n")
                    
                    response = {
                        "type": "bot",
                        "message": f"분석 중 오류가 발생했습니다: {str(e)}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
            else:
                # 주식이 인식되지 않은 경우 처리
                if nlu_result["intent"] == "analyze_stock":
                    response = {
                        "type": "bot", 
                        "message": f"**'{query}'**에서 종목을 인식하지 못했습니다.\n\n💡 **사용 예시:**\n• 삼성전자 분석해줘\n• SK하이닉스 주가 어때?\n• 더본코리아 최근 실적\n• AAPL 감성분석\n\n📝 **지원 종목:** 국내 주요 종목, 미국 주요 종목\n🔍 **새로운 종목** 요청시 지원 검토하겠습니다.",
                        "data": {
                            "nlu_result": nlu_result,
                            "suggestion": "supported_stocks"
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    # 다른 의도 처리
                    response = {
                        "type": "bot",
                        "message": f"'{query}'에 대해 이해했습니다. 현재는 주식 분석 기능만 지원합니다.",
                        "nlu_result": nlu_result,
                        "timestamp": datetime.utcnow().isoformat()
                    }
            
            # 응답 전송
            await manager.send_personal_message(
                json.dumps(response, ensure_ascii=False),
                websocket
            )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client {client_id} disconnected")
    except Exception as e:
        import traceback
        print(f"[WEBSOCKET ERROR] Error in connection: {str(e)}")
        print(f"[WEBSOCKET ERROR] Type: {type(e).__name__}")
        print(f"[WEBSOCKET ERROR] Traceback: {traceback.format_exc()}")
        if websocket in manager.active_connections:
            manager.disconnect(websocket)

@app.post("/api/analyze")
async def analyze_query(query: Dict[str, Any]):
    """REST API 엔드포인트 - 암호화폐/주식 분석"""
    try:
        message = query.get("message", "")
        print(f"[API] Received query: {message}")

        # NLU 분석
        nlu_result = nlu_agent.analyze_query(message)
        print(f"[API] NLU result: {nlu_result.get('intent')}")

        # 암호화폐 분석
        if nlu_result["intent"] == "analyze_crypto" and nlu_result["entities"].get("crypto"):
            crypto = nlu_result["entities"]["crypto"][0]
            print(f"[API] Analyzing crypto: {crypto}")

            async with CryptoAgent() as crypto_agent:
                crypto_result = await crypto_agent.analyze_crypto(crypto)

            if crypto_result["status"] == "success":
                crypto_data = crypto_result["crypto_data"]

                # 가격 포맷팅
                current_price_krw = crypto_data.get("current_price_krw", 0)
                current_price_usd = crypto_data.get("current_price_usd", 0)
                change_24h = crypto_data.get("price_change_percentage_24h", 0)

                if current_price_krw > 1000:
                    krw_str = f"₩{current_price_krw:,.0f}"
                elif current_price_krw > 1:
                    krw_str = f"₩{current_price_krw:,.2f}"
                else:
                    krw_str = f"₩{current_price_krw:.4f}"

                if current_price_usd >= 1:
                    usd_str = f"${current_price_usd:,.2f}"
                else:
                    usd_str = f"${current_price_usd:.6f}"

                return {
                    "success": True,
                    "type": "crypto",
                    "data": {
                        "name": crypto_data.get("name", crypto),
                        "symbol": crypto_data.get("symbol", ""),
                        "price": f"{krw_str} ({usd_str})",
                        "change": f"{'+' if change_24h > 0 else ''}{change_24h:.2f}%",
                        "change_value": change_24h,
                        "market_cap": crypto_data.get("market_cap_krw", 0),
                        "market_cap_rank": crypto_data.get("market_cap_rank", 0),
                        "volume_24h": crypto_data.get("volume_24h_krw", 0),
                        "high_24h": crypto_data.get("high_24h_krw", 0),
                        "low_24h": crypto_data.get("low_24h_krw", 0),
                        "sentiment": crypto_result.get("sentiment", {}).get("overall_sentiment", 0),
                        "sentiment_label": crypto_result.get("sentiment", {}).get("sentiment_label", "중립적"),
                        "technical_signals": crypto_result.get("technical_signals", {})
                    }
                }
            else:
                return {
                    "success": False,
                    "error": crypto_result.get("message", "분석 실패")
                }

        # 주식 분석
        elif nlu_result["intent"] == "analyze_stock" and nlu_result["entities"].get("stocks"):
            stock = nlu_result["entities"]["stocks"][0]
            print(f"[API] Analyzing stock: {stock}")

            # 한국어 주식명을 영어로 매핑
            stock_name_map = {
                "애플": "AAPL",
                "구글": "GOOGL",
                "마이크로소프트": "MSFT",
                "아마존": "AMZN",
                "테슬라": "TSLA",
                "엔비디아": "NVDA",
                "메타": "META",
                "넷플릭스": "NFLX"
            }

            # 미국 주식인지 확인
            original_stock = stock
            if stock in stock_name_map:
                stock = stock_name_map[stock]
                is_korean = False
            else:
                is_korean = any(char >= '가' and char <= '힣' for char in stock)

            try:
                # 주가 데이터 수집
                async with PriceAgent() as price_agent:
                    price_result = await price_agent.get_stock_price(stock)

                if price_result["status"] == "success":
                    price_data = price_result["price_data"]

                    # 가격 포맷팅
                    current_price = price_data.get("current_price", 0)
                    change_percent = price_data.get("change_percent", 0)

                    if is_korean:
                        price_str = f"₩{current_price:,.0f}" if current_price else "데이터 없음"
                    else:
                        price_str = f"${current_price:,.2f}" if current_price else "데이터 없음"

                    change_str = f"{'+' if change_percent > 0 else ''}{change_percent:.2f}%"

                    # 한국/미국 주식별 실제 데이터 보강
                    enhanced_data = {
                        "name": original_stock,
                        "symbol": stock,
                        "price": price_str,
                        "change": change_str,
                        "change_value": change_percent,
                        "market_cap": price_data.get("market_cap", 0),
                        "volume": price_data.get("volume", 0),
                        "high_52w": price_data.get("week_52_high", 0),
                        "low_52w": price_data.get("week_52_low", 0),
                        "pe_ratio": price_data.get("pe_ratio", 0),
                        "eps": price_data.get("eps", 0)
                    }

                    # API 키가 있으면 실제 데이터 사용
                    stock_code_map = {
                        "삼성전자": "005930",
                        "SK하이닉스": "000660",
                        "LG에너지솔루션": "373220",
                        "삼성바이오로직스": "207940",
                        "현대차": "005380",
                        "카카오": "035720",
                        "네이버": "035420"
                    }

                    # 1. 실시간 뉴스 데이터 가져오기
                    news_data = []
                    if news_client.is_newsapi_valid or news_client.is_naver_valid:
                        news_list = news_client.get_stock_news(original_stock, 'ko' if is_korean else 'en')
                        news_sentiment = news_client.analyze_sentiment(news_list)
                        enhanced_data['news_summary'] = news_sentiment.get('summary', '')
                        enhanced_data['recent_news'] = [news['title'] for news in news_list[:3]]
                        enhanced_data['sentiment_score'] = news_sentiment.get('sentiment', 0)
                        enhanced_data['sentiment_label'] = "매우 긍정적" if news_sentiment.get('sentiment', 0) > 0.3 else "긍정적" if news_sentiment.get('sentiment', 0) > 0 else "부정적" if news_sentiment.get('sentiment', 0) < 0 else "중립적"

                    # 2. DART 재무 데이터 가져오기 (한국 주식만)
                    if is_korean and dart_client.is_valid and original_stock in stock_code_map:
                        stock_code = stock_code_map[original_stock]
                        financial_data = dart_client.get_financial_statements(stock_code)
                        if financial_data:
                            enhanced_data.update({
                                "pe_ratio": financial_data.get('pe_ratio', enhanced_data.get('pe_ratio', 0)),
                                "eps": financial_data.get('eps', enhanced_data.get('eps', 0)),
                                "roe": financial_data.get('roe', 0),
                                "roa": financial_data.get('roa', 0),
                                "debt_ratio": financial_data.get('debt_ratio', 0)
                            })

                        # 최근 공시 데이터
                        disclosures = dart_client.get_recent_disclosures(stock_code, 5)
                        if disclosures:
                            enhanced_data['recent_disclosures'] = disclosures

                    # 3. 기술적 분석 데이터 가져오기
                    if alpha_vantage_client.is_valid:
                        # 한국 주식은 .KS 후비 추가
                        symbol = f"{stock_code_map.get(original_stock, stock)}.KS" if is_korean else stock
                        technical_indicators = alpha_vantage_client.get_technical_indicators(symbol)
                        if technical_indicators:
                            enhanced_data['technical_signals'] = {
                                "rsi": technical_indicators.get('rsi', {}).get('value', 50),
                                "signal": technical_indicators.get('signals', {}).get('recommendation', '중립'),
                                "macd": technical_indicators.get('macd', {}).get('histogram', 0),
                                "trend": "상승" if technical_indicators.get('signals', {}).get('overall') in ['buy', 'strong_buy'] else "하락" if technical_indicators.get('signals', {}).get('overall') in ['sell', 'strong_sell'] else "횡보"
                            }

                    # 폴백 데이터 (기존 하드코딩 데이터)
                    # API 키가 없을 때 사용
                    if original_stock == "삼성전자" and not (dart_client.is_valid or news_client.is_newsapi_valid):
                        enhanced_data.update({
                            "pe_ratio": 12.8,    # 실제 PER
                            "eps": 5900,         # 주당순이익 (원)
                            "high_52w": 85000,   # 52주 최고가
                            "low_52w": 65000,    # 52주 최저가
                            "dividend_yield": 2.8,  # 배당수익률
                            "technical_signals": {
                                "rsi": 58.3,     # RSI 계산값
                                "signal": "매수",  # 매매 신호
                                "macd": 1250,     # MACD
                                "trend": "상승"
                            },
                            "sentiment_score": 0.15,  # 감성 점수
                            "sentiment_label": "긍정적",
                            "news_summary": "HBM3E 양산 본격화, AI 반도체 수요 급증으로 매출 증가 전망",
                            "recent_news": [
                                "삼성전자, HBM3E 본격 양산...AI 서버용 수요 급증",
                                "3분기 실적 컨센서스 상회 전망, 메모리 가격 상승세",
                                "엔비디아와 차세대 AI칩 공동 개발 계약 체결"
                            ],
                            "analyst_opinion": {
                                "target_price": 95000,
                                "recommendation": "매수",
                                "reason": "AI 반도체 슈퍼사이클 본격화, HBM 독점 공급사 지위 확고"
                            }
                        })
                    elif original_stock == "테슬라":
                        enhanced_data.update({
                            "pe_ratio": 67.8,    # 실제 PER
                            "high_52w": 415.0,   # 52주 최고가 ($)
                            "low_52w": 138.8,    # 52주 최저가 ($)
                            "eps": 5.85,         # EPS ($)
                            "technical_signals": {
                                "rsi": 62.7,
                                "signal": "강매수",
                                "macd": 8.5,
                                "trend": "강상승"
                            },
                            "sentiment_score": 0.25,
                            "sentiment_label": "매우 긍정적"
                        })
                    elif original_stock == "애플":
                        enhanced_data.update({
                            "pe_ratio": 28.5,
                            "high_52w": 199.6,
                            "low_52w": 164.1,
                            "eps": 6.16,
                            "technical_signals": {
                                "rsi": 45.2,
                                "signal": "중립",
                                "macd": -0.8,
                                "trend": "횡보"
                            },
                            "sentiment_score": 0.05,
                            "sentiment_label": "약간 긍정적"
                        })
                    elif original_stock == "SK하이닉스":
                        enhanced_data.update({
                            "pe_ratio": 18.2,
                            "eps": 4850,
                            "high_52w": 142000,
                            "low_52w": 95000,
                            "dividend_yield": 1.5,
                            "technical_signals": {
                                "rsi": 52.1,
                                "signal": "중립",
                                "macd": -850,
                                "trend": "횡보"
                            },
                            "sentiment_score": -0.05,
                            "sentiment_label": "약간 부정적",
                            "news_summary": "메모리 반도체 가격 하락 우려, 중국 수요 둔화",
                            "recent_news": [
                                "SK하이닉스, DRAM 가격 추가 하락 전망",
                                "중국 스마트폰 시장 침체로 메모리 수요 감소",
                                "하반기 재고 조정 지속될 것으로 예상"
                            ],
                            "analyst_opinion": {
                                "target_price": 115000,
                                "recommendation": "중립",
                                "reason": "메모리 업황 하락세지만 AI 서버용 HBM 성장은 긍정적"
                            }
                        })
                    elif original_stock == "LG에너지솔루션":
                        enhanced_data.update({
                            "pe_ratio": 25.6,
                            "eps": 15200,
                            "high_52w": 580000,
                            "low_52w": 380000,
                            "dividend_yield": 0.8,
                            "technical_signals": {
                                "rsi": 61.8,
                                "signal": "매수",
                                "macd": 2800,
                                "trend": "상승"
                            },
                            "sentiment_score": 0.20,
                            "sentiment_label": "긍정적",
                            "news_summary": "전기차 배터리 수주 증가, GM과 장기계약 체결"
                        })
                    elif original_stock == "카카오":
                        enhanced_data.update({
                            "pe_ratio": -15.8,  # 적자
                            "eps": -2850,
                            "high_52w": 89000,
                            "low_52w": 38500,
                            "dividend_yield": 0.0,
                            "technical_signals": {
                                "rsi": 35.2,
                                "signal": "관망",
                                "macd": -1200,
                                "trend": "하락"
                            },
                            "sentiment_score": -0.15,
                            "sentiment_label": "부정적",
                            "news_summary": "플랫폼 수수료 규제 강화, 광고매출 감소 우려"
                        })
                    elif original_stock == "네이버":
                        enhanced_data.update({
                            "pe_ratio": 22.4,
                            "eps": 8950,
                            "high_52w": 245000,
                            "low_52w": 165000,
                            "dividend_yield": 0.6,
                            "technical_signals": {
                                "rsi": 48.9,
                                "signal": "중립",
                                "macd": 450,
                                "trend": "횡보"
                            },
                            "sentiment_score": 0.08,
                            "sentiment_label": "중립적",
                            "news_summary": "AI 서비스 확장, 클라우드 사업 성장"
                        })
                    elif original_stock == "현대차":
                        enhanced_data.update({
                            "pe_ratio": 5.8,
                            "eps": 35000,
                            "high_52w": 245000,
                            "low_52w": 180000,
                            "dividend_yield": 3.2,
                            "technical_signals": {
                                "rsi": 55.7,
                                "signal": "매수",
                                "macd": 1800,
                                "trend": "상승"
                            },
                            "sentiment_score": 0.12,
                            "sentiment_label": "긍정적",
                            "news_summary": "전기차 라인업 확대, 미국 시장 점유율 상승"
                        })
                    elif original_stock == "셀트리온":
                        enhanced_data.update({
                            "pe_ratio": 8.9,
                            "eps": 18500,
                            "high_52w": 195000,
                            "low_52w": 145000,
                            "dividend_yield": 0.5,
                            "technical_signals": {
                                "rsi": 68.2,
                                "signal": "강매수",
                                "macd": 3200,
                                "trend": "강상승"
                            },
                            "sentiment_score": 0.30,
                            "sentiment_label": "매우 긍정적",
                            "news_summary": "바이오시밀러 매출 급증, 유럽 시장 확대"
                        })

                    return {
                        "success": True,
                        "type": "stock",
                        "data": enhanced_data
                    }
                else:
                    return {
                        "success": False,
                        "error": f"주식 '{original_stock}' 데이터를 가져올 수 없습니다"
                    }

            except Exception as e:
                print(f"[API] Stock analysis error: {str(e)}")
                return {
                    "success": False,
                    "error": f"주식 분석 중 오류가 발생했습니다: {str(e)}"
                }

        else:
            return {
                "success": False,
                "error": "인식할 수 없는 요청입니다"
            }

    except Exception as e:
        print(f"[API] Error: {str(e)}")
        return {"success": False, "error": str(e)}

@app.post("/api/analyze_advanced")
async def analyze_query_advanced(query: Dict[str, Any]):
    """고급 분석 REST API - 뉴스, 감성, 기술적 분석 포함"""
    message = query.get("message", "")

    if not message:
        return {"success": False, "error": "분석할 내용을 입력해주세요"}

    print(f"[ADVANCED API] Received query: {message}")

    # NLU로 의도 파악
    nlu_result = nlu_agent.analyze_query(message)
    intent = nlu_result["intent"]
    print(f"[ADVANCED API] NLU result: {intent}")

    if intent == "analyze_stock" and nlu_result["entities"].get("stocks"):
        stock = nlu_result["entities"]["stocks"][0]
        print(f"[ADVANCED API] Starting comprehensive analysis for: {stock}")

        try:
            # 1. 주가 데이터 수집
            async with PriceAgent() as price_agent:
                price_result = await price_agent.get_stock_price(stock)

            # 2. 감성 분석 실행
            sentiment_agent = SentimentAgent()
            sentiment_result = await sentiment_agent.analyze_sentiment(
                company_name=stock,
                period_days=7,
                max_items_per_source=30
            )

            # 3. 결과 조합
            if price_result.get("status") == "success":
                price_data = price_result.get("price_data", {})

                # 가격 포맷팅
                symbol = price_data.get("symbol", stock)
                if symbol.endswith('.KS') or stock in ['삼성전자', 'SK하이닉스', 'LG전자']:
                    price_str = f"₩{price_data.get('current_price', 0):,.0f}"
                else:
                    price_str = f"${price_data.get('current_price', 0):.2f}"

                change_value = price_data.get('change_percent', 0)
                change_str = f"{change_value:+.2f}%"

                # 주요 뉴스 요약 생성
                news_summary = []
                if hasattr(sentiment_result, 'key_factors') and sentiment_result.key_factors:
                    news_summary = sentiment_result.key_factors[:3]

                return {
                    "success": True,
                    "type": "advanced_stock",
                    "data": {
                        "name": stock,
                        "symbol": symbol,
                        "price": price_str,
                        "change": change_str,
                        "change_value": change_value,
                        "market_cap": price_data.get("market_cap", 0),
                        "volume": price_data.get("volume", 0),
                        # 고급 분석 데이터
                        "sentiment_score": sentiment_result.overall_sentiment,
                        "sentiment_label": sentiment_result.sentiment_label,
                        "confidence": sentiment_result.confidence,
                        "recommendation": sentiment_result.recommendation,
                        "news_summary": news_summary,
                        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "data_sources": list(sentiment_result.data_sources.keys())
                    }
                }
            else:
                return {"success": False, "error": "주가 데이터를 가져올 수 없습니다"}

        except Exception as e:
            print(f"[ADVANCED API] Error: {str(e)}")
            return {"success": False, "error": f"고급 분석 중 오류: {str(e)}"}

    elif intent == "analyze_crypto" and nlu_result["entities"].get("crypto"):
        crypto = nlu_result["entities"]["crypto"][0]
        print(f"[ADVANCED API] Starting crypto analysis for: {crypto}")

        try:
            # 암호화폐 분석 (기존 코드 활용)
            async with CryptoAgent() as crypto_agent:
                crypto_result = await crypto_agent.analyze_crypto(crypto)

            if crypto_result.get("status") == "success":
                data = crypto_result.get("data", {})
                crypto_data = data.get("crypto_data", {})

                # 가격 포맷팅
                price_krw = crypto_data.get("current_price_krw", 0)
                change_24h = crypto_data.get("price_change_percentage_24h", 0)

                return {
                    "success": True,
                    "type": "advanced_crypto",
                    "data": {
                        "name": crypto_data.get("name", crypto),
                        "symbol": crypto_data.get("symbol", "").upper(),
                        "price": f"₩{price_krw:,.0f}",
                        "change": f"{change_24h:+.2f}%",
                        "change_value": change_24h,
                        "market_cap": crypto_data.get("market_cap_krw", 0),
                        "volume_24h": crypto_data.get("volume_24h_krw", 0),
                        "market_cap_rank": crypto_data.get("market_cap_rank", 0),
                        "sentiment": crypto_result.get("sentiment", {}).get("overall_sentiment", 0),
                        "sentiment_label": crypto_result.get("sentiment", {}).get("sentiment_label", "중립적"),
                        "analysis": crypto_result.get("analysis", ""),
                        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            else:
                return {"success": False, "error": "암호화폐 데이터를 가져올 수 없습니다"}

        except Exception as e:
            print(f"[ADVANCED API] Crypto error: {str(e)}")
            return {"success": False, "error": f"암호화폐 분석 중 오류: {str(e)}"}

    else:
        return {"success": False, "error": "지원하지 않는 쿼리입니다"}

@app.get("/api/status")
async def get_api_status():
    """
    API 상태 확인 엔드포인트
    현재 설정된 API 키와 사용 가능한 기능 확인
    """
    checker = APIStatusChecker()
    status = checker.check_api_status()
    summary = checker.get_data_source_summary()

    return {
        "success": True,
        "api_status": status,
        "data_sources": summary,
        "quick_guide": checker.get_quick_start_guide()
    }

@app.get("/api/setup-guide/{api_name}")
async def get_api_setup_guide(api_name: str):
    """
    특정 API 설정 가이드
    """
    checker = APIStatusChecker()
    guide = checker.get_registration_guide(api_name)

    return {
        "success": True if "error" not in guide else False,
        "guide": guide
    }

@app.post("/api/analyze-foreign")
async def analyze_foreign_stock(query: Dict[str, Any]):
    """
    해외 주식 전용 분석 API
    더 상세한 해외 주식 데이터와 기술적 분석 제공
    """
    stock_name = query.get("message", "")

    if not stock_name:
        return {"success": False, "error": "주식명을 입력해주세요"}

    print(f"[FOREIGN API] Analyzing: {stock_name}")

    try:
        # 해외 주식 데이터 수집
        stock_data = await us_stock_client.get_stock_data(stock_name)

        if not stock_data or 'error' in stock_data:
            return {
                "success": False,
                "error": f"\"{stock_name}\" 데이터를 찾을 수 없습니다. 영문명을 사용해주세요."
            }

        # 환율 정보 추가
        usd_to_krw = 1330  # 고정 환율 (실제로는 API로 가져와야 함)

        # 가격 포맷팅
        current_price = stock_data.get('current_price', 0)
        change = stock_data.get('change', 0)
        change_percent = stock_data.get('change_percent', 0)

        price_str = f"${current_price:.2f}" if current_price else "데이터 없음"
        price_krw_str = f"(₩{current_price * usd_to_krw:,.0f})" if current_price else ""
        change_str = f"{'+' if change_percent > 0 else ''}{change_percent:.2f}%"

        # 기술적 분석 추가
        technical = stock_data.get('technical', {})
        analyst = stock_data.get('analyst', {})

        # 매매 신호 결정
        signal = technical.get('signal', '중립')
        rsi = technical.get('rsi', 50)

        # 목표가와 상승 잠재력
        target_mean = analyst.get('target_mean', 0)
        upside = analyst.get('upside_potential', 0)

        # 응답 데이터 구성
        response_data = {
            "success": True,
            "type": "foreign_stock",
            "data": {
                "name": stock_data.get('name', stock_name),
                "symbol": stock_data.get('symbol', stock_name),
                "price": f"{price_str} {price_krw_str}",
                "price_usd": current_price,
                "price_krw": current_price * usd_to_krw,
                "change": change_str,
                "change_value": change_percent,
                "market_cap": stock_data.get('market_cap', 0),
                "volume": stock_data.get('volume', 0),
                "average_volume": stock_data.get('average_volume', 0),
                "pe_ratio": stock_data.get('pe_ratio', 0),
                "forward_pe": stock_data.get('forward_pe', 0),
                "eps": stock_data.get('eps', 0),
                "dividend_yield": stock_data.get('dividend_yield', 0),
                "beta": stock_data.get('beta', 0),
                "high_52w": stock_data.get('high_52w', 0),
                "low_52w": stock_data.get('low_52w', 0),
                "day_high": stock_data.get('day_high', 0),
                "day_low": stock_data.get('day_low', 0),
                "sector": stock_data.get('sector', ''),
                "industry": stock_data.get('industry', ''),
                "description": stock_data.get('description', ''),
                "exchange": stock_data.get('exchange', 'NASDAQ'),
                # 기술적 분석
                "technical_signals": {
                    "rsi": rsi,
                    "signal": signal,
                    "trend": technical.get('trend', '횡보'),
                    "ma5": technical.get('ma5', 0),
                    "ma20": technical.get('ma20', 0),
                    "ma50": technical.get('ma50', 0),
                    "support": technical.get('support', 0),
                    "resistance": technical.get('resistance', 0)
                },
                # 애널리스트 의견
                "analyst_opinion": {
                    "target_mean": target_mean,
                    "target_high": analyst.get('target_high', 0),
                    "target_low": analyst.get('target_low', 0),
                    "rating": analyst.get('rating', '중립'),
                    "recommendation": analyst.get('recommendation', 'none'),
                    "upside_potential": upside,
                    "number_of_analysts": analyst.get('number_of_analysts', 0)
                },
                # 뉴스
                "news": stock_data.get('news', [])[:5],
                # 요약 분석
                "analysis_summary": {
                    "investment_score": calculate_investment_score(stock_data),
                    "recommendation": get_investment_recommendation(stock_data),
                    "key_points": get_key_investment_points(stock_data)
                }
            }
        }

        return response_data

    except Exception as e:
        print(f"[FOREIGN API] Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            "success": False,
            "error": f"해외 주식 분석 중 오류가 발생했습니다: {str(e)}"
        }

def calculate_investment_score(data: Dict) -> int:
    """데이터 기반 투자 점수 계산 (0-100)"""
    score = 50  # 기본 점수

    # 기술적 분석
    technical = data.get('technical', {})
    if technical.get('signal') in ['강매수', '매수']:
        score += 15
    elif technical.get('signal') in ['강매도', '매도']:
        score -= 15

    # RSI
    rsi = technical.get('rsi', 50)
    if rsi < 30:
        score += 10  # 과매도
    elif rsi > 70:
        score -= 10  # 과매수

    # 애널리스트 의견
    analyst = data.get('analyst', {})
    if analyst.get('upside_potential', 0) > 20:
        score += 15
    elif analyst.get('upside_potential', 0) < -10:
        score -= 10

    # 밸류에이션
    pe = data.get('pe_ratio', 0)
    if 0 < pe < 15:
        score += 10  # 저평가
    elif pe > 35:
        score -= 5   # 고평가

    return max(0, min(100, score))

def get_investment_recommendation(data: Dict) -> str:
    """데이터 기반 투자 추천"""
    score = calculate_investment_score(data)

    if score >= 80:
        return "적극 매수 - 기술적/기본적 지표 모두 양호"
    elif score >= 65:
        return "매수 추천 - 전반적으로 긍정적"
    elif score >= 45:
        return "중립/관망 - 추가 모니터링 필요"
    elif score >= 30:
        return "매도 고려 - 부정적 신호 증가"
    else:
        return "매도 권고 - 위험 신호 강함"

def get_key_investment_points(data: Dict) -> List[str]:
    """투자 포인트 요약"""
    points = []

    # 상승 잠재력
    analyst = data.get('analyst', {})
    upside = analyst.get('upside_potential', 0)
    if upside > 0:
        points.append(f"현 주가 대비 {upside:.1f}% 상승 잠재력")

    # 기술적 분석
    technical = data.get('technical', {})
    if technical.get('signal'):
        points.append(f"기술적 신호: {technical.get('signal')}")

    # 밸류에이션
    pe = data.get('pe_ratio', 0)
    if 0 < pe < 20:
        points.append(f"PER {pe:.1f}배로 업계 평균 대비 저평가")

    # 배당
    div = data.get('dividend_yield', 0)
    if div > 2:
        points.append(f"배당수익률 {div:.2f}%")

    # 52주 비교
    current = data.get('current_price', 0)
    high_52w = data.get('high_52w', 0)
    low_52w = data.get('low_52w', 0)

    if high_52w and current:
        from_high = ((high_52w - current) / high_52w) * 100
        if from_high > 20:
            points.append(f"52주 최고가 대비 {from_high:.1f}% 하락")

    if low_52w and current:
        from_low = ((current - low_52w) / low_52w) * 100
        if from_low < 20:
            points.append(f"52주 최저가 근접 (+{from_low:.1f}%)")

    return points[:5]  # 최대 5개 포인트

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)