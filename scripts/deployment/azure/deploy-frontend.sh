#!/bin/bash
# scripts/deployment/azure/deploy-frontend.sh
# 프론트엔드 전용 배포 스크립트

# 공통 함수 및 변수 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

print_step "DB Agent 프론트엔드 배포 시작..."

# 환경변수 로드 및 검증
load_env_file
validate_deployment_env
validate_frontend_env

# 프론트엔드 디렉토리로 이동
print_info "프론트엔드 디렉토리로 이동 중..."
cd frontend

# 프론트엔드 빌드
print_step "Frontend 빌드 중..."
yarn build

# 배포 토큰 가져오기
print_info "배포 토큰 생성 중..."
DEPLOYMENT_TOKEN=$(az staticwebapp secrets list \
  --name "$APP_NAME-frontend" \
  --resource-group "$RESOURCE_GROUP" \
  --query properties.apiKey -o tsv)

print_info "Static Web App 배포 토큰: $DEPLOYMENT_TOKEN"
print_step "Azure Static Web Apps CLI를 이용해 Frontend를 배포합니다..."

# npx를 사용하여 SWA CLI로 배포
npx @azure/static-web-apps-cli deploy ./dist \
  --deployment-token "$DEPLOYMENT_TOKEN" \
  --env production

print_success "Frontend가 Azure Static Web App에 배포되었습니다."

# 루트 디렉토리로 돌아가기
cd ..

print_success "프론트엔드 배포 완료!"
echo "📋 업데이트된 리소스:"
echo "  - Frontend Static Web App: $APP_NAME-frontend"

print_deployment_complete
