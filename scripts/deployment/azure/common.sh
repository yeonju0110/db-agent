#!/bin/bash
# scripts/deployment/azure/common.sh
# 공통 배포 함수 및 변수 정의

set -e

# 기본 변수 설정 (환경변수에서 로드, 기본값 제공)
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-yj}"
LOCATION="${LOCATION:-Korea Central}"
APP_NAME="${APP_NAME:-db-agent}"
IMAGE_NAME="${IMAGE_NAME:-db-agent-backend}"

# 색상 출력 함수
print_info() {
    echo "ℹ️  $1"
}

print_success() {
    echo "✅ $1"
}

print_warning() {
    echo "⚠️  $1"
}

print_error() {
    echo "❌ $1"
}

print_step() {
    echo "🚀 $1"
}

# 환경변수 파일 로드 함수
load_env_file() {
    if [[ -f ".env.production" ]]; then
        print_info ".env.production 파일 로드 중..."
        export $(grep -v '^#' .env.production | xargs)
    else
        print_warning ".env.production 파일이 없습니다. 환경변수를 수동으로 설정해주세요."
    fi
}

# Container Registry 정보 확인 함수
check_acr_config() {
    if [[ -z "${ACR_NAME}" ]]; then
        print_error "ACR_NAME 환경변수가 설정되지 않았습니다."
        echo "Azure Container Registry 이름을 설정해주세요."
        echo "예: export ACR_NAME=dbmonitorpro"
        exit 1
    fi
    
    ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
    print_success "ACR 설정 확인 완료: $ACR_LOGIN_SERVER"
}

# 배포 기본 환경변수 검증 함수
validate_deployment_env() {
    print_info "배포 환경변수 검증 중..."
    required_vars=(
        "RESOURCE_GROUP"
        "LOCATION"
        "APP_NAME"
        "IMAGE_NAME"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "필수 배포 환경변수가 설정되지 않았습니다:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "다음 명령어로 환경변수를 설정하거나 .env.production 파일을 생성하세요:"
        echo "  export $var=your_value"
        exit 1
    fi
    
    print_success "배포 환경변수 검증 완료."
}

# 데이터베이스 환경변수 검증 함수
validate_database_env() {
    print_info "데이터베이스 환경변수 검증 중..."
    required_vars=(
        "TEST_CLIENT_DB_HOST"
        "TEST_CLIENT_DB_PORT"
        "TEST_CLIENT_DB_NAME"
        "TEST_CLIENT_DB_USER"
        "TEST_CLIENT_DB_PASSWORD"
        "TEST_CLIENT_DB_TYPE"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "필수 배포 환경변수가 설정되지 않았습니다:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "다음 명령어로 환경변수를 설정하거나 .env.production 파일을 생성하세요:"
        echo "  export $var=your_value"
        exit 1
    fi
    
    print_success "배포 환경변수 검증 완료."
}

# 백엔드 필수 환경변수 검증 함수
validate_backend_env() {
    print_info "백엔드 환경변수 검증 중..."
    required_vars=(
        "COSMOS_ENDPOINT"
        "COSMOS_KEY" 
        "COSMOS_DATABASE"
        "AZURE_SEARCH_ENDPOINT"
        "AZURE_SEARCH_API_KEY"
        "AZURE_SEARCH_INDEX_NAME"
        "AZURE_OPENAI_ENDPOINT"
        "AZURE_OPENAI_API_KEY"
        "AZURE_OPENAI_API_VERSION"
        "AZURE_OPENAI_DEPLOYMENT_NAME"
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
        "EMBEDDING_DIM"
        "DEFAULT_TENANT_ID"
        "DEFAULT_TENANT_NAME"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "필수 데이터베이스 환경변수가 설정되지 않았습니다:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "다음 명령어로 환경변수를 설정하거나 .env.production 파일을 생성하세요:"
        echo "  export $var=your_value"
        exit 1
    fi
    
    print_success "데이터베이스 환경변수 검증 완료."
}

# 백엔드 필수 환경변수 검증 함수
validate_backend_env() {
    print_info "백엔드 환경변수 검증 중..."
    required_vars=(
        "COSMOS_ENDPOINT"
        "COSMOS_KEY" 
        "COSMOS_DATABASE"
        "AZURE_SEARCH_ENDPOINT"
        "AZURE_SEARCH_API_KEY"
        "AZURE_SEARCH_INDEX_NAME"
        "AZURE_OPENAI_ENDPOINT"
        "AZURE_OPENAI_API_KEY"
        "AZURE_OPENAI_API_VERSION"
        "AZURE_OPENAI_DEPLOYMENT_NAME"
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
        "EMBEDDING_DIM"
        "DEFAULT_TENANT_ID"
        "DEFAULT_TENANT_NAME"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "필수 환경변수가 설정되지 않았습니다:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "다음 명령어로 환경변수를 설정하거나 .env.production 파일을 생성하세요:"
        echo "  export $var=your_value"
        exit 1
    fi
    
    print_success "모든 필수 환경변수가 설정되었습니다."
}

# 프론트엔드 필수 환경변수 검증 함수
validate_frontend_env() {
    print_info "프론트엔드 환경변수 검증 중..."
    # 프론트엔드는 특별한 환경변수가 필요하지 않을 수 있음
    print_success "프론트엔드 환경변수 검증 완료."
}

# URL 정보 출력 함수
print_deployment_urls() {
    echo ""
    echo "🔗 접속 URL:"
    
    # 프론트엔드 URL
    if command -v az &> /dev/null; then
        FRONTEND_URL=$(az staticwebapp show --name "$APP_NAME-frontend" --resource-group "$RESOURCE_GROUP" --query defaultHostname -o tsv 2>/dev/null || echo "")
        if [[ -n "$FRONTEND_URL" ]]; then
            echo "  - Frontend: https://$FRONTEND_URL"
        fi
        
        # 백엔드 URL
        BACKEND_URL=$(az containerapp show --name "$APP_NAME-backend" --resource-group "$RESOURCE_GROUP" --query properties.configuration.ingress.fqdn -o tsv 2>/dev/null || echo "")
        if [[ -n "$BACKEND_URL" ]]; then
            echo "  - Backend API: https://$BACKEND_URL"
        fi
    else
        echo "  - Azure CLI가 설치되지 않아 URL을 가져올 수 없습니다."
    fi
    echo ""
}

# 배포 완료 메시지 출력 함수
print_deployment_complete() {
    echo "🎉 배포가 성공적으로 완료되었습니다!"
    print_deployment_urls
}

# 사용법 출력 함수
print_usage() {
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  backend     백엔드만 배포"
    echo "  frontend    프론트엔드만 배포"
    echo "  all         백엔드와 프론트엔드 모두 배포 (기본값)"
    echo "  help        이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  $0 backend    # 백엔드만 배포"
    echo "  $0 frontend   # 프론트엔드만 배포"
    echo "  $0 all        # 전체 배포"
}
