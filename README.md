# DB Monitoring Pro

AI 기반 자연어 쿼리와 실시간 이상 탐지로 누구나 쉽게 데이터베이스 모니터링할 수 있는 한국형 DB 모니터링 플랫폼입니다.

- [발표 자료](https://gamma.app/docs/DB-Monitor-Pro-kw2ql057408qbzj)

## ☁️ 주요 기능

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

## ☁️ 기술 스택

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

## ☁️ Azure 아키텍처

### 핵심 Azure 서비스

#### 1. **Azure OpenAI Service**

- **GPT-4**: 자연어 쿼리를 SQL로 변환하는 핵심 AI 모델
- **Text Embedding**: 스키마 문서의 벡터화를 통한 의미 기반 검색
- **Chat Completion API**: 대화형 SQL 생성 및 검증

#### 2. **Azure AI Search**

- **하이브리드 검색**: 키워드 검색 + 벡터 검색의 조합
- **한국어 분석기**: `ko.lucene` 분석기로 한국어 쿼리 최적화
- **멀티테넌트 지원**: 고객사별 스키마 인덱스 분리
- **필터링**: 스키마, 테이블, 비즈니스 태그 기반 정밀 검색

#### 3. **Azure Cosmos DB**

- **NoSQL 문서 저장**: 모니터링 지표, 쿼리 히스토리, 이상 감지 결과
- **자동 스케일링**: 트래픽 증가에 따른 자동 성능 확장
- **글로벌 분산**: 다중 리전 복제로 고가용성 확보

#### 4. **Azure Container Apps**

- **마이크로서비스 배포**: 백엔드 API와 스케줄러 서비스 분리
- **자동 스케일링**: 사용량에 따른 컨테이너 인스턴스 조정
- **관리형 인프라**: 서버리스 환경으로 운영 부담 최소화

### 아키텍처 플로우

```
사용자 자연어 입력
    ↓
Azure OpenAI (GPT-4) - 쿼리 이해
    ↓
Azure AI Search - 관련 스키마 검색 (RAG)
    ↓
Azure OpenAI (GPT-4) - SQL 생성
    ↓
PostgreSQL - 쿼리 실행
    ↓
Azure Cosmos DB - 결과 저장
    ↓
이상치 감지 알고리즘
    ↓
알림 시스템 (Slack/Email)
```

## ☁️ AI 워크플로우 (LangGraph)

### LangGraph 에이전트 노드 구조

#### 1. **검색 노드 (search_tables)**

- Azure AI Search를 통한 관련 테이블 검색
- 하이브리드 검색으로 정확도 향상
- 비즈니스 컨텍스트 기반 스코어링

#### 2. **SQL 생성 노드 (generate_sql)**

- 검색된 스키마 정보를 바탕으로 SQL 생성
- GPT-4 기반 자연어 → SQL 변환
- 비즈니스 로직을 고려한 쿼리 최적화

#### 3. **검증 노드 (validate_sql)**

- SQL 문법 및 보안 검증
- 스키마 호환성 확인
- 위험한 쿼리 차단 (DDL, DML 등)

#### 4. **실행 노드 (execute_sql)**

- 읽기 전용 계정으로 안전한 쿼리 실행
- 타임아웃 및 결과 제한 설정
- 에러 핸들링 및 로깅

#### 5. **이상 감지 노드 (detect_anomaly)**

- 통계 기반 이상치 탐지 알고리즘
- 히스토리 데이터와 비교 분석
- 임계값 기반 알림 트리거

### 상태 관리 (AgentState)

```python
class AgentState(TypedDict):
    user_query: str                    # 사용자 입력
    relevant_tables: List[dict]         # 검색된 테이블 정보
    generated_sql: str                 # 생성된 SQL
    sql_valid: bool                    # 검증 결과
    query_result: dict                 # 실행 결과
    anomaly_detected: bool             # 이상 감지 여부
    notification_sent: bool            # 알림 발송 상태
```

## ☁️ RAG (Retrieval-Augmented Generation) 구현

### 1. **스키마 인덱싱 파이프라인**

```
PostgreSQL 스키마 추출
    ↓
비즈니스 컨텍스트 생성 (YAML)
    ↓
문서화 및 메타데이터 추가
    ↓
Azure OpenAI 임베딩 생성
    ↓
Azure AI Search 인덱싱
```

### 2. **검색 증강 생성 프로세스**

- **쿼리 분석**: 사용자 자연어 입력 파싱
- **컨텍스트 검색**: 관련 테이블/컬럼 정보 검색
- **컨텍스트 압축**: 중복 제거 및 관련성 높은 정보 선별
- **SQL 생성**: 검색된 컨텍스트를 바탕으로 정확한 SQL 생성

### 3. **인덱스 스키마 설계**

```json
{
  "id": "table_name",
  "object_type": "table|column|view",
  "name": "테이블명",
  "description": "테이블 설명",
  "content": "검색용 텍스트",
  "columns_text": "컬럼 정보",
  "relations_text": "관계 정보",
  "sample_queries_text": "예시 쿼리",
  "business_tags": ["태그1", "태그2"],
  "embedding": [벡터값...]
}
```

## ☁️ 모니터링 및 스케줄링

### APScheduler 기반 백그라운드 모니터링

- **1시간 간격**: 등록된 모든 지표 자동 실행
- **멀티테넌트**: 고객사별 독립적인 모니터링
- **장애 복구**: 실패한 작업 자동 재시도
- **상태 추적**: 실시간 스케줄러 상태 모니터링

### 고도화된 이상치 감지 알고리즘

- **상대적 비율 감지**: 20개 중 1개(5%)도 이상치로 감지
- **카테고리형 분포 분석**: 극소/소수 카테고리 자동 감지
- **다층 감지 시스템**: NULL, 중복, 분포 이상치 종합 분석
- **통계적 방법**: Z-score, IQR 기반 수치형 아웃라이어 탐지
- **시계열 분석**: 트렌드 변화 및 패턴 이상 감지
- **학습 기능**: 히스토리 데이터 기반 임계값 자동 조정

#### 감지 레벨

- **극소 카테고리**: 1% 미만 (100개 중 1개)
- **소수 카테고리**: 5% 미만 (20개 중 1개) ← 핵심 기능
- **분포 불균형**: 한 값이 90% 이상 차지
- **상대적 NULL 감지**: 15개 중 1개만 NULL이어도 이상치로 감지
  - NOT NULL 컬럼에 NULL 값 존재 (심각)
  - 소수 NULL (5% 미만) - 20개 중 1개 미만
  - 극소 NULL (1% 미만) - 100개 중 1개 미만
  - 다수 NULL (20% 이상) - 데이터 품질 문제

## ☁️ 핵심 차별화 포인트

### 1. **한국형 자연어 처리**

- **한국어 최적화**: `ko.lucene` 분석기로 한국어 쿼리 정확도 향상
- **비즈니스 컨텍스트**: 도메인별 용어와 비즈니스 로직 이해
- **맥락적 이해**: "신규 회원가입수", "이탈률" 등 비즈니스 용어 자동 해석

### 2. **지능형 스키마 검색**

- **하이브리드 검색**: 키워드 + 벡터 검색으로 정확도 극대화
- **관계형 추론**: 테이블 간 관계를 고려한 스마트 추천
- **컨텍스트 압축**: 관련성 높은 정보만 선별하여 토큰 효율성 증대

### 3. **지능형 이상치 감지**

- **상대적 비율 감지**: 20개 중 1개(5%)도 정확히 감지
- **카테고리형 분석**: 분포 불균형 및 소수 카테고리 자동 탐지
- **다층 감지**: NULL, 중복, 분포 이상치를 종합적으로 분석
- **실시간 모니터링**: 1시간마다 자동 실행되는 백그라운드 모니터링

### 4. **확장 가능한 아키텍처**

- **마이크로서비스**: API, 스케줄러, 알림 서비스 분리
- **클라우드 네이티브**: Azure 서비스 기반 완전 관리형 인프라
- **자동 스케일링**: 트래픽 증가에 따른 자동 확장

## ☁️ 설치 및 실행

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

## ☁️ Azure 배포

### 배포 스크립트 사용법

#### 1. 통합 배포 (기본)

```bash
# 백엔드와 프론트엔드 모두 배포
./scripts/deployment/azure/deploy-container-apps.sh

# 또는 명시적으로 all 옵션 사용
./scripts/deployment/azure/deploy-container-apps.sh all
```

#### 2. 백엔드만 배포

```bash
./scripts/deployment/azure/deploy-container-apps.sh backend
```

#### 3. 프론트엔드만 배포

```bash
./scripts/deployment/azure/deploy-container-apps.sh frontend
```

#### 4. 개별 스크립트 사용

```bash
# 백엔드 전용 배포
./scripts/deployment/azure/deploy-backend.sh

# 프론트엔드 전용 배포
./scripts/deployment/azure/deploy-frontend.sh
```

#### 5. 도움말 보기

```bash
./scripts/deployment/azure/deploy-container-apps.sh help
```

### 배포 전 준비사항

1. **Azure CLI 설치 및 로그인**

   ```bash
   az login
   az account set --subscription "your-subscription-id"
   ```

2. **환경변수 설정**

   ```bash
   # .env.production 파일 생성
   cp .env.sample .env.production
   # 필요한 Azure 서비스 키들을 설정
   ```

3. **필수 환경변수**
   - `ACR_NAME`: Azure Container Registry 이름
   - `COSMOS_ENDPOINT`, `COSMOS_KEY`: Cosmos DB 연결 정보
   - `AZURE_SEARCH_*`: Azure AI Search 설정
   - `AZURE_OPENAI_*`: Azure OpenAI 서비스 설정
   - 기타 모니터링 관련 설정들

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

## ☁️ 화면

### 랜딩 페이지

<img width="890" height="774" alt="Image" src="https://github.com/user-attachments/assets/4eae9232-3220-4f9c-b711-d267005e0444" />

### DB 스키마 인덱싱

<img width="1696" height="895" alt="Image" src="https://github.com/user-attachments/assets/9d9258ee-7b6d-45d6-b5b5-7031179a0b08" />

### 모니터링 지표 설정

<img width="1690" height="945" alt="Image" src="https://github.com/user-attachments/assets/0e37a173-f823-4ced-98f9-34fd5d58b591" />

### 대시보드

<img width="1699" height="940" alt="Image" src="https://github.com/user-attachments/assets/2b29b0d0-02b5-4ed8-963c-b38728672287" />

<img width="1700" height="940" alt="Image" src="https://github.com/user-attachments/assets/9de20876-1372-4a01-a336-10d96fd632ea" />
