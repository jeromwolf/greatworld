"""
주가 데이터 캐싱 시스템
Redis 또는 메모리 기반 캐싱
"""

import json
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import asdict
import os


class PriceCache:
    """주가 데이터 캐싱 클래스"""
    
    def __init__(self):
        self.memory_cache: Dict[str, Dict] = {}  # 메모리 캐시
        self.cache_ttl = {
            "realtime": 10,      # 실시간 주가: 10초
            "daily": 300,        # 일봉: 5분
            "history": 3600,     # 히스토리: 1시간
            "indicator": 600     # 기술지표: 10분
        }
        print("[CACHE] Using in-memory cache")
            
    def _get_cache_key(self, stock: str, data_type: str = "realtime") -> str:
        """캐시 키 생성"""
        return f"stockai:price:{data_type}:{stock}"
        
    async def get(self, stock: str, data_type: str = "realtime") -> Optional[Dict]:
        """캐시에서 데이터 조회"""
        key = self._get_cache_key(stock, data_type)
        
        # 메모리 캐시
        if key in self.memory_cache:
            cached = self.memory_cache[key]
            if datetime.fromisoformat(cached["expires_at"]) > datetime.now():
                return cached["data"]
            else:
                del self.memory_cache[key]
                    
        return None
        
    async def set(self, stock: str, data: Dict, data_type: str = "realtime"):
        """캐시에 데이터 저장"""
        key = self._get_cache_key(stock, data_type)
        ttl = self.cache_ttl.get(data_type, 60)
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        cache_data = {
            "data": data,
            "cached_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat()
        }
        
        # 메모리 캐시
        self.memory_cache[key] = cache_data
        
        # 메모리 캐시 크기 제한 (최대 1000개)
        if len(self.memory_cache) > 1000:
            # 가장 오래된 항목 삭제
            oldest_key = min(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k]["cached_at"]
            )
            del self.memory_cache[oldest_key]
                
    async def invalidate(self, stock: str, data_type: Optional[str] = None):
        """특정 종목의 캐시 무효화"""
        if data_type:
            # 특정 타입만 삭제
            key = self._get_cache_key(stock, data_type)
            if key in self.memory_cache:
                del self.memory_cache[key]
        else:
            # 해당 종목의 모든 캐시 삭제
            keys_to_delete = [
                k for k in self.memory_cache.keys()
                if k.endswith(f":{stock}")
            ]
            for key in keys_to_delete:
                del self.memory_cache[key]
                
    async def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        return {
            "type": "memory",
            "memory_cache_size": len(self.memory_cache),
            "cache_items": list(self.memory_cache.keys())[:10]  # 처음 10개만
        }


# 전역 캐시 인스턴스
price_cache = PriceCache()


# 캐시 데코레이터
def cache_price_data(data_type: str = "realtime"):
    """주가 데이터 캐싱 데코레이터"""
    def decorator(func):
        async def wrapper(self, stock_name: str, *args, **kwargs):
            # 캐시 확인
            cached = await price_cache.get(stock_name, data_type)
            if cached:
                print(f"[CACHE HIT] {stock_name} - {data_type}")
                return cached
                
            # 캐시 미스 - 실제 데이터 조회
            print(f"[CACHE MISS] {stock_name} - {data_type}")
            result = await func(self, stock_name, *args, **kwargs)
            
            # 성공한 경우만 캐싱
            if result.get("status") == "success":
                await price_cache.set(stock_name, result, data_type)
                
            return result
        return wrapper
    return decorator