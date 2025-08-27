# StockAI - AI 기반 주식 분석 서비스

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/FastAPI-0.109+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/license-MIT-orange.svg" alt="License">
</p>

## 🚀 개요

StockAI는 AI 기반 주식 분석 서비스로, 국내외 주식에 대한 실시간 분석을 제공하는 대화형 플랫폼입니다.

### 주요 특징
- 🤖 **대화형 인터페이스**: 자연어로 질문하면 AI가 즉시 분석
- 🌍 **글로벌 통합**: 국내(KOSPI/KOSDAQ)와 해외(NYSE/NASDAQ) 주식 통합 분석
- 📊 **실시간 감성 분석**: Reddit, X(Twitter) 등 SNS 모니터링
- 🔍 **종합적 분석**: 공시, 뉴스, 재무제표를 한 번에

## 🛠 기술 스택

- **Backend**: Python 3.8+, FastAPI
- **AI**: Gemini AI, GPT-4
- **Real-time**: WebSocket
- **Database**: PostgreSQL, Redis
- **Architecture**: A2A Multi-Agent System

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
```bash
uvicorn api.main:app --reload --port 8000
```

웹 브라우저에서 http://localhost:8000 접속

## 📁 프로젝트 구조

```
greatworld/
├── agents/               # AI 에이전트들
│   ├── nlu_agent.py     # 자연어 이해
│   ├── dart_agent.py    # 국내 공시 수집
│   └── sentiment_agent.py # 감성 분석
├── api/                  # FastAPI 백엔드
├── frontend/             # 웹 UI
├── tests/                # 테스트 코드
└── docs/                 # 문서
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
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

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