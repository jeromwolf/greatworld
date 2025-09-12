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
from api.professional_report_formatter import ProfessionalReportFormatter
from config.period_config import PeriodConfig

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
    """메인 페이지 반환 - 대시보드로 변경"""
    return FileResponse("frontend/dashboard.html")

@app.get("/old")
async def old_ui():
    """기존 채팅 UI"""
    return FileResponse("frontend/responsive.html")

@app.get("/chat")
async def chat():
    """채팅 페이지 반환"""
    return FileResponse("frontend/index.html")

@app.get("/responsive")
async def responsive():
    """반응형 페이지 반환"""
    return FileResponse("frontend/responsive.html")

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
            if nlu_result["intent"] == "analyze_stock" and nlu_result["entities"].get("stocks"):
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
                            "price_data": price_result.get("price_data", {}),  # 차트를 위한 가격 데이터 추가
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
                            ]
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
    """REST API 엔드포인트 - 쿼리 분석"""
    try:
        nlu_result = nlu_agent.analyze_query(query.get("message", ""))
        return {"success": True, "result": nlu_result}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)