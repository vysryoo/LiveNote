#!/bin/bash

# RAGKit 자동 설치 및 테스트 스크립트
# 사용법: ./setup.sh

set -e  # 에러 발생 시 즉시 종료

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# 구분선
DIVIDER="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 헤더 출력
print_header() {
    echo -e "\n${BLUE}${DIVIDER}${NC}"
    echo -e "${BOLD}  $1${NC}"
    echo -e "${BLUE}${DIVIDER}${NC}\n"
}

# 성공 메시지
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 경고 메시지
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 에러 메시지
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 단계 표시
print_step() {
    echo -e "\n${BOLD}[$1/$2] $3...${NC}"
}

# 메인 스크립트 시작
clear
print_header "RAGKit 자동 설치 스크립트"

TOTAL_STEPS=7
CURRENT_STEP=0

# ========== 1. Python 버전 확인 ==========
CURRENT_STEP=$((CURRENT_STEP + 1))
print_step $CURRENT_STEP $TOTAL_STEPS "Python 버전 확인"

PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    print_success "Python $PYTHON_VERSION 확인"
else
    print_error "Python 3.11 이상이 필요합니다 (현재: $PYTHON_VERSION)"
    echo "설치 방법: https://www.python.org/downloads/"
    exit 1
fi

# ========== 2. 가상 환경 설정 ==========
CURRENT_STEP=$((CURRENT_STEP + 1))
print_step $CURRENT_STEP $TOTAL_STEPS "가상 환경 설정"

if [ ! -d ".venv" ]; then
    echo "  가상 환경 생성 중..."
    python -m venv .venv
    print_success "가상 환경 생성 완료"
else
    print_warning "가상 환경이 이미 존재함 (.venv)"
fi

# 가상 환경 활성화
source .venv/bin/activate
print_success ".venv 활성화 완료"

# pip 업그레이드
echo "  pip 업그레이드 중..."
pip install --upgrade pip -q
print_success "pip 최신 버전 확인"

# ========== 3. 패키지 설치 ==========
CURRENT_STEP=$((CURRENT_STEP + 1))
print_step $CURRENT_STEP $TOTAL_STEPS "패키지 설치"

echo "  numpy 다운그레이드 (호환성)..."
pip install "numpy<2" -q

echo "  RAGKit 및 의존성 설치 중 (1-2분 소요)..."
pip install -e . -q

# 설치 확인
if python -c "from ragkit import RAGService" 2>/dev/null; then
    print_success "모든 패키지 설치 완료"
else
    print_error "패키지 설치 실패"
    exit 1
fi

# ========== 4. API 키 설정 ==========
CURRENT_STEP=$((CURRENT_STEP + 1))
print_step $CURRENT_STEP $TOTAL_STEPS "API 키 설정"

if [ -f ".env" ] && grep -q "OPENAI_API_KEY" .env 2>/dev/null; then
    print_warning ".env 파일이 이미 존재함"
    echo -n "  덮어쓰시겠습니까? (y/N): "
    read -r OVERWRITE
    if [[ ! $OVERWRITE =~ ^[Yy]$ ]]; then
        print_success "기존 API 키 유지"
        SKIP_API_KEY=true
    fi
fi

if [ "$SKIP_API_KEY" != true ]; then
    echo ""
    echo -e "${BOLD}OpenAI API 키를 입력하세요 (sk-로 시작):${NC}"
    echo -n "> "
    read -r API_KEY
    
    if [[ $API_KEY == sk-* ]]; then
        echo "OPENAI_API_KEY=$API_KEY" > .env
        chmod 600 .env
        print_success "API 키 저장 완료 (.env)"
    else
        print_error "유효하지 않은 API 키 형식 (sk-로 시작해야 함)"
        exit 1
    fi
fi

# 환경 변수 로드
export $(cat .env | grep -v '^#' | xargs)

# ========== 5. 설치 확인 ==========
CURRENT_STEP=$((CURRENT_STEP + 1))
print_step $CURRENT_STEP $TOTAL_STEPS "설치 확인"

if [ -f "verify_setup.py" ]; then
    if python verify_setup.py > /dev/null 2>&1; then
        print_success "설치 확인 완료"
    else
        print_warning "설치 확인 중 경고 발생 (계속 진행)"
    fi
else
    print_warning "verify_setup.py 없음 (건너뜀)"
fi

# ========== 6. 테스트 PDF 생성 ==========
CURRENT_STEP=$((CURRENT_STEP + 1))
print_step $CURRENT_STEP $TOTAL_STEPS "테스트 PDF 생성"

if [ ! -f "test_data/large_test_20pages.pdf" ]; then
    if [ -f "create_large_test_pdf.py" ]; then
        echo "  20페이지 PDF 생성 중..."
        python create_large_test_pdf.py > /dev/null 2>&1
        print_success "20페이지 PDF 생성 완료"
    else
        print_warning "PDF 생성 스크립트 없음 (건너뜀)"
    fi
else
    print_success "테스트 PDF가 이미 존재함"
fi

# ========== 7. 종합 테스트 실행 ==========
CURRENT_STEP=$((CURRENT_STEP + 1))
print_step $CURRENT_STEP $TOTAL_STEPS "종합 테스트 실행"

echo ""
echo -e "${BOLD}종합 테스트를 실행하시겠습니까?${NC}"
echo "  - 60개 텍스트 청크 업로드"
echo "  - 20페이지 PDF 업로드"
echo "  - 7개 검색 쿼리 테스트"
echo "  (약 5-10초 소요, OpenAI API 사용)"
echo ""
echo -n "실행 (Y/n): "
read -r RUN_TEST

if [[ ! $RUN_TEST =~ ^[Nn]$ ]]; then
    echo ""
    python all_test.py
    print_success "종합 테스트 완료"
else
    print_warning "종합 테스트 건너뜀"
fi

# ========== 완료 ==========
print_header "설치 완료! 🎉"

echo -e "${BOLD}✅ 설치된 구성 요소:${NC}"
echo "   - Python $(python --version | awk '{print $2}')"
echo "   - 가상 환경: .venv"
echo "   - RAGKit 패키지"
echo "   - OpenAI API 키 설정"
echo ""

echo -e "${BOLD}📚 다음 단계:${NC}"
echo ""
echo "  1. 가상 환경 활성화:"
echo -e "     ${GREEN}source .venv/bin/activate${NC}"
echo ""
echo "  2. 간단한 예제 실행:"
echo -e "     ${GREEN}python examples/test_light.py${NC}"
echo ""
echo "  3. 상세 문서 확인:"
echo -e "     ${GREEN}cat README_KR.md${NC}"
echo ""
echo "  4. 단위 테스트 실행:"
echo -e "     ${GREEN}pytest -v${NC}"
echo ""

echo -e "${BOLD}🔧 유용한 명령어:${NC}"
echo "   - 종합 테스트: ${GREEN}python all_test.py${NC}"
echo "   - PDF 생성:    ${GREEN}python create_large_test_pdf.py${NC}"
echo "   - 환경 확인:   ${GREEN}python verify_setup.py${NC}"
echo ""

print_header "Ready to use RAGKit! 🚀"
