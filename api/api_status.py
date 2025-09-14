"""
API 상태 확인 및 관리 모듈
각 API의 활성화 상태와 설정 가이드 제공
"""

import os
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

class APIStatusChecker:
    """API 상태 확인 클래스"""

    def __init__(self):
        self.api_configs = {
            "DART": {
                "key_name": "DART_API_KEY",
                "name": "DART (한국 공시)",
                "url": "https://opendart.fss.or.kr/",
                "description": "한국 상장기업 재무제표, 공시정보",
                "features": ["재무제표", "대주주현황", "공시정보", "기업개황"],
                "required_for": ["한국 주식 재무 분석"]
            },
            "NewsAPI": {
                "key_name": "NEWSAPI_KEY",
                "name": "NewsAPI (글로벌 뉴스)",
                "url": "https://newsapi.org/",
                "description": "전 세계 뉴스 데이터",
                "features": ["실시간 뉴스", "과거 뉴스 검색", "다국어 지원"],
                "required_for": ["뉴스 감성 분석", "시장 동향 파악"]
            },
            "Naver": {
                "key_name": ["NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET"],
                "name": "네이버 API (한국 뉴스)",
                "url": "https://developers.naver.com/",
                "description": "네이버 뉴스 검색",
                "features": ["한국 뉴스", "블로그", "카페"],
                "required_for": ["한국 주식 뉴스 분석"]
            },
            "Alpha Vantage": {
                "key_name": "ALPHA_VANTAGE_API_KEY",
                "name": "Alpha Vantage (기술적 분석)",
                "url": "https://www.alphavantage.co/",
                "description": "기술적 지표 계산",
                "features": ["RSI", "MACD", "볼린저밴드", "이동평균선"],
                "required_for": ["기술적 분석", "매매 신호"]
            },
            "Finnhub": {
                "key_name": "FINNHUB_API_KEY",
                "name": "Finnhub (미국 주식)",
                "url": "https://finnhub.io/",
                "description": "미국 주식 실시간 데이터",
                "features": ["실시간 주가", "기업 정보", "내부자 거래"],
                "required_for": ["미국 주식 분석"]
            },
            "Reddit": {
                "key_name": ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"],
                "name": "Reddit API (소셜 감성)",
                "url": "https://www.reddit.com/dev/api/",
                "description": "Reddit 투자 커뮤니티 분석",
                "features": ["WSB 감성", "투자자 심리", "트렌드"],
                "required_for": ["소셜 미디어 감성 분석"]
            }
        }

    def check_api_status(self) -> Dict:
        """모든 API 상태 확인"""
        status = {
            "configured": [],
            "not_configured": [],
            "total": len(self.api_configs),
            "details": {}
        }

        for api_name, config in self.api_configs.items():
            key_names = config["key_name"] if isinstance(config["key_name"], list) else [config["key_name"]]

            # 모든 키가 설정되어 있는지 확인
            all_keys_set = True
            for key_name in key_names:
                key_value = os.getenv(key_name, "")
                if not key_value or "your_" in key_value.lower():
                    all_keys_set = False
                    break

            is_configured = all_keys_set

            if is_configured:
                status["configured"].append(api_name)
            else:
                status["not_configured"].append(api_name)

            status["details"][api_name] = {
                "configured": is_configured,
                "name": config["name"],
                "url": config["url"],
                "description": config["description"],
                "features": config["features"],
                "required_for": config["required_for"]
            }

        status["configured_count"] = len(status["configured"])
        status["not_configured_count"] = len(status["not_configured"])
        status["configuration_rate"] = f"{(status['configured_count'] / status['total'] * 100):.0f}%"

        return status

    def get_registration_guide(self, api_name: str) -> Dict:
        """특정 API 등록 가이드"""
        if api_name not in self.api_configs:
            return {"error": "알 수 없는 API입니다"}

        config = self.api_configs[api_name]

        if api_name == "DART":
            return {
                "name": config["name"],
                "steps": [
                    f"1. {config['url']} 접속",
                    "2. 회원가입 (이메일 인증 필요)",
                    "3. 로그인 후 '인증키 신청' 메뉴 클릭",
                    "4. 신청서 작성 (즉시 발급)",
                    "5. 발급받은 API 키를 .env 파일의 DART_API_KEY에 입력",
                    "6. 서버 재시작"
                ],
                "example": "DART_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            }
        elif api_name == "NewsAPI":
            return {
                "name": config["name"],
                "steps": [
                    f"1. {config['url']} 접속",
                    "2. 'Get API Key' 클릭",
                    "3. 이메일로 회원가입",
                    "4. 무료 플랜 선택 (월 500회 요청)",
                    "5. API 키 즉시 발급",
                    "6. .env 파일의 NEWSAPI_KEY에 입력"
                ],
                "example": "NEWSAPI_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            }
        elif api_name == "Naver":
            return {
                "name": config["name"],
                "steps": [
                    f"1. {config['url']} 접속",
                    "2. 네이버 로그인",
                    "3. '애플리케이션 등록' 클릭",
                    "4. 앱 이름 입력, 사용 API에서 '검색' 선택",
                    "5. 비로그인 오픈 API 서비스 환경에 'http://localhost' 입력",
                    "6. Client ID와 Client Secret 발급",
                    "7. .env 파일에 입력"
                ],
                "example": "NAVER_CLIENT_ID=xxxxx\nNAVER_CLIENT_SECRET=xxxxx"
            }
        elif api_name == "Alpha Vantage":
            return {
                "name": config["name"],
                "steps": [
                    f"1. {config['url']} 접속",
                    "2. 'Get your free API key' 클릭",
                    "3. 이메일 입력하여 회원가입",
                    "4. 무료 키 즉시 발급 (분당 5회, 일 500회 제한)",
                    "5. .env 파일의 ALPHA_VANTAGE_API_KEY에 입력"
                ],
                "example": "ALPHA_VANTAGE_API_KEY=xxxxxxxxxxxxxxxx"
            }
        elif api_name == "Finnhub":
            return {
                "name": config["name"],
                "steps": [
                    f"1. {config['url']} 접속",
                    "2. 'Sign up free' 클릭",
                    "3. 이메일로 회원가입",
                    "4. 무료 플랜 선택",
                    "5. API 키 즉시 발급",
                    "6. .env 파일의 FINNHUB_API_KEY에 입력"
                ],
                "example": "FINNHUB_API_KEY=xxxxxxxxxxxxxxxx"
            }
        elif api_name == "Reddit":
            return {
                "name": config["name"],
                "steps": [
                    "1. Reddit 계정으로 로그인",
                    f"2. {config['url']} 접속",
                    "3. 'Create App' 클릭",
                    "4. 앱 타입을 'script'로 선택",
                    "5. redirect uri에 'http://localhost:8080' 입력",
                    "6. Client ID (앱 이름 아래)와 Secret 확인",
                    "7. .env 파일에 입력"
                ],
                "example": "REDDIT_CLIENT_ID=xxxxx\nREDDIT_CLIENT_SECRET=xxxxx"
            }

        return {"error": f"{api_name}에 대한 가이드가 준비되지 않았습니다"}

    def get_quick_start_guide(self) -> str:
        """빠른 시작 가이드"""
        return """
# 🚀 StockAI API 설정 가이드

## 필수 API (최소한 이것만 설정하면 기본 기능 사용 가능)
1. **Yahoo Finance** - 이미 활성화됨 (API 키 불필요) ✅
   - 실시간 주가, 거래량, 시가총액

## 권장 API (더 풍부한 분석을 원한다면)
1. **DART** - 한국 주식 재무제표
2. **NewsAPI** 또는 **Naver** - 뉴스 감성 분석
3. **Alpha Vantage** - 기술적 분석 지표

## 설정 방법
1. 위 사이트에서 무료 API 키 발급
2. `.env` 파일 열기
3. 해당 API_KEY 값 입력
4. 서버 재시작: `./restart.sh`

## 현재 사용 가능한 기능
- ✅ 실시간 주가 조회 (Yahoo Finance)
- ✅ 기본 재무 지표 (하드코딩 데이터)
- ⚠️ 뉴스 분석 (API 키 필요)
- ⚠️ 기술적 분석 (API 키 필요)
- ⚠️ 재무제표 분석 (API 키 필요)
"""

    def get_data_source_summary(self) -> Dict:
        """현재 데이터 소스 요약"""
        status = self.check_api_status()

        return {
            "real_data_sources": [
                "Yahoo Finance (실시간 주가)",
                "RSS 피드 (기본 뉴스)"
            ] + [f"{name} ✅" for name in status["configured"]],
            "mock_data_sources": [
                f"{name} ⚠️" for name in status["not_configured"]
            ],
            "data_quality": {
                "주가": "실시간 (Yahoo Finance)",
                "뉴스": "제한적" if "NewsAPI" not in status["configured"] else "실시간",
                "재무제표": "하드코딩" if "DART" not in status["configured"] else "실시간",
                "기술적분석": "예측값" if "Alpha Vantage" not in status["configured"] else "실시간"
            }
        }