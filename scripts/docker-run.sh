#!/bin/bash

# macOS hidden files 제거
echo "Removing macOS hidden files..."
find . -name "._*" -type f -delete

# Docker 실행
echo "Starting Docker containers..."
docker-compose up -d --build

# 상태 확인
echo "Checking container status..."
docker-compose ps