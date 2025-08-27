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

## 현재 진행 상황
- [x] PRD 작성 완료
- [x] BMC 작성 완료
- [x] 개발 태스크 분해 완료
- [ ] A2A 코드베이스 Fork
- [ ] MVP 개발 시작

## 다음 단계
1. A2A 프로젝트(https://github.com/jeromwolf/A2A_sentiment_analysis) Fork
2. StockAI용으로 코드 정리 및 수정
3. DART/SEC API 연동 시작
4. 기본 채팅 UI 구현

## 테스트 및 검증 명령어
```bash
# 프로젝트 설정
git clone [repository]
cd greatWorld
pip install -r requirements.txt

# 개발 서버 실행
uvicorn api.main:app --reload --port 8000

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