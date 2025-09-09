"""
A2A Registry Server

에이전트 등록 및 발견을 위한 중앙 레지스트리 서버
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

# AgentInfo를 직접 정의
class AgentInfo:
    """에이전트 정보"""
    def __init__(self, agent_id: str, name: str, description: str, 
                 endpoint: str, capabilities: List[Dict], metadata: Optional[Dict] = None):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.endpoint = endpoint
        self.capabilities = capabilities
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "endpoint": self.endpoint,
            "capabilities": self.capabilities,
            "metadata": self.metadata
        }


class RegisterRequest(BaseModel):
    """에이전트 등록 요청"""
    agent_id: str
    name: str
    description: str
    endpoint: str
    capabilities: List[Dict]
    metadata: Optional[Dict] = {}


class DiscoverResponse(BaseModel):
    """에이전트 발견 응답"""
    agents: List[Dict]


class Registry:
    """에이전트 레지스트리"""
    
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self.last_heartbeat: Dict[str, datetime] = {}
        self.timeout_seconds = 120  # 2분
        
    def register_agent(self, request: RegisterRequest) -> AgentInfo:
        """에이전트 등록"""
        agent_info = AgentInfo(
            agent_id=request.agent_id,
            name=request.name,
            description=request.description,
            endpoint=request.endpoint,
            capabilities=request.capabilities,
            metadata=request.metadata
        )
        
        self.agents[request.agent_id] = agent_info
        self.last_heartbeat[request.agent_id] = datetime.now()
        
        print(f"✅ 에이전트 등록: {agent_info.name} (ID: {agent_info.agent_id})")
        print(f"   - Endpoint: {agent_info.endpoint}")
        print(f"   - Capabilities: {[c['name'] for c in agent_info.capabilities]}")
        
        return agent_info
        
    def update_heartbeat(self, agent_id: str):
        """하트비트 업데이트"""
        if agent_id in self.agents:
            self.last_heartbeat[agent_id] = datetime.now()
            # 하트비트 로그는 비활성화 (너무 많은 로그 방지)
            # print(f"💓 하트비트 업데이트: {agent_id}")
        else:
            raise ValueError(f"Unknown agent: {agent_id}")
            
    def discover_agents(self, capability: Optional[str] = None) -> List[AgentInfo]:
        """활성 에이전트 발견"""
        # 타임아웃된 에이전트 제거
        self._cleanup_inactive_agents()
        
        active_agents = []
        for agent_id, agent_info in self.agents.items():
            if capability:
                # 특정 능력을 가진 에이전트만 필터링
                has_capability = any(
                    cap.get("name") == capability 
                    for cap in agent_info.capabilities
                )
                if has_capability:
                    active_agents.append(agent_info)
            else:
                active_agents.append(agent_info)
                
        print(f"🔍 에이전트 검색 - capability: {capability}")
        print(f"   - 활성 에이전트 수: {len(active_agents)}")
        
        return active_agents
        
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """특정 에이전트 조회"""
        self._cleanup_inactive_agents()
        return self.agents.get(agent_id)
        
    def _cleanup_inactive_agents(self):
        """비활성 에이전트 정리"""
        now = datetime.now()
        timeout_threshold = now - timedelta(seconds=self.timeout_seconds)
        
        inactive_agents = []
        for agent_id, last_seen in self.last_heartbeat.items():
            if last_seen < timeout_threshold:
                inactive_agents.append(agent_id)
                
        for agent_id in inactive_agents:
            agent_name = self.agents[agent_id].name
            del self.agents[agent_id]
            del self.last_heartbeat[agent_id]
            print(f"🔴 비활성 에이전트 제거: {agent_name} (ID: {agent_id})")


# FastAPI 앱 생성
app = FastAPI(title="A2A Registry Server")
registry = Registry()


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "A2A Registry Server",
        "version": "1.0.0",
        "active_agents": len(registry.agents)
    }


@app.post("/register")
async def register_agent(request: RegisterRequest):
    """에이전트 등록"""
    try:
        agent_info = registry.register_agent(request)
        return agent_info.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/heartbeat/{agent_id}")
async def update_heartbeat(agent_id: str):
    """하트비트 업데이트"""
    try:
        registry.update_heartbeat(agent_id)
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/discover", response_model=DiscoverResponse)
async def discover_agents(capability: Optional[str] = None):
    """에이전트 발견"""
    agents = registry.discover_agents(capability)
    return DiscoverResponse(
        agents=[agent.to_dict() for agent in agents]
    )


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """특정 에이전트 조회"""
    agent = registry.get_agent(agent_id)
    if agent:
        return agent.to_dict()
    else:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")


@app.get("/status")
async def get_status():
    """레지스트리 상태"""
    registry._cleanup_inactive_agents()
    
    return {
        "total_agents": len(registry.agents),
        "agents": [
            {
                "id": agent_id,
                "name": agent.name,
                "endpoint": agent.endpoint,
                "capabilities": [c["name"] for c in agent.capabilities],
                "last_heartbeat": registry.last_heartbeat.get(agent_id).isoformat()
            }
            for agent_id, agent in registry.agents.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)