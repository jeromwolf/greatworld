"""
베이스 에이전트 클래스

모든 A2A 에이전트가 상속받아야 하는 기본 클래스
"""

import asyncio
import httpx
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import uvicorn

from ..protocols.message import A2AMessage, MessageType, Priority
from ..registry.service_registry import AgentInfo


class BaseAgent(ABC):
    """A2A 베이스 에이전트"""
    
    def __init__(
        self,
        name: str,
        description: str,
        port: int,
        registry_url: str = "http://localhost:8001"
    ):
        self.agent_id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.port = port
        self.registry_url = registry_url
        self.endpoint = f"http://localhost:{port}"
        
        # Lifespan 컨텍스트 매니저 정의
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # 시작 시
            await self.start()
            yield
            # 종료 시
            await self.stop()
        
        # FastAPI 앱 (lifespan 포함)
        self.app = FastAPI(title=name, description=description, lifespan=lifespan)
        
        # 능력 목록
        self.capabilities = []
        
        # 메시지 큐
        self.message_queue = asyncio.Queue()
        
        # 다른 에이전트 캐시
        self.known_agents: Dict[str, AgentInfo] = {}
        
        # HTTP 클라이언트
        self.http_client = None
        
        # 하트비트 태스크
        self.heartbeat_task = None
        
        # 레지스트리 등록 상태
        self.is_registered = False
        
        # 기본 라우트 설정
        self._setup_routes()
        
    def _setup_routes(self):
        """기본 라우트 설정"""
        
        @self.app.get("/health")
        async def health_check():
            """상태 확인 엔드포인트"""
            return {
                "status": "healthy",
                "agent_id": self.agent_id,
                "name": self.name,
                "timestamp": datetime.now().isoformat()
            }
            
        @self.app.post("/message")
        async def receive_message(message: Dict):
            """메시지 수신 엔드포인트"""
            try:
                a2a_message = A2AMessage(**message)
                await self.message_queue.put(a2a_message)
                
                # ACK 필요한 경우
                if a2a_message.metadata.require_ack:
                    return {"status": "received", "message_id": a2a_message.header.message_id}
                    
                return {"status": "accepted"}
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
                
        @self.app.get("/capabilities")
        async def get_capabilities():
            """에이전트 능력 조회"""
            return {
                "agent_id": self.agent_id,
                "name": self.name,
                "capabilities": self.capabilities
            }
            
    async def register_capability(self, capability: Dict):
        """능력 등록"""
        self.capabilities.append(capability)
        
        # 레지스트리에 capability 업데이트 (에이전트가 등록된 후에만)
        # 초기 등록 시에는 _register_to_registry()에서 capabilities가 함께 전달됨
        if self.http_client and self.is_registered:
            await self._update_capabilities_in_registry()
        
    async def start(self):
        """에이전트 시작"""
        print(f"🚀 {self.name} 에이전트 시작중...")
        
        # HTTP 클라이언트 초기화
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # 초기화 수행 (capabilities 등록 포함)
        await self.on_start()
        
        # 레지스트리에 등록 (on_start 이후에 실행하여 capabilities가 포함되도록)
        await self._register_to_registry()
        
        # 하트비트 시작
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # 메시지 처리 루프 시작
        asyncio.create_task(self._message_processing_loop())
        
        print(f"✅ {self.name} 에이전트 시작 완료 (ID: {self.agent_id})")
        
    async def stop(self):
        """에이전트 종료"""
        print(f"🛑 {self.name} 에이전트 종료중...")
        
        # 종료 전 처리
        await self.on_stop()
        
        # 하트비트 중지
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            
        # 레지스트리에서 등록 해제
        await self._deregister_from_registry()
        
        # HTTP 클라이언트 종료
        if self.http_client:
            await self.http_client.aclose()
            
        print(f"✅ {self.name} 에이전트 종료 완료")
        
    async def _register_to_registry(self):
        """서비스 레지스트리에 등록"""
        try:
            agent_info = {
                "agent_id": self.agent_id,
                "name": self.name,
                "description": self.description,
                "endpoint": self.endpoint,
                "capabilities": self.capabilities,
                "status": "active"
            }
            
            response = await self.http_client.post(
                f"{self.registry_url}/register",
                json=agent_info
            )
            
            if response.status_code == 200:
                print(f"✅ 레지스트리 등록 성공: {self.name}")
                self.is_registered = True
            else:
                print(f"❌ 레지스트리 등록 실패: {response.text}")
                
        except Exception as e:
            print(f"❌ 레지스트리 연결 실패: {e}")
            
    async def _update_capabilities_in_registry(self):
        """레지스트리에 능력 업데이트"""
        try:
            response = await self.http_client.put(
                f"{self.registry_url}/agents/{self.agent_id}/capabilities",
                json={"capabilities": self.capabilities}
            )
            
            if response.status_code == 200:
                print(f"✅ 능력 업데이트 성공: {[cap.get('name') for cap in self.capabilities]}")
            else:
                print(f"❌ 능력 업데이트 실패: {response.text}")
                
        except Exception as e:
            print(f"❌ 능력 업데이트 오류: {e}")
            
    async def _deregister_from_registry(self):
        """서비스 레지스트리에서 등록 해제"""
        try:
            response = await self.http_client.delete(
                f"{self.registry_url}/register/{self.agent_id}"
            )
            
            if response.status_code == 200:
                print(f"✅ 레지스트리 등록 해제 성공: {self.name}")
                self.is_registered = False
                
        except Exception as e:
            print(f"⚠️ 레지스트리 등록 해제 실패: {e}")
            
    async def _heartbeat_loop(self):
        """하트비트 전송 루프"""
        # 설정에서 하트비트 주기 가져오기 (기본값 600초 = 10분)
        heartbeat_interval = 600  # 10분 기본값
        try:
            from utils.config_manager import config
            heartbeat_interval = config.get("registry.heartbeat_interval", 600)
        except:
            pass
            
        heartbeat_count = 0
        while True:
            try:
                await asyncio.sleep(heartbeat_interval)
                heartbeat_count += 1
                
                response = await self.http_client.put(
                    f"{self.registry_url}/heartbeat/{self.agent_id}"
                )
                
                if response.status_code != 200:
                    print(f"⚠️ 하트비트 실패: {response.text}")
                else:
                    # 10회에 1번만 로그 출력 (100분에 1번)
                    if heartbeat_count % 10 == 0:
                        print(f"💓 하트비트 업데이트 완료 ({heartbeat_count}회)")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ 하트비트 오류: {e}")
                
    async def _message_processing_loop(self):
        """메시지 처리 루프"""
        while True:
            try:
                # 메시지 대기
                message = await self.message_queue.get()
                
                # 만료된 메시지 무시
                if message.is_expired():
                    print(f"⏰ 만료된 메시지 무시: {message.header.message_id}")
                    continue
                    
                # 메시지 처리
                await self.handle_message(message)
                
            except Exception as e:
                print(f"❌ 메시지 처리 오류: {e}")
                
    async def discover_agents(self, capability: Optional[str] = None) -> List[AgentInfo]:
        """다른 에이전트 발견"""
        try:
            print(f"🔍 에이전트 검색 시작 - capability: {capability}")
            print(f"📡 Registry URL: {self.registry_url}")
            
            response = await self.http_client.get(
                f"{self.registry_url}/discover",
                params={"capability": capability} if capability else {}
            )
            
            print(f"📨 Registry 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Registry 응답 데이터: {data}")
                
                agents = [AgentInfo(**agent) for agent in data["agents"]]
                print(f"✅ 발견된 에이전트 수: {len(agents)}")
                
                # 캐시 업데이트
                for agent in agents:
                    self.known_agents[agent.agent_id] = agent
                    print(f"   - {agent.name} (ID: {agent.agent_id})")
                    
                return agents
            else:
                print(f"❌ Registry 응답 오류: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ 에이전트 발견 실패: {e}")
            import traceback
            traceback.print_exc()
            return []
            
    async def send_message(
        self,
        receiver_id: str,
        action: str,
        payload: Dict[str, Any],
        priority: Priority = Priority.NORMAL,
        require_ack: bool = False
    ) -> Optional[A2AMessage]:
        """다른 에이전트에게 메시지 전송"""
        print(f"\n🔍 [DEBUG] send_message 호출됨")
        print(f"   - receiver_id: {receiver_id}")
        print(f"   - action: {action}")
        print(f"   - payload: {payload}")
        try:
            # 수신자 정보 확인
            if receiver_id not in self.known_agents:
                print(f"   - {receiver_id}가 캐시에 없음, 레지스트리 조회 시작")
                # 캐시에 없으면 레지스트리에서 조회
                # 먼저 전체 에이전트 목록에서 이름으로 검색
                print(f"   - Registry URL: {self.registry_url}/discover")
                response = await self.http_client.get(f"{self.registry_url}/discover")
                print(f"   - Registry 응답 상태: {response.status_code}")
                
                if response.status_code == 200:
                    agents_data = response.json()
                    agents = agents_data.get("agents", [])
                    
                    # 이름 또는 ID로 매칭되는 에이전트 찾기
                    # receiver_id를 소문자로 변환하고 공백을 하이픈으로 치환하여 비교
                    receiver_id_normalized = receiver_id.lower().replace("-", " ")
                    found_agent = None
                    for agent_data in agents:
                        agent_name = agent_data.get("name", "").lower()
                        agent_id = agent_data.get("agent_id", "")
                        
                        # 여러 형식으로 매칭 시도
                        if (agent_data.get("name") == receiver_id or 
                            agent_data.get("agent_id") == receiver_id or
                            agent_name.replace(" ", "-") == receiver_id or
                            agent_name == receiver_id_normalized):
                            found_agent = agent_data
                            break
                    
                    if found_agent:
                        agent_info = AgentInfo(**found_agent)
                        self.known_agents[receiver_id] = agent_info
                    else:
                        print(f"❌ 수신자를 찾을 수 없음: {receiver_id}")
                        return None
                else:
                    print(f"❌ 레지스트리 조회 실패: {response.status_code}")
                    return None
                    
            receiver = self.known_agents[receiver_id]
            
            # 메시지 생성
            message = A2AMessage.create_request(
                sender_id=self.agent_id,
                receiver_id=receiver_id,
                action=action,
                payload=payload
            )
            
            message.metadata.priority = priority
            message.metadata.require_ack = require_ack
            
            # 메시지 전송
            response = await self.http_client.post(
                f"{receiver.endpoint}/message",
                json=message.to_dict()
            )
            
            if response.status_code == 200:
                print(f"📤 메시지 전송 성공: {action} -> {receiver.name}")
                return message
            else:
                print(f"❌ 메시지 전송 실패: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 메시지 전송 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    async def broadcast_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ):
        """이벤트 브로드캐스트"""
        # 모든 활성 에이전트 발견
        agents = await self.discover_agents()
        
        # 이벤트 메시지 생성
        message = A2AMessage.create_event(
            sender_id=self.agent_id,
            event_type=event_type,
            event_data=event_data
        )
        
        # 모든 에이전트에게 전송
        tasks = []
        for agent in agents:
            if agent.agent_id != self.agent_id:  # 자기 자신 제외
                task = self.http_client.post(
                    f"{agent.endpoint}/message",
                    json=message.to_dict()
                )
                tasks.append(task)
                
        # 병렬 전송
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        print(f"📢 이벤트 브로드캐스트 완료: {event_type} ({success_count}/{len(tasks)} 성공)")
        
    async def reply_to_message(
        self,
        original_message: A2AMessage,
        result: Any,
        success: bool = True
    ):
        """메시지에 응답"""
        print(f"📤 reply_to_message 시작 - sender_id: {original_message.header.sender_id}")
        
        response = A2AMessage.create_response(
            original_message=original_message,
            sender_id=self.agent_id,
            result=result,
            success=success
        )
        
        # 응답 전송
        receiver = self.known_agents.get(original_message.header.sender_id)
        if receiver:
            print(f"📍 캐시에서 수신자 발견: {receiver.name} at {receiver.endpoint}")
            try:
                resp = await self.http_client.post(
                    f"{receiver.endpoint}/message",
                    json=response.to_dict()
                )
                print(f"✅ 응답 전송 완료 - status: {resp.status_code}")
            except Exception as e:
                print(f"❌ 응답 전송 실패: {e}")
                raise
        else:
            # known_agents에 없으면 레지스트리에서 조회
            print(f"⚠️ 수신자 {original_message.header.sender_id}를 캐시에서 찾을 수 없음. 레지스트리 조회 시도...")
            try:
                response_r = await self.http_client.get(
                    f"{self.registry_url}/agents/{original_message.header.sender_id}"
                )
                if response_r.status_code == 200:
                    agent_info = AgentInfo(**response_r.json())
                    self.known_agents[agent_info.agent_id] = agent_info
                    await self.http_client.post(
                        f"{agent_info.endpoint}/message",
                        json=response.to_dict()
                    )
                    print(f"✅ 응답 전송 성공: {agent_info.name}")
                else:
                    print(f"❌ 레지스트리에서 수신자 정보를 찾을 수 없음: {original_message.header.sender_id}")
            except Exception as e:
                print(f"❌ 응답 전송 실패: {e}")
            
    @abstractmethod
    async def handle_message(self, message: A2AMessage):
        """메시지 처리 (하위 클래스에서 구현)"""
        pass
        
    @abstractmethod
    async def on_start(self):
        """에이전트 시작 시 호출 (하위 클래스에서 구현)"""
        pass
        
    @abstractmethod
    async def on_stop(self):
        """에이전트 종료 시 호출 (하위 클래스에서 구현)"""
        pass
        
    def run(self):
        """에이전트 실행"""
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)