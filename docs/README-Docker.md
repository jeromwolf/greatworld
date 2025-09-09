# StockAI Docker 배포 가이드

## 개요
StockAI 프로젝트를 Docker로 컨테이너화하여 쉽게 배포하고 관리할 수 있도록 구성했습니다.

## 아키텍처
```
┌─────────────────────────────────────────────────────┐
│                   Nginx (Port 80)                   │
├─────────────────────┬───────────────────────────────┤
│   FastAPI (8200)    │      Next.js (3200)          │
├─────────────────────┴───────────────────────────────┤
│              StockAI Application                     │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │   Agents    │  │     API     │  │  Frontend  │ │
│  └─────────────┘  └─────────────┘  └────────────┘ │
├─────────────────────┬───────────────────────────────┤
│  PostgreSQL (5432)  │       Redis (6379)           │
└─────────────────────┴───────────────────────────────┘
```

## 필요 사항
- Docker Engine 20.10+
- Docker Compose 2.0+
- 최소 4GB RAM
- 10GB 여유 디스크 공간

## 빠른 시작

### 1. 환경 변수 설정
```bash
# .env.docker를 .env로 복사
cp .env.docker .env

# 필수 API 키 설정
# GEMINI_API_KEY, DART_API_KEY 등을 실제 값으로 변경
nano .env
```

### 2. 프로덕션 배포
```bash
# 전체 스택 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 상태 확인
docker-compose ps
```

### 3. 개발 환경
```bash
# 개발 모드로 실행 (hot reload 지원)
docker-compose -f docker-compose.yml -f docker-compose.override.yml up

# 특정 서비스만 재시작
docker-compose restart stockai
```

## 접속 방법
- **메인 애플리케이션**: http://localhost
- **FastAPI 직접 접속**: http://localhost:8200
- **Next.js 직접 접속**: http://localhost:3200
- **API 문서**: http://localhost:8200/docs

## 주요 Docker 구성

### Multi-Stage Build
1. **backend-builder**: Python 의존성 설치
2. **frontend-builder**: Next.js 빌드
3. **runtime**: 최종 실행 이미지 (경량화)

### 서비스 구성
- **stockai**: 메인 애플리케이션 (FastAPI + Next.js)
- **postgres**: PostgreSQL 데이터베이스
- **redis**: Redis 캐시 서버
- **nginx**: 리버스 프록시 (선택사항)

### 볼륨 마운트
- `./logs`: 애플리케이션 로그
- `./data`: 데이터 파일
- `postgres_data`: PostgreSQL 데이터
- `redis_data`: Redis 데이터

## 운영 명령어

### 컨테이너 관리
```bash
# 전체 중지
docker-compose down

# 데이터 포함 전체 삭제
docker-compose down -v

# 이미지 재빌드
docker-compose build --no-cache

# 특정 서비스만 재빌드
docker-compose build stockai
```

### 로그 및 모니터링
```bash
# 실시간 로그
docker-compose logs -f stockai

# 최근 100줄 로그
docker-compose logs --tail=100

# 컨테이너 리소스 사용량
docker stats
```

### 백업 및 복원
```bash
# PostgreSQL 백업
docker exec stockai-postgres pg_dump -U stockai stockai > backup.sql

# PostgreSQL 복원
docker exec -i stockai-postgres psql -U stockai stockai < backup.sql

# 전체 볼륨 백업
docker run --rm -v greatworld_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

## 환경별 설정

### 프로덕션
```yaml
# docker-compose.yml 사용
- 최적화된 이미지
- 리소스 제한 설정
- 헬스체크 활성화
```

### 개발
```yaml
# docker-compose.override.yml 자동 적용
- 소스 코드 마운트
- Hot reload 활성화
- 디버그 모드
```

### 스테이징
```bash
# 별도 override 파일 사용
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up
```

## 트러블슈팅

### 포트 충돌
```bash
# 사용 중인 포트 확인
netstat -tulpn | grep -E '(80|8200|3200|5432|6379)'

# docker-compose.yml에서 포트 변경
ports:
  - "8080:80"  # 80 → 8080으로 변경
```

### 메모리 부족
```bash
# Docker 메모리 할당 증가 (Docker Desktop)
# Preferences → Resources → Memory: 4GB 이상

# 컨테이너별 메모리 제한
deploy:
  resources:
    limits:
      memory: 2G
```

### 빌드 실패
```bash
# 캐시 삭제 후 재빌드
docker system prune -a
docker-compose build --no-cache
```

### 권한 문제
```bash
# 로그 디렉토리 권한 설정
sudo chown -R 1000:1000 logs/
```

## 보안 고려사항

1. **환경 변수**
   - `.env` 파일은 절대 커밋하지 않음
   - 프로덕션에서는 Docker secrets 사용 권장

2. **네트워크**
   - 내부 서비스는 외부 노출 최소화
   - 필요시 방화벽 규칙 설정

3. **SSL/TLS**
   - 프로덕션에서는 Let's Encrypt 인증서 사용
   - nginx-proxy.conf에서 SSL 설정 활성화

## 성능 최적화

1. **이미지 크기**
   - Multi-stage build로 최종 이미지 경량화
   - 불필요한 파일은 .dockerignore에 추가

2. **캐싱**
   - Docker 레이어 캐싱 활용
   - pip, npm 캐시 최적화

3. **리소스 관리**
   - CPU/메모리 제한 설정
   - 헬스체크로 자동 재시작

## 모니터링 도구 추가 (선택사항)

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    # ... 설정
  
  grafana:
    image: grafana/grafana
    # ... 설정
```

## 문제 발생 시 연락처
- 개발자: 켈리
- 프로젝트: https://github.com/[repository]
- 이슈 트래커: https://github.com/[repository]/issues