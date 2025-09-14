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

4. **포트 설정 및 프론트엔드 아키텍처**
   - **메인 개발**: Port 8200 (FastAPI + HTML Dashboard) 
   - **참고용**: Port 3200 (Next.js React)
   - WebSocket: ws://localhost:8200/ws
   
   **🎯 개발 방향 결정 (2025-08-29):**
   - **Port 8200이 더 완성도 높음** → 메인 개발 포트로 결정
   - FastAPI가 정적 파일도 서빙하는 통합 아키텍처
   - 단일 서버 실행으로 개발/배포 효율성 극대화
   - Next.js(3200)는 참고용으로 유지

## 현재 진행 상황 (2025-08-28 → 2025-08-29 → 2025-08-30 업데이트)
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
  - DART Agent: 한국 공시 데이터 수집 + 재무제표 파싱
  - SEC Agent: 미국 공시 데이터 수집  
  - News Agent: 뉴스 데이터 수집 + 핵심 정보 추출 (📈목표가, 💰실적, 🤝계약 등)
  - Social Agent: SNS 데이터 수집 (Reddit, StockTwits)
- [x] **Sentiment Analysis Agent 강화 완료** (2025-08-29)
  - A2A 방식 감성 분석 (가중치 0.8까지 대폭 상향)
  - 실행 가능한 투자 전략 제공 (매수 시점, 손절선, 포트폴리오 비중)
  - 시나리오별 리스크 관리 전략 (강세/중립/약세/위험 단계)
  - Gemini AI 통합 및 규칙 기반 분석
- [x] **Professional Dashboard UI 개발 완료** (2025-08-29)
  - 채팅 UI → 전문 투자 리포트 UI 전환
  - 뉴스 중요도 분류 (🚨즉시확인필요, 💡주요뉴스, 📌일반뉴스)
  - 실시간 주식 분석 결과 표시
  - 감성 점수 시각화 및 데이터 소스별 차트
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
- [x] **데이터 수집 기간 최적화** (2025-08-29)
  - PeriodConfig 클래스 구현으로 데이터별 차별화된 기간 설정
  - 뉴스: 7일 → 14일 (뉴스 시장 반영 시간 고려)
  - 공시: 90일 → 45일 (공시 영향력 지속성 반영)
  - 소셜: 7일 유지 (빠른 트렌드 변화)
  - 시간 가중치 감쇠 및 투자 스타일별 조정 기능 추가

## Phase 1: 데이터 인프라 구축 완료 (2025-08-30)
- [x] **Task 1.1: 실시간 주가 시스템**
  - `agents/price_agent.py`: Yahoo Finance API 연동
  - `cache/price_cache.py`: 메모리 기반 캐싱 시스템
  - `api/price_streamer.py`: WebSocket 실시간 스트리밍
  - 한국/미국 주식 심볼 자동 변환
- [x] **Task 1.2: 재무 데이터 파싱 엔진**
  - `agents/financial_agent.py`: DART API 재무제표 파싱
  - 재무 지표 계산: ROE, ROA, 부채비율, 유동비율 등
  - 재무 건전성 스코어링 시스템 (A-E 등급)
  - 투자 포인트 자동 생성
- [x] **Task 1.3: 기술적 분석 지표 계산**
  - `agents/technical_agent.py`: 기술적 분석 에이전트
  - 이동평균선 (MA5, MA20, MA60, MA120)
  - 모멘텀 지표: RSI, MACD, 볼린저밴드
  - 매매 신호 생성 및 신뢰도 계산
- [x] **Task 1.4: 뉴스 감성 스코어링 고도화**
  - `agents/advanced_sentiment_agent.py`: 도메인 특화 감성 분석
  - 금융 전문 용어 사전 구축
  - 컨텍스트별 가중치 (제목 2.0, 공시 1.8)
  - 부정어 처리 및 강조 표현 인식
- [x] **Task 1.5: 데이터 정규화 및 표준화**
  - `utils/data_normalizer.py`: 통합 데이터 정규화
  - 다양한 소스 데이터를 표준 형식으로 변환
  - 날짜/시간, 숫자, 통화 자동 파싱

## Phase 2: 사용자 인터페이스 개선 진행 중 (2025-08-30)
- [x] **Task 2.1: 반응형 웹 디자인 구현**
  - `frontend/static/responsive.css`: 모바일/태블릿/데스크톱 대응
  - `frontend/responsive.html`: 새로운 반응형 UI
  - 다크 모드 및 접근성 지원
  - 실시간 채팅 + 사이드바 레이아웃

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
- `config/period_config.py`: 데이터별 최적 수집 기간 설정 (신규)
- `period_optimization_analysis.md`: 기간 설정 분석 문서 (신규)
- `requirements.txt`: 프로젝트 의존성 정의
- `.env.example`: 환경 변수 템플릿
- `restart.sh`: 서비스 자동 시작/중지 스크립트

### Frontend (Professional Dashboard)
- `frontend/report.html`: 전문 투자 리포트 UI (메인)
- `frontend/static/report.js`: WebSocket 연동 및 뉴스 파싱 로직  
- `frontend/static/report.css`: 카테고리별 뉴스 스타일링 및 다크 테마
- `frontend/index.html`: 기본 채팅 인터페이스 (백업용)
- `api/professional_report_formatter.py`: 리포트 포맷팅 및 뉴스 분류 로직

### Frontend (Next.js) - 완료
- `stockai-frontend/types/chat.ts`: 타입 정의 업데이트 완료 (AnalysisData, SentimentSource 추가)
- `stockai-frontend/components/chat/ChatContainer.tsx`: WebSocket 연동 업데이트, 연결 상태 표시 추가
- `stockai-frontend/components/chat/ChatMessage.tsx`: 감성 분석 표시 추가, 마크다운 렌더링
- `stockai-frontend/components/chat/SentimentIndicator.tsx`: 감성 점수 시각화 컴포넌트 신규 생성
- `stockai-frontend/hooks/useWebSocket.ts`: 재연결 로직 개선 (백오프 전략, 최대 5회 시도)
- `stockai-frontend/app/page.tsx`: ChatContainer 연결
- `stockai-frontend/app/layout.tsx`: 메타데이터 업데이트
- `stockai-frontend/package.json`: Next.js 포트 3200 설정

### Phase 1 신규 파일 (2025-08-30)
- `agents/price_agent.py`: 실시간 주가 데이터 수집
- `agents/financial_agent.py`: 재무제표 분석 에이전트
- `agents/technical_agent.py`: 기술적 분석 에이전트
- `agents/advanced_sentiment_agent.py`: 고도화된 감성 분석
- `cache/price_cache.py`: 주가 캐싱 시스템
- `api/price_streamer.py`: WebSocket 스트리밍 관리
- `agents/price_tracker.py`: 주가 추적 및 알림
- `utils/data_normalizer.py`: 데이터 정규화 유틸리티
- `frontend/responsive.html`: 반응형 웹 인터페이스
- `frontend/static/responsive.css`: 반응형 스타일시트

### 최신 업데이트 (2025-08-29 완료)
**사용자 중심 투자 인사이트 시스템:**
- **실행 가능한 투자 전략**: 구체적 매수/매도 시점 (종가 -2% 하락시), 손절선 (-3%), 포트폴리오 비중 (5-10%)
- **뉴스 인텔리전스**: 핵심 정보 자동 추출 및 중요도별 분류 시스템
- **Professional UI**: 채팅 → 투자 리포트 형식으로 완전 전환
- **리스크 관리**: 시나리오별 대응 전략 및 주간 체크리스트 제공
- **데이터 품질**: 실제 DART/뉴스 데이터 활용 및 신뢰도 표시 시스템

## 실행 방법

### 메인 개발 환경 (권장)
```bash
# Python 가상환경 활성화
source venv/bin/activate  # Windows: venv\Scripts\activate

# FastAPI 서버 실행 (프론트엔드 포함)
uvicorn api.main:app --reload --port 8200
```

### 자동 실행 (권장)
```bash
# 모든 서비스 시작
./restart.sh

# 상태 확인
./restart.sh status
```

### Next.js 실행 (참고용)
```bash
# 별도 터미널에서
cd stockai-frontend
npm install
npm run dev
```

### 접속
- **메인 UI**: http://localhost:8200 ⭐️ **권장 - Professional Dashboard**
- 참고 UI: http://localhost:3200 (Next.js React)
- API 문서: http://localhost:8200/docs

**🎯 개발 우선순위:**
1. Port 8200 대시보드 기능 확장
2. `frontend/report.html`, `frontend/static/report.js` 중심 개발
3. 단일 서버 아키텍처로 배포 효율성 최대화

## 현재 작업 컨텍스트 (2025-09-14 업데이트)

### ✅ 최근 완료된 작업 (2025-09-14)

#### 해외 주식 분석 기능 완성
1. **US Stock Client 구현** (`agents/us_stock_client.py`)
   - 70+ 해외 주식 지원 (미국, 중국 ADR, 일본 ADR, 유럽)
   - Yahoo Finance API 연동 (실시간 데이터)
   - 섹터별 분류 및 ETF 지원

2. **실제 API 통합 시스템**
   - DART API Client: 한국 기업 재무제표
   - News API Client: 실시간 뉴스 수집
   - Alpha Vantage Client: 기술적 지표
   - API 상태 관리 시스템 (`api/api_status.py`)

3. **해외 주식 상세 분석 페이지**
   - `/foreign-stock` 라우트 추가
   - 실시간 차트 (가격 + 거래량)
   - 기술적 분석 (RSI, MACD, 이동평균선)
   - 애널리스트 의견 및 목표가
   - 투자 점수 시스템 (0-100점)

4. **다중 시장 지원**
   - 미국: AAPL, TSLA, NVDA, MSFT 등 30+
   - 중국 ADR: BABA, TCEHY, BIDU, NIO 등
   - 일본 ADR: TM, SONY, HMC, NTDOY
   - 유럽: ASML, NSRGY, SAP, LVMH 등

### ✅ 이전 완료 작업 (2025-09-12)
1. **데이터 연결 및 오류 수정 완료**
   - stocks 변수 오류 수정 → 대시보드 정상 동작
   - 한국어 미국 주식명 매핑 추가 ("애플" → "AAPL", "테슬라" → "TSLA")
   - asyncio import 추가 및 타임아웃 처리 (5초)
   - feedparser 모듈 설치로 뉴스 수집 정상화
   - financial_data None 처리로 에러 방지

2. **실시간 데이터 표시 개선**
   - Yahoo Finance API로 실제 주가 데이터 표시 (₩73,400 등)
   - 한국/미국 주식 구분하여 통화 포맷팅 (₩/$ 자동 변환)
   - 가격 변동률 색상 및 아이콘 표시 (▲▼ 추가)
   - 시가총액, 거래량, 52주 최고/최저가 추가
   - RSS 피드로 실제 뉴스 데이터 수집 성공

3. **AI 감성 분석 작동**
   - 삼성전자: 감성 점수 0.66 (매우 긍정적)
   - 실제 뉴스 기사 기반 AI 분석 제공
   - 상세한 투자 조언 및 리스크 분석

### 📊 현재 작동 상태
- **✅ 실시간 주가**: Yahoo Finance API (API 키 불필요)
- **✅ 뉴스 수집**: RSS 피드 (feedparser)
- **✅ 감성 분석**: AI 기반 긍정/부정 분석
- **✅ 대시보드**: 주가, 뉴스, 지표 정상 표시
- **⚠️ DART API**: 재무제표 (API 키 필요)
- **⚠️ News API**: 더 많은 뉴스 소스 (API 키 필요)
- **⚠️ Gemini AI**: 고급 AI 분석 (API 키 필요)

### 🔑 필요한 API 키
1. **DART API**: https://opendart.fss.or.kr/ (한국 재무제표)
2. **News API**: https://newsapi.org/ (실시간 뉴스)
3. **Gemini AI**: https://makersuite.google.com/ (AI 분석)

### 🚀 다음 구현 예정
1. **기술적 분석**: RSI, MACD, 이동평균선
2. **실시간 차트**: 캔들스틱 차트 구현
3. **재무 지표**: PER, PBR, ROE 계산 및 표시
4. **Financial Agent Session 오류 수정**

## 다음 단계 (2025-08-30 진행중)
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