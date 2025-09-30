# DB Monitoring Pro

AI 기반 자연어 쿼리와 실시간 이상 탐지로 누구나 쉽게 데이터베이스 모니터링할 수 있는 한국형 DB 모니터링 플랫폼입니다.

## 🚀 주요 기능

### 1. 자연어 기반 모니터링 설정

- **Text-to-SQL**: 자연어로 입력한 모니터링 지표를 자동으로 SQL로 변환
- **실시간 미리보기**: 생성된 SQL 쿼리 결과를 즉시 확인
- **스마트 테이블 추천**: 관련 테이블을 AI가 자동 추천하여 이상치 감지 정확도 향상

### 2. 실시간 모니터링

- **자동 스케줄링**: 1시간마다 등록된 지표를 자동 실행
- **다양한 지표 타입**: 수치형, 카테고리형, 상태형 지표 지원
- **실시간 대시보드**: 직관적인 차트와 시각화로 모니터링 현황 확인

### 3. 이상치 감지 및 알림

- **자동 이상 탐지**: 통계 기반 이상치 감지 알고리즘
- **다중 알림 채널**: 이메일, Slack, Webhook 지원
- **팀 협업**: 역할별 알림 대상 설정

### 4. 통합 대시보드

- **실시간 상태 모니터링**: 지표별 정상/경고/장애 상태 표시
- **DB 연결 상태**: 연결된 데이터베이스 상태 실시간 확인
- **스케줄러 상태**: 백그라운드 모니터링 서비스 상태 표시

## 🏗️ 기술 스택

### Backend

- **FastAPI**: 고성능 Python 웹 프레임워크
- **LangGraph**: AI 에이전트 워크플로우 오케스트레이션
- **Azure OpenAI**: GPT-4 기반 자연어 처리
- **Azure Cosmos DB**: 모니터링 데이터 저장
- **Azure AI Search**: 스키마 검색 및 RAG
- **APScheduler**: 백그라운드 작업 스케줄링

### Frontend

- **React 19**: 최신 React 버전
- **TypeScript**: 타입 안전성
- **Tailwind CSS**: 유틸리티 기반 스타일링
- **Recharts**: 데이터 시각화
- **TanStack Query**: 서버 상태 관리

## 📋 설치 및 실행

### 1. 환경 설정

```bash
# 환경 변수 설정
cp .env.sample .env
# .env 파일에 필요한 Azure 서비스 키들을 설정하세요
```

### 2. 개발 서버 실행

```bash
# 백엔드 서버 (포트 8000)
uv run uvicorn backend.api.v1.main:app --reload --port 8000

# 프론트엔드 서버 (포트 5173)
cd frontend
yarn install
yarn dev
```

## 🔧 개발 가이드

### 프로젝트 구조

```
db-agent/
├── backend/                # FastAPI 백엔드
│   ├── api/v1/             # API 엔드포인트
│   ├── core/ai/            # AI 에이전트 및 LangGraph
│   ├── services/           # 비즈니스 로직
│   ├── models/             # 데이터 모델
│   └── repositories/       # 데이터 접근 계층
├── frontend/               # React 프론트엔드
│   ├── src/pages/          # 페이지 컴포넌트
│   ├── src/components/     # 재사용 가능한 컴포넌트
│   └── src/features/       # 기능별 모듈
├── scripts/                # 설정 및 유틸리티 스크립트
└── infrastructure/         # 인프라 코드
```

### AI 워크플로우

1. **스키마 인덱싱**: DB 스키마 추출 → 비즈니스 컨텍스트 생성 → Azure AI Search 인덱싱
2. **쿼리 처리**: 자연어 입력 → 스키마 검색 → SQL 생성 → 검증 → 실행
3. **모니터링**: 결과 저장 → 이상치 감지 → 알림 발송 → 대시보드 업데이트
