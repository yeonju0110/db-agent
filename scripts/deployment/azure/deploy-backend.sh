#!/bin/bash
# scripts/deployment/azure/deploy-backend.sh
# 백엔드 전용 배포 스크립트

# 공통 함수 및 변수 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

print_step "DB Agent 백엔드 배포 시작..."

# 환경변수 로드 및 검증
load_env_file
validate_deployment_env
check_acr_config
validate_database_env
validate_backend_env

# 이미지 태그 설정 (현재 시간 기반)
IMAGE_TAG=$(date +%Y%m%d-%H%M%S)
print_info "이미지 태그: $IMAGE_TAG"

# ACR 로그인
print_info "Azure Container Registry 로그인 중..."
az acr login --name "$ACR_NAME"

# Docker 이미지 빌드 및 푸시
print_step "Docker 이미지 빌드 및 푸시 중..."
docker build --platform linux/amd64 -t "$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG" -f backend/Dockerfile .
docker push "$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG"

# Backend Container App 업데이트
print_step "Backend Container App 업데이트 중..."
az containerapp update \
  --name "$APP_NAME-backend" \
  --resource-group "$RESOURCE_GROUP" \
  --image "$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG" \
  --set-env-vars \
    ENVIRONMENT=production \
    TEST_CLIENT_DB_HOST="${TEST_CLIENT_DB_HOST:-$APP_NAME-postgres.postgres.database.azure.com}" \
    TEST_CLIENT_DB_PORT="${TEST_CLIENT_DB_PORT:-5432}" \
    TEST_CLIENT_DB_NAME="${TEST_CLIENT_DB_NAME:-ecommerce_db}" \
    TEST_CLIENT_DB_USER="${TEST_CLIENT_DB_USER:-monitoring_user}" \
    TEST_CLIENT_DB_PASSWORD="${TEST_CLIENT_DB_PASSWORD:-1234}" \
    TEST_CLIENT_DB_TYPE="${TEST_CLIENT_DB_TYPE:-postgres}" \
    SCHEDULER_INTERVAL_MINUTES="${SCHEDULER_INTERVAL_MINUTES:-60}" \
    SCHEDULER_DEFAULT_INTERVAL_MINUTES="${SCHEDULER_DEFAULT_INTERVAL_MINUTES:-60}" \
    DEFAULT_TENANT_ID="$DEFAULT_TENANT_ID" \
    DEFAULT_TENANT_NAME="$DEFAULT_TENANT_NAME" \
    COSMOS_ENDPOINT="$COSMOS_ENDPOINT" \
    COSMOS_KEY="$COSMOS_KEY" \
    COSMOS_DATABASE="$COSMOS_DATABASE" \
    AZURE_SEARCH_ENDPOINT="$AZURE_SEARCH_ENDPOINT" \
    AZURE_SEARCH_API_KEY="$AZURE_SEARCH_API_KEY" \
    AZURE_SEARCH_INDEX_NAME="$AZURE_SEARCH_INDEX_NAME" \
    AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
    AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
    AZURE_OPENAI_API_VERSION="$AZURE_OPENAI_API_VERSION" \
    AZURE_OPENAI_DEPLOYMENT_NAME="$AZURE_OPENAI_DEPLOYMENT_NAME" \
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT="$AZURE_OPENAI_EMBEDDING_DEPLOYMENT" \
    EMBEDDING_DIM="$EMBEDDING_DIM" \
  --output none

print_success "백엔드 배포 완료!"
echo "📋 업데이트된 리소스:"
echo "  - Backend Container: $APP_NAME-backend (이미지: $IMAGE_TAG)"

print_deployment_complete
