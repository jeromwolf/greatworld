"""
서비스 레지스트리: 에이전트 동적 발견 및 관리

에이전트들이 자신을 등록하고, 다른 에이전트를 발견할 수 있는 중앙 레지스트리
"""

import asyncio
import httpx
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn


class AgentInfo(BaseModel):
    """에이전트 정보 모델"""
    agent_id: str
    name: str
    description: str
    endpoint: str
    capabilities: List[Dict]
    status: str = "active"
    last_heartbeat: datetime = None
    metadata: Dict = {}


class ServiceRegistry:
    """서비스 레지스트리 구현"""
    
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self.capabilities_index: Dict[str, Set[str]] = {}  # capability -> agent_ids
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 90  # seconds
        
    async def register_agent(self, agent_info: AgentInfo) -> Dict:
        """에이전트 등록"""
        agent_id = agent_info.agent_id
        if not agent_id:
            agent_id = str(uuid.uuid4())
            agent_info.agent_id = agent_id
            
        agent_info.last_heartbeat = datetime.now()
        self.agents[agent_id] = agent_info
        
        # 능력별 인덱스 업데이트
        for capability in agent_info.capabilities:
            cap_name = capability.get("name")
            if cap_name:
                if cap_name not in self.capabilities_index:
                    self.capabilities_index[cap_name] = set()
                self.capabilities_index[cap_name].add(agent_id)
                
        print(f"✅ 에이전트 등록 완료: {agent_info.name} ({agent_id})")
        
        return {
            "agent_id": agent_id,
            "status": "registered",
            "message": f"Agent {agent_info.name} successfully registered"
        }
        
    async def deregister_agent(self, agent_id: str) -> Dict:
        """에이전트 등록 해제"""
        if agent_id in self.agents:
            agent_info = self.agents[agent_id]
            
            # 능력 인덱스에서 제거
            for capability in agent_info.capabilities:
                cap_name = capability.get("name")
                if cap_name and cap_name in self.capabilities_index:
                    self.capabilities_index[cap_name].discard(agent_id)
                    
            del self.agents[agent_id]
            print(f"🔴 에이전트 등록 해제: {agent_info.name} ({agent_id})")
            
            return {"status": "deregistered", "message": f"Agent {agent_id} deregistered"}
        
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
    async def update_heartbeat(self, agent_id: str) -> Dict:
        """에이전트 상태 업데이트 (하트비트)"""
        if agent_id in self.agents:
            self.agents[agent_id].last_heartbeat = datetime.now()
            return {"status": "ok", "timestamp": datetime.now().isoformat()}
            
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
    async def discover_agents(self, capability: Optional[str] = None) -> List[AgentInfo]:
        """에이전트 발견"""
        active_agents = []
        current_time = datetime.now()
        
        # 타임아웃된 에이전트 필터링
        for agent_id, agent_info in list(self.agents.items()):
            if agent_info.last_heartbeat:
                time_diff = (current_time - agent_info.last_heartbeat).total_seconds()
                if time_diff > self.heartbeat_timeout:
                    agent_info.status = "inactive"
                else:
                    agent_info.status = "active"
                    
            if agent_info.status == "active":
                if capability:
                    # 특정 능력을 가진 에이전트만 반환
                    if capability in self.capabilities_index and agent_id in self.capabilities_index[capability]:
                        active_agents.append(agent_info)
                else:
                    active_agents.append(agent_info)
                    
        return active_agents
        
    async def get_agent_info(self, agent_id: str) -> AgentInfo:
        """특정 에이전트 정보 조회"""
        if agent_id in self.agents:
            return self.agents[agent_id]
            
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
    async def health_check_agents(self):
        """모든 에이전트 상태 확인"""
        async with httpx.AsyncClient() as client:
            for agent_id, agent_info in self.agents.items():
                try:
                    # 각 에이전트의 health endpoint 호출
                    health_url = f"{agent_info.endpoint}/health"
                    response = await client.get(health_url, timeout=5.0)
                    
                    if response.status_code == 200:
                        agent_info.status = "active"
                        agent_info.last_heartbeat = datetime.now()
                    else:
                        agent_info.status = "unhealthy"
                        
                except Exception as e:
                    agent_info.status = "unreachable"
                    print(f"⚠️ 에이전트 {agent_info.name} 상태 확인 실패: {e}")
                    
    async def update_agent_capabilities(self, agent_id: str, capabilities: List[Dict]) -> Dict:
        """에이전트 능력 업데이트"""
        if agent_id not in self.agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
            
        agent_info = self.agents[agent_id]
        
        # 기존 능력 인덱스에서 제거
        for capability in agent_info.capabilities:
            cap_name = capability.get("name")
            if cap_name and cap_name in self.capabilities_index:
                self.capabilities_index[cap_name].discard(agent_id)
                
        # 새 능력 설정
        agent_info.capabilities = capabilities
        
        # 새 능력 인덱스에 추가
        for capability in capabilities:
            cap_name = capability.get("name")
            if cap_name:
                if cap_name not in self.capabilities_index:
                    self.capabilities_index[cap_name] = set()
                self.capabilities_index[cap_name].add(agent_id)
                
        print(f"✅ 에이전트 {agent_info.name}의 능력 업데이트: {[cap.get('name') for cap in capabilities]}")
        
        return {
            "status": "updated",
            "agent_id": agent_id,
            "capabilities": capabilities
        }


# FastAPI 앱 생성
app = FastAPI(title="A2A Service Registry", version="1.0.0")
registry = ServiceRegistry()


@app.post("/register")
async def register_agent(agent_info: AgentInfo):
    """에이전트 등록 엔드포인트"""
    return await registry.register_agent(agent_info)


@app.delete("/register/{agent_id}")
async def deregister_agent(agent_id: str):
    """에이전트 등록 해제 엔드포인트"""
    return await registry.deregister_agent(agent_id)


@app.put("/heartbeat/{agent_id}")
async def update_heartbeat(agent_id: str):
    """하트비트 업데이트 엔드포인트"""
    return await registry.update_heartbeat(agent_id)


@app.get("/discover")
async def discover_agents(capability: Optional[str] = None):
    """에이전트 발견 엔드포인트"""
    agents = await registry.discover_agents(capability)
    return {"agents": agents, "count": len(agents)}


@app.get("/agents/{agent_id}")
async def get_agent_info(agent_id: str):
    """특정 에이전트 정보 조회 엔드포인트"""
    return await registry.get_agent_info(agent_id)


@app.get("/health")
async def health_check():
    """레지스트리 상태 확인"""
    return {
        "status": "healthy",
        "registered_agents": len(registry.agents),
        "active_agents": len([a for a in registry.agents.values() if a.status == "active"])
    }


@app.put("/agents/{agent_id}/capabilities")
async def update_agent_capabilities(agent_id: str, request_body: Dict):
    """에이전트 능력 업데이트 엔드포인트"""
    capabilities = request_body.get("capabilities", [])
    return await registry.update_agent_capabilities(agent_id, capabilities)


# 주기적인 헬스체크 태스크
async def periodic_health_check():
    """주기적으로 모든 에이전트 상태 확인"""
    while True:
        await asyncio.sleep(30)  # 30초마다
        await registry.health_check_agents()


@app.on_event("startup")
async def startup_event():
    """서비스 시작 시 백그라운드 태스크 실행"""
    asyncio.create_task(periodic_health_check())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)