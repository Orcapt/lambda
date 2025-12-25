#!/bin/bash
# deploy.sh
# =========
# اسکریپت ساده برای دیپلوی روی Lambda

set -e  # Exit on error

# رنگ‌ها برای output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Orca Dummy Agent - Lambda Deployment${NC}"
echo "=================================="
echo ""

# بررسی وجود Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker نصب نیست!${NC}"
    exit 1
fi

# بررسی وجود orca-cli
if ! command -v orca &> /dev/null; then
    echo -e "${RED}❌ orca-cli نصب نیست!${NC}"
    echo "نصب کنید: npm install -g @orca-platform/cli"
    exit 1
fi

# نام image
IMAGE_NAME="orca-dummy-agent"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

# بررسی وجود .env.lambda
if [ ! -f ".env.lambda" ]; then
    echo -e "${YELLOW}⚠️  فایل .env.lambda پیدا نشد!${NC}"
    echo "ایجاد .env.lambda.example..."
    if [ -f ".env.lambda.example" ]; then
        cp .env.lambda.example .env.lambda
        echo -e "${YELLOW}⚠️  لطفاً .env.lambda را ویرایش کنید و سپس دوباره اجرا کنید.${NC}"
        exit 1
    else
        echo -e "${RED}❌ .env.lambda.example هم پیدا نشد!${NC}"
        exit 1
    fi
fi

# مرحله 1: Build Docker image
echo -e "${GREEN}📦 Building Docker image...${NC}"
docker build -f Dockerfile.lambda -t "${FULL_IMAGE_NAME}" .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Image built successfully!${NC}"
echo ""

# مرحله 2: Deploy با orca ship
echo -e "${GREEN}🚀 Deploying to Lambda...${NC}"
echo ""

orca ship "${IMAGE_NAME}" \
  --image "${FULL_IMAGE_NAME}" \
  --memory 2048 \
  --timeout 300 \
  --env-file ./.env.lambda

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment failed!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo "  - View logs: orca lambda logs ${IMAGE_NAME} --tail"
echo "  - Test function: curl -XPOST <function-url> ..."
echo "  - See LAMBDA_DEPLOY.md for more details"

