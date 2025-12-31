@echo off
REM 춤마루 모바일 웹앱 프로젝트 자동 설정 스크립트 (Windows)
REM 사용법: setup-mobile-project.bat

echo.
echo ========================================
echo 춤마루(Choomaru) 모바일 웹앱 프로젝트 설정
echo ========================================
echo.

REM 1. Node.js 버전 확인
echo [1/10] Node.js 버전 확인 중...
node -v > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js가 설치되어 있지 않습니다.
    echo https://nodejs.org 에서 Node.js 18 이상을 설치하세요.
    pause
    exit /b 1
)
echo [OK] Node.js 확인 완료
echo.

REM 2. Vite 프로젝트 생성
echo [2/10] React + Vite 프로젝트 생성 중...
if exist choomaru-mobile (
    echo [WARNING] choomaru-mobile 폴더가 이미 존재합니다.
    set /p CONFIRM="덮어쓰시겠습니까? (y/n): "
    if /i "%CONFIRM%"=="y" (
        rmdir /s /q choomaru-mobile
    ) else (
        echo 설정을 취소합니다.
        pause
        exit /b 0
    )
)

call npm create vite@latest choomaru-mobile -- --template react
cd choomaru-mobile
echo [OK] 프로젝트 생성 완료
echo.

REM 3. 기본 의존성 설치
echo [3/10] 기본 의존성 설치 중...
call npm install
echo [OK] 기본 의존성 설치 완료
echo.

REM 4. 추가 패키지 설치
echo [4/10] 추가 패키지 설치 중...
echo   - MediaPipe, Router, 상태 관리, 웹캠...
call npm install @mediapipe/tasks-vision react-router-dom zustand react-webcam
echo [OK] 코어 패키지 설치 완료
echo.

REM 5. UI 라이브러리 설치
echo [5/10] UI 라이브러리 설치 중...
call npm install -D tailwindcss postcss autoprefixer daisyui
call npx tailwindcss init -p
echo [OK] Tailwind CSS + DaisyUI 설치 완료
echo.

REM 6. PWA 플러그인 설치
echo [6/10] PWA 플러그인 설치 중...
call npm install -D vite-plugin-pwa
echo [OK] PWA 플러그인 설치 완료
echo.

REM 7. 제스처 라이브러리 설치
echo [7/10] 제스처 라이브러리 설치 중...
call npm install @use-gesture/react @react-spring/web
echo [OK] 제스처 라이브러리 설치 완료
echo.

REM 8. 폴더 구조 생성
echo [8/10] 프로젝트 폴더 구조 생성 중...
mkdir src\components\common 2>nul
mkdir src\components\camera 2>nul
mkdir src\components\pose 2>nul
mkdir src\pages 2>nul
mkdir src\stores 2>nul
mkdir src\utils 2>nul
mkdir src\hooks 2>nul
mkdir src\styles 2>nul
mkdir public\models 2>nul
mkdir public\icons 2>nul
echo [OK] 폴더 구조 생성 완료
echo.

REM 9. Tailwind 설정 업데이트
echo [9/10] Tailwind CSS 설정 중...

echo /** @type {import('tailwindcss').Config} */ > tailwind.config.js
echo export default { >> tailwind.config.js
echo   content: [ >> tailwind.config.js
echo     "./index.html", >> tailwind.config.js
echo     "./src/**/*.{js,ts,jsx,tsx}", >> tailwind.config.js
echo   ], >> tailwind.config.js
echo   theme: { >> tailwind.config.js
echo     extend: { >> tailwind.config.js
echo       colors: { >> tailwind.config.js
echo         primary: '#667eea', >> tailwind.config.js
echo         secondary: '#764ba2', >> tailwind.config.js
echo       }, >> tailwind.config.js
echo     }, >> tailwind.config.js
echo   }, >> tailwind.config.js
echo   plugins: [require('daisyui')], >> tailwind.config.js
echo   daisyui: { >> tailwind.config.js
echo     themes: ["light", "dark"], >> tailwind.config.js
echo   }, >> tailwind.config.js
echo } >> tailwind.config.js

echo @tailwind base; > src\index.css
echo @tailwind components; >> src\index.css
echo @tailwind utilities; >> src\index.css
echo. >> src\index.css
echo /* 모바일 최적화 */ >> src\index.css
echo * { >> src\index.css
echo   -webkit-tap-highlight-color: transparent; >> src\index.css
echo   touch-action: manipulation; >> src\index.css
echo } >> src\index.css

echo [OK] Tailwind CSS 설정 완료
echo.

REM 10. MediaPipe 모델 복사
echo [10/10] MediaPipe 모델 파일 복사 중...
if exist ..\models\pose_landmarker_lite.task (
    copy ..\models\pose_landmarker_lite.task public\models\ > nul
    echo [OK] pose_landmarker_lite.task 복사 완료
) else (
    echo [WARNING] ..\models\pose_landmarker_lite.task 파일을 찾을 수 없습니다.
    echo            public\models\ 폴더에 수동으로 복사하세요.
)

if exist ..\models\hand_landmarker.task (
    copy ..\models\hand_landmarker.task public\models\ > nul
    echo [OK] hand_landmarker.task 복사 완료
) else (
    echo [WARNING] ..\models\hand_landmarker.task 파일을 찾을 수 없습니다.
    echo            public\models\ 폴더에 수동으로 복사하세요.
)
echo.

REM Git 초기화
echo Git 저장소 초기화 중...
git init > nul 2>&1

echo # Logs > .gitignore
echo logs >> .gitignore
echo *.log >> .gitignore
echo. >> .gitignore
echo # Dependencies >> .gitignore
echo node_modules/ >> .gitignore
echo. >> .gitignore
echo # Production >> .gitignore
echo dist/ >> .gitignore
echo dist-ssr/ >> .gitignore
echo. >> .gitignore
echo # Env files >> .gitignore
echo .env >> .gitignore
echo .env.local >> .gitignore
echo. >> .gitignore
echo # Editor >> .gitignore
echo .vscode/ >> .gitignore
echo .idea/ >> .gitignore
echo. >> .gitignore
echo # OS >> .gitignore
echo .DS_Store >> .gitignore
echo Thumbs.db >> .gitignore

git add . > nul 2>&1
git commit -m "Initial commit: Choomaru mobile web app setup" > nul 2>&1
echo [OK] Git 저장소 초기화 완료
echo.

REM 완료 메시지
echo.
echo ========================================
echo ✨ 춤마루 모바일 웹앱 프로젝트 설정 완료! ✨
echo ========================================
echo.
echo 다음 단계:
echo.
echo   1. 프로젝트 폴더로 이동:
echo      cd choomaru-mobile
echo.
echo   2. 개발 서버 실행:
echo      npm run dev
echo.
echo   3. 브라우저에서 확인:
echo      http://localhost:5173
echo.
echo   4. 모바일에서 테스트 (ngrok):
echo      npx ngrok http 5173
echo.
echo 문서 참조:
echo   - 개발 가이드: mobile_app_development_guide.md
echo   - 빠른 시작: QUICK_START_MOBILE.md
echo   - 체크리스트: PROJECT_CHECKLIST.md
echo.
echo Happy Coding! 🎭💃
echo.

pause
