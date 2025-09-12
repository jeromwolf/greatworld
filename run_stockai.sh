#!/bin/bash

# StockAI 간편 실행 스크립트
# NLU 에이전트 개선 버전 실행

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 포트 8200에서 실행 중인 프로세스 종료
kill_existing() {
    local pid=$(lsof -ti:8200 2>/dev/null || true)
    if [ ! -z "$pid" ]; then
        log "기존 서버 종료 중 (PID: $pid)"
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi
}

# 의존성 설치
install_deps() {
    log "필수 패키지 설치 중..."
    
    # pip 업그레이드
    python3 -m pip install --upgrade pip --quiet
    
    # 핵심 의존성만 설치
    python3 -m pip install fastapi==0.109.0 --quiet
    python3 -m pip install uvicorn[standard]==0.27.0 --quiet
    python3 -m pip install python-dotenv==1.0.0 --quiet
    python3 -m pip install pydantic==2.5.3 --quiet
    python3 -m pip install dataclasses-json==0.6.3 --quiet
    python3 -m pip install websockets==12.0 --quiet
    python3 -m pip install aiohttp==3.9.1 --quiet
    python3 -m pip install requests==2.31.0 --quiet
    python3 -m pip install python-dateutil==2.8.2 --quiet
    python3 -m pip install beautifulsoup4==4.12.3 --quiet
    
    success "필수 패키지 설치 완료"
}

# NLU 에이전트 테스트
test_nlu() {
    log "NLU 에이전트 테스트 중..."
    
    python3 -c "
from agents.simple_nlu_agent import SimpleNLUAgent
nlu = SimpleNLUAgent()
result = nlu.analyze_query('삼성전자 vs Apple 분석해줘')
print('✅ 종목:', result['entities']['stocks'])
print('✅ 의도:', result['intent']) 
print('✅ 신뢰도:', f\"{result['confidence']:.3f}\")
"
    
    if [ $? -eq 0 ]; then
        success "NLU 에이전트 정상 작동 확인"
    else
        error "NLU 에이전트 오류 발생"
        exit 1
    fi
}

# 서버 시작
start_server() {
    log "StockAI 서버 시작 중..."
    
    # 백그라운드에서 서버 실행
    nohup python3 -m uvicorn api.main:app --reload --port 8200 > stockai.log 2>&1 &
    
    sleep 3
    
    # 서버 실행 확인
    if lsof -i:8200 > /dev/null 2>&1; then
        success "StockAI 서버가 실행되었습니다!"
        echo ""
        echo "🌐 접속 URL:"
        echo "  - 메인 UI: http://localhost:8200"
        echo "  - API 문서: http://localhost:8200/docs"
        echo ""
        echo "📝 로그 확인: tail -f stockai.log"
        echo "🛑 서버 중지: kill \$(lsof -ti:8200)"
    else
        error "서버 시작 실패. 로그를 확인하세요: cat stockai.log"
        exit 1
    fi
}

# 메인 실행
main() {
    echo ""
    echo "🚀 StockAI - 개선된 NLU 에이전트 버전"
    echo "======================================="
    echo ""
    
    # 기존 프로세스 종료
    kill_existing
    
    # Python 버전 확인
    if ! command -v python3 &> /dev/null; then
        error "Python 3가 설치되지 않았습니다"
        exit 1
    fi
    
    # 의존성 설치
    install_deps
    
    # NLU 에이전트 테스트
    test_nlu
    
    # 서버 시작
    start_server
}

# 옵션 처리
case "$1" in
    stop)
        log "서버 중지 중..."
        kill_existing
        success "서버가 중지되었습니다"
        ;;
    test)
        test_nlu
        ;;
    *)
        main
        ;;
esac