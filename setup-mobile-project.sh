#!/bin/bash

# 춤마루 모바일 웹앱 프로젝트 자동 설정 스크립트
# 사용법: bash setup-mobile-project.sh

set -e  # 에러 발생 시 중단

echo "🎭 춤마루(Choomaru) 모바일 웹앱 프로젝트 설정을 시작합니다..."
echo ""

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Node.js 버전 확인
echo -e "${BLUE}[1/10] Node.js 버전 확인 중...${NC}"
node_version=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$node_version" -lt 18 ]; then
    echo -e "${YELLOW}⚠️  Node.js 18 이상이 필요합니다. 현재 버전: $(node -v)${NC}"
    echo "https://nodejs.org 에서 최신 버전을 설치하세요."
    exit 1
fi
echo -e "${GREEN}✓ Node.js $(node -v) 확인 완료${NC}"
echo ""

# 2. Vite 프로젝트 생성
echo -e "${BLUE}[2/10] React + Vite 프로젝트 생성 중...${NC}"
if [ -d "choomaru-mobile" ]; then
    echo -e "${YELLOW}⚠️  choomaru-mobile 폴더가 이미 존재합니다.${NC}"
    read -p "덮어쓰시겠습니까? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf choomaru-mobile
    else
        echo "설정을 취소합니다."
        exit 0
    fi
fi

npm create vite@latest choomaru-mobile -- --template react
cd choomaru-mobile
echo -e "${GREEN}✓ 프로젝트 생성 완료${NC}"
echo ""

# 3. 기본 의존성 설치
echo -e "${BLUE}[3/10] 기본 의존성 설치 중...${NC}"
npm install
echo -e "${GREEN}✓ 기본 의존성 설치 완료${NC}"
echo ""

# 4. 추가 패키지 설치
echo -e "${BLUE}[4/10] 추가 패키지 설치 중...${NC}"
echo "  - MediaPipe, Router, 상태 관리, 웹캠..."

npm install @mediapipe/tasks-vision \
            react-router-dom \
            zustand \
            react-webcam

echo -e "${GREEN}✓ 코어 패키지 설치 완료${NC}"
echo ""

# 5. UI 라이브러리 설치
echo -e "${BLUE}[5/10] UI 라이브러리 설치 중...${NC}"
npm install -D tailwindcss postcss autoprefixer daisyui
npx tailwindcss init -p
echo -e "${GREEN}✓ Tailwind CSS + DaisyUI 설치 완료${NC}"
echo ""

# 6. PWA 플러그인 설치
echo -e "${BLUE}[6/10] PWA 플러그인 설치 중...${NC}"
npm install -D vite-plugin-pwa
echo -e "${GREEN}✓ PWA 플러그인 설치 완료${NC}"
echo ""

# 7. 제스처 라이브러리 설치
echo -e "${BLUE}[7/10] 제스처 라이브러리 설치 중...${NC}"
npm install @use-gesture/react @react-spring/web
echo -e "${GREEN}✓ 제스처 라이브러리 설치 완료${NC}"
echo ""

# 8. 폴더 구조 생성
echo -e "${BLUE}[8/10] 프로젝트 폴더 구조 생성 중...${NC}"
mkdir -p src/components/common
mkdir -p src/components/camera
mkdir -p src/components/pose
mkdir -p src/pages
mkdir -p src/stores
mkdir -p src/utils
mkdir -p src/hooks
mkdir -p src/styles
mkdir -p public/models
mkdir -p public/icons

echo -e "${GREEN}✓ 폴더 구조 생성 완료${NC}"
echo ""

# 9. Tailwind 설정 업데이트
echo -e "${BLUE}[9/10] Tailwind CSS 설정 중...${NC}"
cat > tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#667eea',
        secondary: '#764ba2',
      },
    },
  },
  plugins: [require('daisyui')],
  daisyui: {
    themes: ["light", "dark"],
  },
}
EOF

# src/index.css 업데이트
cat > src/index.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

/* 모바일 최적화 */
* {
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 터치 친화적 버튼 */
button, a {
  min-height: 44px;
  min-width: 44px;
}

/* 스크롤 최적화 */
.scrollable {
  -webkit-overflow-scrolling: touch;
}
EOF

echo -e "${GREEN}✓ Tailwind CSS 설정 완료${NC}"
echo ""

# 10. MediaPipe 모델 복사
echo -e "${BLUE}[10/10] MediaPipe 모델 파일 복사 중...${NC}"
if [ -f "../models/pose_landmarker_lite.task" ]; then
    cp ../models/pose_landmarker_lite.task public/models/
    echo -e "${GREEN}✓ pose_landmarker_lite.task 복사 완료${NC}"
else
    echo -e "${YELLOW}⚠️  ../models/pose_landmarker_lite.task 파일을 찾을 수 없습니다.${NC}"
    echo "   public/models/ 폴더에 수동으로 복사하세요."
fi

if [ -f "../models/hand_landmarker.task" ]; then
    cp ../models/hand_landmarker.task public/models/
    echo -e "${GREEN}✓ hand_landmarker.task 복사 완료${NC}"
else
    echo -e "${YELLOW}⚠️  ../models/hand_landmarker.task 파일을 찾을 수 없습니다.${NC}"
    echo "   public/models/ 폴더에 수동으로 복사하세요."
fi
echo ""

# Git 초기화
echo -e "${BLUE}Git 저장소 초기화 중...${NC}"
git init
cat > .gitignore << 'EOF'
# Logs
logs
*.log
npm-debug.log*

# Dependencies
node_modules/

# Production
dist/
dist-ssr/

# Local env files
.env
.env.local
.env.*.local

# Editor
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# PWA
sw.js
workbox-*.js
EOF

git add .
git commit -m "Initial commit: Choomaru mobile web app setup"
echo -e "${GREEN}✓ Git 저장소 초기화 완료${NC}"
echo ""

# 완료 메시지
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✨ 춤마루 모바일 웹앱 프로젝트 설정 완료! ✨${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}다음 단계:${NC}"
echo ""
echo "  1. 프로젝트 폴더로 이동:"
echo -e "     ${YELLOW}cd choomaru-mobile${NC}"
echo ""
echo "  2. 개발 서버 실행:"
echo -e "     ${YELLOW}npm run dev${NC}"
echo ""
echo "  3. 브라우저에서 확인:"
echo -e "     ${YELLOW}http://localhost:5173${NC}"
echo ""
echo "  4. 모바일에서 테스트 (ngrok):"
echo -e "     ${YELLOW}npx ngrok http 5173${NC}"
echo ""
echo -e "${BLUE}문서 참조:${NC}"
echo "  - 개발 가이드: mobile_app_development_guide.md"
echo "  - 빠른 시작: QUICK_START_MOBILE.md"
echo "  - 체크리스트: PROJECT_CHECKLIST.md"
echo ""
echo -e "${GREEN}Happy Coding! 🎭💃${NC}"
echo ""
