"""
A2A 표준 메시지 형식

에이전트 간 통신을 위한 표준화된 메시지 구조
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import uuid
from enum import Enum


class MessageType(str, Enum):
    """메시지 타입 정의"""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    BROADCAST = "broadcast"


class Priority(str, Enum):
    """메시지 우선순위"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageHeader(BaseModel):
    """메시지 헤더"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    sender_id: str
    receiver_id: Optional[str] = None  # None이면 브로드캐스트
    message_type: MessageType
    protocol_version: str = "1.0"
    correlation_id: Optional[str] = None  # 요청-응답 연결용
    reply_to: Optional[str] = None  # 응답 받을 엔드포인트
    
    
class MessageMetadata(BaseModel):
    """메시지 메타데이터"""
    priority: Priority = Priority.NORMAL
    ttl: Optional[int] = None  # Time to live in seconds
    retry_count: int = 0
    max_retries: int = 3
    require_ack: bool = False
    tags: List[str] = []
    

class A2AMessage(BaseModel):
    """A2A 표준 메시지"""
    header: MessageHeader
    body: Dict[str, Any]
    metadata: MessageMetadata = Field(default_factory=MessageMetadata)
    
    def to_dict(self) -> Dict:
        """메시지를 딕셔너리로 변환"""
        return {
            "header": {
                "message_id": self.header.message_id,
                "timestamp": self.header.timestamp.isoformat(),
                "sender_id": self.header.sender_id,
                "receiver_id": self.header.receiver_id,
                "message_type": self.header.message_type.value,
                "protocol_version": self.header.protocol_version,
                "correlation_id": self.header.correlation_id,
                "reply_to": self.header.reply_to
            },
            "body": self.body,
            "metadata": {
                "priority": self.metadata.priority.value,
                "ttl": self.metadata.ttl,
                "retry_count": self.metadata.retry_count,
                "max_retries": self.metadata.max_retries,
                "require_ack": self.metadata.require_ack,
                "tags": self.metadata.tags
            }
        }
        
    @classmethod
    def create_request(
        cls,
        sender_id: str,
        receiver_id: str,
        action: str,
        payload: Dict[str, Any],
        **kwargs
    ) -> "A2AMessage":
        """요청 메시지 생성 헬퍼"""
        header = MessageHeader(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=MessageType.REQUEST,
            **kwargs
        )
        
        body = {
            "action": action,
            "payload": payload
        }
        
        return cls(header=header, body=body)
        
    @classmethod
    def create_response(
        cls,
        original_message: "A2AMessage",
        sender_id: str,
        result: Any,
        success: bool = True,
        **kwargs
    ) -> "A2AMessage":
        """응답 메시지 생성 헬퍼"""
        header = MessageHeader(
            sender_id=sender_id,
            receiver_id=original_message.header.sender_id,
            message_type=MessageType.RESPONSE,
            correlation_id=original_message.header.message_id,
            **kwargs
        )
        
        body = {
            "success": success,
            "result": result,
            "original_action": original_message.body.get("action")
        }
        
        return cls(header=header, body=body)
        
    @classmethod
    def create_error(
        cls,
        sender_id: str,
        receiver_id: str,
        error_code: str,
        error_message: str,
        correlation_id: Optional[str] = None,
        **kwargs
    ) -> "A2AMessage":
        """에러 메시지 생성 헬퍼"""
        header = MessageHeader(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=MessageType.ERROR,
            correlation_id=correlation_id,
            **kwargs
        )
        
        body = {
            "error_code": error_code,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat()
        }
        
        return cls(header=header, body=body)
        
    @classmethod
    def create_event(
        cls,
        sender_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        **kwargs
    ) -> "A2AMessage":
        """이벤트 메시지 생성 헬퍼"""
        header = MessageHeader(
            sender_id=sender_id,
            receiver_id=None,  # 브로드캐스트
            message_type=MessageType.EVENT,
            **kwargs
        )
        
        body = {
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": datetime.now().isoformat()
        }
        
        return cls(header=header, body=body)
        
    def is_expired(self) -> bool:
        """메시지 만료 여부 확인"""
        if self.metadata.ttl is None:
            return False
            
        age = (datetime.now() - self.header.timestamp).total_seconds()
        return age > self.metadata.ttl
        
    def should_retry(self) -> bool:
        """재시도 가능 여부 확인"""
        return self.metadata.retry_count < self.metadata.max_retries
        
    def increment_retry(self) -> None:
        """재시도 카운트 증가"""
        self.metadata.retry_count += 1