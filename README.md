# StockAI - AI 기반 주식 분석 플랫폼

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/FastAPI-0.109+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/license-MIT-orange.svg" alt="License">
</p>

A2A 멀티에이전트 시스템을 기반으로 한 실시간 주식 분석 챗봇 서비스

## 🏗️ 프로젝트 구조

```
stock-ai/
├── agents/                    # A2A 기반 분석 에이전트들
│   ├── simple_nlu_agent.py   # 자연어 이해
│   ├── financial_agent.py    # 재무제표 분석
│   ├── technical_agent.py    # 기술적 분석
│   ├── sentiment_agent.py    # 감성 분석 통합
│   └── ...
├── api/                      # FastAPI 백엔드
│   ├── main.py              # 메인 API 서버
│   └── price_streamer.py    # WebSocket 실시간 스트리밍
├── frontend/                # 웹 인터페이스
│   ├── responsive.html      # 반응형 메인 UI
│   └── static/             # CSS/JS 파일들
├── stockai-frontend/        # Next.js React (참고용)
├── cache/                   # 캐싱 시스템
├── utils/                   # 유틸리티 함수들
├── config/                  # 설정 파일들
├── docs/                    # 문서들
├── scripts/                 # 실행 스크립트들
├── docker/                  # Docker 설정 파일들
└── tests/                   # 테스트 코드
```

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# Python 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정
```bash
# .env 파일 생성 (템플릿 복사)
cp .env.example .env

# API 키 설정 (.env 파일 편집)
# GEMINI_API_KEY=your_gemini_key
# OPENAI_API_KEY=your_openai_key
# DART_API_KEY=your_dart_key
```

### 3. 서버 실행
```bash
# 메인 서버 실행 (권장)
uvicorn api.main:app --reload --port 8200

# 또는 스크립트 사용
./scripts/restart.sh
```

### 4. 접속
- **메인 UI**: http://localhost:8200
- **API 문서**: http://localhost:8200/docs
- Next.js UI (참고용): http://localhost:3200

## 💻 주요 기능

### 🤖 AI 에이전트 시스템
- **NLU Agent**: 자연어 쿼리 이해 및 의도 분류
- **Financial Agent**: 재무제표 분석 및 건전성 평가
- **Technical Agent**: 기술적 지표 계산 (MA, RSI, MACD 등)
- **Sentiment Agent**: 뉴스/SNS 감성 분석 통합
- **Price Agent**: 실시간 주가 데이터 수집

### 📊 데이터 소스
- **실시간 주가**: Yahoo Finance API
- **공시 데이터**: DART (한국), SEC (미국)
- **뉴스**: 다양한 뉴스 API
- **소셜 데이터**: Reddit, StockTwits

### 🎯 핵심 특징
- **가중치 시스템**: 데이터 소스별 신뢰도 반영
- **실시간 WebSocket**: 즉시 업데이트되는 분석 결과
- **반응형 UI**: 모바일/태블릿/데스크톱 완벽 지원
- **투자 인사이트**: 실행 가능한 투자 전략 제공

## 📋 주요 기능

### 1. 자연어 주식 분석
```
사용자: "삼성전자 최근 실적 어때?"
AI: "삼성전자의 3분기 실적을 분석해드릴게요..."
```

### 2. 실시간 시장 감성 분석
- SNS 버즈 모니터링
- 투자자 심리 지수
- 이상 신호 감지

### 3. 통합 리포트 생성
- 공시 자동 요약
- 재무 트렌드 분석
- AI 투자 의견

## 🚦 시작하기

### 필수 요구사항
- Python 3.8 이상
- PostgreSQL 12 이상
- Redis 6 이상
- API 키: Gemini AI, OpenAI (선택)

### 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/jeromwolf/greatworld.git
cd greatworld
```

2. 가상환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 API 키 추가
```

5. 데이터베이스 초기화
```bash
python scripts/init_db.py
```

6. 개발 서버 실행

**자동 재시작 스크립트 사용 (권장)**
```bash
# 모든 서비스 시작
./restart.sh

# 개별 서비스 제어
./restart.sh backend   # 백엔드만
./restart.sh frontend  # 프론트엔드만
./restart.sh status    # 상태 확인
./restart.sh stop      # 모두 중지
```

**수동 실행**
```bash
# Backend (FastAPI) - 포트 8200
uvicorn api.main:app --reload --port 8200

# Frontend (Next.js) - 포트 3200 (별도 터미널)
cd stockai-frontend
npm install
npm run dev
```

접속 URL:
- Next.js UI: http://localhost:3200 (권장)
- 기본 UI: http://localhost:8200
- API 문서: http://localhost:8200/docs

## 📁 프로젝트 구조

```
greatworld/
├── agents/                     # AI 에이전트들
│   ├── simple_nlu_agent.py    # 자연어 이해
│   ├── dart_agent.py          # 국내 공시 수집
│   ├── sec_agent.py           # 미국 공시 수집
│   ├── news_agent.py          # 뉴스 수집
│   ├── social_agent.py        # SNS 데이터 수집
│   └── sentiment_agent.py     # 감성 분석 통합
├── api/                       # FastAPI 백엔드
│   └── main.py               # WebSocket & REST API
├── frontend/                  # 기본 웹 UI
├── stockai-frontend/          # Next.js 모던 UI
│   ├── app/                  # App Router
│   ├── components/           # React 컴포넌트
│   └── types/               # TypeScript 타입
├── a2a_core/                 # A2A 프로토콜 코어
├── tests/                    # 테스트 코드
└── docs/                     # 문서
```

## 🧪 테스트

```bash
# 유닛 테스트
pytest tests/

# 커버리지 확인
pytest --cov=. tests/

# 코드 품질 검사
ruff check .
mypy .
```

## 📊 API 문서

서버 실행 후 다음 주소에서 API 문서 확인:
- Swagger UI: http://localhost:8200/docs
- ReDoc: http://localhost:8200/redoc

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요.

## 👥 팀

- **Kelly** - 개발자 - [@jeromwolf](https://github.com/jeromwolf)

## 🙏 감사의 말

- A2A 프로젝트 - 멀티 에이전트 시스템 기반 제공
- Gemini AI & OpenAI - AI 분석 엔진

## 📞 문의

질문이나 제안사항이 있으시면 이슈를 생성해주세요!

---

<p align="center">Made with ❤️ by StockAI Team</p>