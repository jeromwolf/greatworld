#!/bin/bash

# StockAI 재시작 스크립트
# 사용법: ./restart.sh [backend|frontend|all]

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 로그 함수
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
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

# 프로세스 종료 함수
kill_process_on_port() {
    local port=$1
    local pid=$(lsof -ti:$port)
    
    if [ ! -z "$pid" ]; then
        log "포트 $port 에서 실행 중인 프로세스 종료 (PID: $pid)"
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi
}

# Backend 재시작
restart_backend() {
    log "FastAPI 백엔드 재시작 중..."
    
    # 기존 프로세스 종료
    kill_process_on_port 8200
    
    # 가상환경 확인
    if [ ! -d "$PROJECT_ROOT/venv" ]; then
        error "Python 가상환경이 없습니다. 먼저 설치하세요:"
        echo "  python -m venv venv"
        echo "  source venv/bin/activate"
        echo "  pip install -r requirements.txt"
        exit 1
    fi
    
    # 백엔드 시작
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    
    log "FastAPI 서버 시작 (포트: 8200)..."
    # .env 파일의 환경변수를 명시적으로 export
    set -a
    source .env
    set +a
    nohup uvicorn api.main:app --reload --port 8200 > logs/backend.log 2>&1 &
    
    sleep 2
    
    # 실행 확인
    if lsof -i:8200 > /dev/null 2>&1; then
        success "백엔드가 포트 8200에서 실행 중입니다"
        echo "로그 확인: tail -f $PROJECT_ROOT/logs/backend.log"
    else
        error "백엔드 시작 실패"
        exit 1
    fi
}

# Frontend 재시작
restart_frontend() {
    log "Next.js 프론트엔드 재시작 중..."
    
    # 기존 프로세스 종료
    kill_process_on_port 3200
    
    # node_modules 확인
    if [ ! -d "$PROJECT_ROOT/stockai-frontend/node_modules" ]; then
        warning "node_modules가 없습니다. npm install 실행 중..."
        cd "$PROJECT_ROOT/stockai-frontend"
        npm install
    fi
    
    # 프론트엔드 시작
    cd "$PROJECT_ROOT/stockai-frontend"
    
    log "Next.js 서버 시작 (포트: 3200)..."
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    
    sleep 3
    
    # 실행 확인
    if lsof -i:3200 > /dev/null 2>&1; then
        success "프론트엔드가 포트 3200에서 실행 중입니다"
        echo "로그 확인: tail -f $PROJECT_ROOT/logs/frontend.log"
    else
        error "프론트엔드 시작 실패"
        exit 1
    fi
}

# 상태 확인
check_status() {
    log "서비스 상태 확인 중..."
    echo ""
    
    # Backend 상태
    if lsof -i:8200 > /dev/null 2>&1; then
        echo -e "  백엔드 (FastAPI):  ${GREEN}● 실행 중${NC} (포트 8200)"
    else
        echo -e "  백엔드 (FastAPI):  ${RED}● 중지됨${NC}"
    fi
    
    # Frontend 상태
    if lsof -i:3200 > /dev/null 2>&1; then
        echo -e "  프론트엔드 (Next.js): ${GREEN}● 실행 중${NC} (포트 3200)"
    else
        echo -e "  프론트엔드 (Next.js): ${RED}● 중지됨${NC}"
    fi
    
    echo ""
    echo "접속 URL:"
    echo "  - Next.js UI: http://localhost:3200"
    echo "  - 기본 UI: http://localhost:8200"
    echo "  - API 문서: http://localhost:8200/docs"
}

# 로그 디렉토리 생성
mkdir -p "$PROJECT_ROOT/logs"

# 메인 로직
case "$1" in
    backend)
        restart_backend
        ;;
    frontend)
        restart_frontend
        ;;
    all|"")
        restart_backend
        restart_frontend
        echo ""
        check_status
        ;;
    status)
        check_status
        ;;
    stop)
        log "모든 서비스 중지 중..."
        kill_process_on_port 8200
        kill_process_on_port 3200
        success "모든 서비스가 중지되었습니다"
        ;;
    *)
        echo "사용법: $0 [backend|frontend|all|status|stop]"
        echo ""
        echo "옵션:"
        echo "  backend   - FastAPI 백엔드만 재시작"
        echo "  frontend  - Next.js 프론트엔드만 재시작"
        echo "  all       - 모든 서비스 재시작 (기본값)"
        echo "  status    - 서비스 상태 확인"
        echo "  stop      - 모든 서비스 중지"
        exit 1
        ;;
esac