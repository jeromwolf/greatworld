"""
StockAI FastAPI 메인 애플리케이션
WebSocket을 통한 실시간 채팅 기능 제공
"""
import os
import sys
from datetime import datetime
from typing import List, Dict, Any
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Simple NLU Agent import
from agents.simple_nlu_agent import SimpleNLUAgent
from agents.dart_agent import DartAgent
from agents.sec_agent import SECAgent
from agents.news_agent import NewsAgent
from agents.social_agent import SocialAgent
from agents.sentiment_agent import SentimentAgent

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

@app.get("/")
async def root():
    """메인 페이지 반환"""
    return FileResponse("frontend/index.html")

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
            message_data = json.loads(data)
            
            # NLU 처리
            nlu_result = nlu_agent.analyze_query(message_data["message"])
            
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
                # 종목 정보 추출
                stock = nlu_result["entities"]["stocks"][0]
                
                # 한국/미국 주식 구분
                is_korean = any(char >= '가' and char <= '힣' for char in stock)
                
                try:
                    # 병렬로 데이터 수집
                    tasks = []
                    
                    # 뉴스 수집
                    async with NewsAgent() as news_agent:
                        if is_korean:
                            news_task = news_agent.search_korean_news(stock)
                        else:
                            news_task = news_agent.search_news(stock, language="en")
                        tasks.append(("news", news_task))
                    
                    # 소셜 데이터 수집
                    async with SocialAgent() as social_agent:
                        if not is_korean:
                            reddit_task = social_agent.search_reddit(stock)
                            tasks.append(("reddit", reddit_task))
                    
                    # 모든 태스크 실행
                    results = {}
                    data_source_summary = {"REAL_DATA": 0, "MOCK_DATA": 0}
                    
                    for name, task in tasks:
                        try:
                            result = await task
                            results[name] = result
                            
                            # 데이터 소스 추적
                            if result and result.get("data_source"):
                                data_source_type = result.get("data_source")
                                data_source_summary[data_source_type] += 1
                        except Exception as e:
                            print(f"Error in {name}: {str(e)}")
                            data_source_summary["MOCK_DATA"] += 1
                    
                    # 감성 분석 실행
                    sentiment_agent = SentimentAgent()
                    
                    # 데이터 준비
                    data_sources = {}
                    if "news" in results and results["news"]["status"] == "success":
                        data_sources["news"] = results["news"]
                    if "reddit" in results and results["reddit"]["status"] == "success":
                        data_sources["social"] = {"reddit": results["reddit"]}
                    
                    # 감성 분석
                    if data_sources:
                        sentiment_result = await sentiment_agent.analyze_sentiment(
                            ticker=stock,
                            company_name=stock,
                            data_sources=data_sources
                        )
                        
                        # 감성 분석 결과의 데이터 소스도 추적
                        for source_name, source_data in sentiment_result.data_sources.items():
                            if source_data.get("data_source"):
                                data_source_type = source_data.get("data_source")
                                if data_source_type not in data_source_summary:
                                    data_source_summary[data_source_type] = 0
                        
                        # 데이터 소스 요약 생성
                        data_source_info = create_data_source_info(data_source_summary)
                        
                        # 결과 포맷팅
                        analysis_message = f"""
📊 **{sentiment_result.company_name} 분석 결과**{data_source_info}
**전체 감성**: {sentiment_result.sentiment_label} (점수: {sentiment_result.overall_sentiment})
**신뢰도**: {sentiment_result.confidence:.0%}

**주요 영향 요인:**
"""
                        for factor in sentiment_result.key_factors:
                            analysis_message += f"• {factor}\\n"
                        
                        analysis_message += f"\\n**AI 의견:**\\n{sentiment_result.recommendation}"
                        
                        # 분석 결과 전송
                        response = {
                            "type": "bot",
                            "message": analysis_message,
                            "data": {
                                "sentiment": sentiment_result.overall_sentiment,
                                "sources": sentiment_result.data_sources,
                                "data_source_summary": data_source_summary,
                                "reliability": get_reliability_level(data_source_summary)
                            },
                            "timestamp": datetime.utcnow().isoformat()
                        }
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
                    response = {
                        "type": "bot",
                        "message": f"분석 중 오류가 발생했습니다: {str(e)}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
            else:
                # 다른 의도 처리
                response = {
                    "type": "bot",
                    "message": f"'{message_data['message']}'에 대해 이해했습니다. 현재는 주식 분석 기능만 지원합니다.",
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
        print(f"Error in websocket connection: {str(e)}")
        manager.disconnect(websocket)

@app.post("/api/analyze")
async def analyze_query(query: Dict[str, Any]):
    """REST API 엔드포인트 - 쿼리 분석"""
    try:
        nlu_result = nlu_agent.parse_query(query.get("message", ""))
        return {"success": True, "result": nlu_result}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)