#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 설정
KEY_PATH="/Users/hyunwookkim/Documents/study/25y2s/캡스톤/LiveNote_프로토타입/module_intergration/sireal-key.pem"
REMOTE_USER="ubuntu"
REMOTE_HOST="54.180.135.94"
REMOTE_PATH="/home/ubuntu/livenote-front"
BUILD_PATH="./build"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}   LiveNote 프론트엔드 자동 배포${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# 1. 빌드
echo -e "${GREEN}[1/3] 빌드 시작...${NC}"
npm run build

if [ $? -ne 0 ]; then
    echo -e "${RED}빌드 실패!${NC}"
    exit 1
fi

echo -e "${GREEN}빌드 완료!${NC}"
echo ""

# 2. 원격 서버의 기존 파일 백업 및 삭제
echo -e "${GREEN}[2/3] 원격 서버 정리 중...${NC}"
ssh -i "$KEY_PATH" ${REMOTE_USER}@${REMOTE_HOST} << 'ENDSSH'
    if [ -d /home/ubuntu/livenote-front/build ]; then
        echo "기존 build 디렉토리 삭제 중..."
        rm -rf /home/ubuntu/livenote-front/build
    fi
ENDSSH

echo -e "${GREEN}서버 정리 완료!${NC}"
echo ""

# 3. 파일 전송
echo -e "${GREEN}[3/3] 파일 전송 중...${NC}"
scp -i "$KEY_PATH" -r "$BUILD_PATH" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}

if [ $? -ne 0 ]; then
    echo -e "${RED}파일 전송 실패!${NC}"
    exit 1
fi

echo -e "${GREEN}파일 전송 완료!${NC}"
echo ""

echo -e "${YELLOW}========================================${NC}"
echo -e "${GREEN}✅ 배포 완료!${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "프론트엔드 URL: ${GREEN}http://${REMOTE_HOST}${NC}"
echo ""
