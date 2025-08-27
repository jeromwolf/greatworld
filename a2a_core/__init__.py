"""
A2A (Agent-to-Agent) Core Framework

진정한 에이전트 간 협업을 위한 핵심 프레임워크
"""

__version__ = "1.0.0"
__author__ = "A2A Sentiment Analysis Team"

from .protocols.message import A2AMessage
from .registry.service_registry import ServiceRegistry
from .base.base_agent import BaseAgent

__all__ = ["A2AMessage", "ServiceRegistry", "BaseAgent"]