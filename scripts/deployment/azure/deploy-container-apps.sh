#!/bin/bash
# scripts/deployment/azure/deploy-container-apps.sh
# 통합 배포 스크립트 - 선택형 배포 지원

# 공통 함수 및 변수 로드
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# 배포 타입 결정
DEPLOY_TYPE="${1:-all}"

case "$DEPLOY_TYPE" in
    "backend")
        print_step "백엔드만 배포합니다..."
        source "$SCRIPT_DIR/deploy-backend.sh"
        ;;
    "frontend")
        print_step "프론트엔드만 배포합니다..."
        source "$SCRIPT_DIR/deploy-frontend.sh"
        ;;
    "all")
        print_step "백엔드와 프론트엔드를 모두 배포합니다..."
        source "$SCRIPT_DIR/deploy-backend.sh"
        echo ""
        source "$SCRIPT_DIR/deploy-frontend.sh"
        ;;
    "help"|"-h"|"--help")
        print_usage
        exit 0
        ;;
    *)
        print_error "알 수 없는 옵션: $DEPLOY_TYPE"
        print_usage
        exit 1
        ;;
esac
