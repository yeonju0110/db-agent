# backend/Dockerfile.optimized
FROM python:3.12-slim as base

# 공통 설정
WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN pip install --no-cache-dir uv

# 의존성 설치 단계
FROM base as deps
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 애플리케이션 단계
FROM base as app
COPY --from=deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# 애플리케이션 코드 복사
COPY backend/ ./backend/
COPY scripts/ ./scripts/

# 비root 사용자
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# 포트 및 헬스체크
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 실행
CMD ["uvicorn", "backend.api.v1.main:app", "--host", "0.0.0.0", "--port", "8000"]