# StockAI 프로젝트 가이드

## 프로젝트 개요
StockAI는 AI 기반 주식 분석 서비스로, 국내외 주식에 대한 실시간 분석을 제공하는 챗봇 형태의 플랫폼입니다. A2A 멀티 에이전트 시스템을 기반으로 구축되었습니다.

## 프로젝트 구조
```
greatWorld/
├── PRD_AI_Stock_Analysis.md          # 제품 요구사항 문서
├── StockAI_Business_Model_Canvas.md  # 비즈니스 모델 캔버스
├── StockAI_Development_Tasks.md      # 개발 태스크 분해
├── CLAUDE.md                         # 프로젝트 가이드 (현재 파일)
├── agents/                           # A2A 기반 에이전트들
│   ├── nlu_agent.py                 # 자연어 이해
│   ├── dart_agent.py                # 국내 공시 수집
│   ├── sec_agent.py                 # 해외 공시 수집
│   ├── sentiment_agent.py           # 감성 분석
│   └── financial_agent.py           # 재무 분석
├── a2a_core/                        # A2A 프로토콜 핵심
├── frontend/                        # 웹 UI
│   ├── index.html                   # 메인 채팅 인터페이스
│   ├── dashboard.html               # 대시보드
│   └── static/                      # CSS/JS
├── api/                             # FastAPI 백엔드
│   ├── main.py                      # 메인 앱
│   ├── routers/                     # API 라우터
│   └── models/                      # 데이터 모델
└── tests/                           # 테스트 코드
```

## 핵심 기술 스택
- **백엔드**: Python 3.8+, FastAPI
- **AI**: Gemini AI (주 엔진), GPT-4 (보조)
- **실시간 통신**: WebSocket
- **데이터베이스**: PostgreSQL, Redis
- **아키텍처**: A2A 멀티 에이전트 시스템

## 주요 기능
1. **대화형 주식 분석**: 자연어로 질문하면 AI가 분석 제공
2. **국내/해외 통합**: DART, SEC 등 다양한 소스 통합
3. **실시간 감성 분석**: Reddit, X 등 SNS 모니터링
4. **가중치 시스템**: 데이터 소스별 신뢰도 반영

## 데이터 소스 및 가중치
- 공시 데이터 (DART/SEC): 1.5
- 재무 데이터: 1.2
- 뉴스: 1.0
- SNS: 0.5-0.8

## 개발 가이드라인
1. **에이전트 개발**
   - 각 에이전트는 독립적으로 동작
   - A2A 프로토콜로 통신
   - 비동기 처리 필수

2. **프롬프트 엔지니어링**
   - Gemini AI 사용 시 구조화된 JSON 응답 요구
   - 감성 점수는 -1.0 ~ 1.0 범위
   - 한국어/영어 모두 지원

3. **API 설계**
   - RESTful + WebSocket 하이브리드
   - JWT 인증 사용
   - Rate limiting 적용

4. **포트 설정**
   - FastAPI: 8200
   - Next.js: 3200
   - WebSocket: ws://localhost:8200/ws

## 현재 진행 상황 (2025-08-28 → 2025-08-29 업데이트)
- [x] PRD 작성 완료
- [x] BMC 작성 완료
- [x] 개발 태스크 분해 완료
- [x] A2A 코드베이스 Fork 및 정리 완료
- [x] 프로젝트 구조 설정 완료
- [x] Simple NLU Agent 구현 완료
  - 자연어 쿼리 파싱 기능
  - 의도 분류: analyze_stock, compare_stocks, get_sentiment, get_financials, get_news
  - 엔티티 추출: 한국/미국 주식명, 티커, 기간
  - 한글/영어 쿼리 지원
  - 신뢰도 점수 계산
- [x] **데이터 수집 에이전트 개발 완료** (2025-08-29)
  - DART Agent: 한국 공시 데이터 수집
  - SEC Agent: 미국 공시 데이터 수집  
  - News Agent: 뉴스 데이터 수집
  - Social Agent: SNS 데이터 수집 (Reddit, StockTwits)
- [x] **Sentiment Analysis Agent 개발 완료** (2025-08-29)
  - 다중 데이터 소스 통합 분석
  - 가중치 기반 감성 점수 계산
  - Gemini AI 통합 (옵션)
- [x] **WebSocket 챗봇 UI 개선** (2025-08-29)
  - 실시간 주식 분석 기능 추가
  - 감성 점수 시각화
  - 마크다운 렌더링 지원
- [x] MVP 개발 완료
- [x] **서버 연결 문제 해결** (2025-08-29)
  - social_agent.py f-string 백슬래시 오류 수정 (lines 150, 427, 432 등)
  - WebSocket 재연결 로직 강화 (지수 백오프, 최대 5회 시도)
  - 서버 상태 확인 및 정상 동작 확인
- [x] **데이터 소스 투명성 구현** (2025-08-29)
  - 모든 에이전트에 `data_source` 필드 추가 (REAL_DATA/MOCK_DATA)
  - API main.py에서 데이터 소스 요약 및 신뢰도 표시
  - 모의 데이터 사용 시 한글 경고 메시지 표시
  - 실제 API vs 모의 데이터 명확한 구분

## 완료된 파일
### Backend (Python/FastAPI)
- `agents/simple_nlu_agent.py`: 자연어 이해 에이전트 (독립 실행형)
- `agents/nlu_agent.py`: A2A 기반 자연어 이해 에이전트 (추후 통합용)
- `agents/dart_agent.py`: DART 공시 데이터 수집 에이전트 (data_source 필드 포함)
- `agents/sec_agent.py`: SEC 공시 데이터 수집 에이전트 (data_source 필드 포함)
- `agents/news_agent.py`: 뉴스 데이터 수집 에이전트 (data_source 필드 포함)
- `agents/social_agent.py`: 소셜 미디어 데이터 수집 에이전트 (data_source 필드 포함)
- `agents/sentiment_agent.py`: 감성 분석 통합 에이전트 (data_source 필드 포함)
- `api/main.py`: FastAPI 백엔드 (에이전트 통합, 데이터 소스 요약 표시)
- `requirements.txt`: 프로젝트 의존성 정의
- `.env.example`: 환경 변수 템플릿
- `restart.sh`: 서비스 자동 시작/중지 스크립트

### Frontend (Vanilla JS)
- `frontend/static/app.js`: 개선된 채팅 UI
- `frontend/static/style.css`: 감성 시각화 추가
- `frontend/index.html`: 메인 채팅 인터페이스

### Frontend (Next.js) - 완료
- `stockai-frontend/types/chat.ts`: 타입 정의 업데이트 완료 (AnalysisData, SentimentSource 추가)
- `stockai-frontend/components/chat/ChatContainer.tsx`: WebSocket 연동 업데이트, 연결 상태 표시 추가
- `stockai-frontend/components/chat/ChatMessage.tsx`: 감성 분석 표시 추가, 마크다운 렌더링
- `stockai-frontend/components/chat/SentimentIndicator.tsx`: 감성 점수 시각화 컴포넌트 신규 생성
- `stockai-frontend/hooks/useWebSocket.ts`: 재연결 로직 개선 (백오프 전략, 최대 5회 시도)
- `stockai-frontend/app/page.tsx`: ChatContainer 연결
- `stockai-frontend/app/layout.tsx`: 메타데이터 업데이트
- `stockai-frontend/package.json`: Next.js 포트 3200 설정

### 최신 업데이트 (2025-08-29)
**데이터 소스 투명성 개선:**
- 모든 에이전트 응답에 `data_source: "REAL_DATA"/"MOCK_DATA"` 필드 추가
- 모의 데이터 사용 시 "⚠️ 모의 데이터 - API 키가 설정되지 않음" 한글 경고
- API 통합 응답에 데이터 신뢰도 레벨 표시 (고신뢰도/혼합/저신뢰도/데이터없음)
- 서버 연결 문제 해결 및 WebSocket 안정성 개선

## 실행 방법

### Backend 실행
```bash
# Python 가상환경 활성화
source venv/bin/activate  # Windows: venv\Scripts\activate

# FastAPI 서버 실행
uvicorn api.main:app --reload --port 8200
```

### Frontend 실행 (Next.js)
```bash
# 별도 터미널에서
cd stockai-frontend
npm install
npm run dev
```

### 자동 실행 (권장)
```bash
# 모든 서비스 시작
./restart.sh

# 상태 확인
./restart.sh status
```

### 접속
- Next.js UI: http://localhost:3200 (권장)
- 기본 UI: http://localhost:8200
- API 문서: http://localhost:8200/docs

## 다음 단계 (2025-08-30 예정)
1. **Financial Agent 개발**
   - 재무제표 분석
   - 기술적 지표 계산
   - 동종업계 비교

2. **차트 및 시각화**
   - 실시간 주가 차트
   - 감성 트렌드 그래프
   - 포트폴리오 대시보드

3. **A2A 시스템 통합**
   - 에이전트 간 비동기 통신
   - 메시지 큐 구현
   - 확장성 개선

4. **고급 기능**
   - 실시간 알림 시스템
   - PDF 리포트 생성
   - 다국어 지원 (한/영/중/일)

## 개발 메모
- A2A 코어 시스템은 `/a2a_core`에 위치
- 현재는 Simple NLU Agent로 독립적으로 테스트 중
- 추후 모든 에이전트를 A2A 시스템으로 통합 예정

## 테스트 및 검증 명령어
```bash
# 프로젝트 설정
git clone [repository]
cd greatWorld
pip install -r requirements.txt

# 개발 서버 실행
uvicorn api.main:app --reload --port 8200

# 또는 자동 스크립트 사용
./restart.sh

# 테스트 실행
pytest tests/

# 코드 품질 검사
ruff check .
mypy .
```

## 주의사항
1. **규제 준수**: 투자 권유가 아닌 정보 제공 서비스로 포지셔닝
2. **API 비용 관리**: Gemini AI 호출 최적화 필수
3. **데이터 정확성**: 복수 소스 교차 검증
4. **개인정보 보호**: 사용자 데이터 암호화 저장

## 문의 및 지원
- 개발자: 켈리
- 이메일: [추가 필요]
- GitHub: [repository URL]

## 라이선스
[라이선스 정보 추가 필요]