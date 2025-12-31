# 춤마루 모바일 웹앱 빠른 시작 가이드

## 🚀 5분 안에 시작하기

이 가이드는 개발자가 최소한의 시간으로 춤마루 모바일 웹앱 개발을 시작할 수 있도록 돕습니다.

---

## 전제 조건

```bash
# Node.js 18+ 설치 확인
node --version  # v18.0.0 이상

# npm 확인
npm --version   # 9.0.0 이상
```

---

## 단계별 빠른 설정

### 1단계: 프로젝트 생성 (2분)

```bash
# React + Vite 프로젝트 생성
npm create vite@latest choomaru-mobile -- --template react

# 프로젝트 폴더로 이동
cd choomaru-mobile

# 의존성 설치
npm install
```

### 2단계: 필수 패키지 설치 (1분)

```bash
# MediaPipe 및 주요 라이브러리 설치
npm install @mediapipe/tasks-vision react-router-dom zustand react-webcam

# UI 라이브러리 (Tailwind CSS + DaisyUI)
npm install -D tailwindcss postcss autoprefixer daisyui
npx tailwindcss init -p

# PWA 플러그인
npm install -D vite-plugin-pwa
```

### 3단계: Tailwind 설정 (30초)

**tailwind.config.js:**
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [require('daisyui')],
  daisyui: {
    themes: ["light", "dark"],
  },
}
```

**src/index.css:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### 4단계: 기본 구조 생성 (1분)

```bash
# 폴더 구조 생성
mkdir -p src/{components,pages,stores,utils}/{common,camera,pose}
mkdir -p public/{models,icons}
```

### 5단계: MediaPipe 모델 복사 (30초)

```bash
# 기존 모델 파일을 public/models/로 복사
cp ../models/pose_landmarker_lite.task public/models/
cp ../models/hand_landmarker.task public/models/
```

---

## 개발 서버 실행

```bash
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

---

## 다음 단계

이제 `mobile_app_development_guide.md`의 **단계 2**부터 진행하세요:
- 컴포넌트 구조 생성
- 라우팅 설정
- 상태 관리 구현

---

## 유용한 명령어

```bash
# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build

# 빌드 미리보기
npm run preview

# 린트 검사
npm run lint
```

---

## 모바일 디바이스에서 테스트

### ngrok 사용 (권장)

```bash
# ngrok 설치
npm install -g ngrok

# 개발 서버 실행 (터미널 1)
npm run dev

# ngrok 실행 (터미널 2)
ngrok http 5173

# ngrok이 제공하는 HTTPS URL을 모바일에서 접속
# 예: https://abc123.ngrok.io
```

### 로컬 네트워크 사용

```bash
# vite.config.js에서 host 설정
export default defineConfig({
  server: {
    host: '0.0.0.0',
    port: 5173
  }
})

# PC의 로컬 IP 확인 (Windows)
ipconfig

# PC의 로컬 IP 확인 (Mac/Linux)
ifconfig

# 모바일에서 http://[로컬IP]:5173 접속
# 예: http://192.168.0.10:5173
```

---

## 문제 해결

### 카메라가 작동하지 않음
- ✅ HTTPS 사용 확인 (ngrok 또는 localhost)
- ✅ 브라우저 카메라 권한 확인
- ✅ 다른 앱에서 카메라 사용 중인지 확인

### MediaPipe 모델 로딩 실패
- ✅ public/models/ 폴더에 .task 파일 존재 확인
- ✅ 파일 경로 확인 (/models/pose_landmarker_lite.task)
- ✅ 브라우저 콘솔에서 네트워크 오류 확인

### 성능이 느림
- ✅ FPS 제한 적용 (30fps)
- ✅ 해상도 낮추기 (640x480)
- ✅ GPU delegate 활성화 확인

---

## 추가 리소스

- 📘 [전체 개발 가이드](./mobile_app_development_guide.md)
- 🎨 [DaisyUI 컴포넌트](https://daisyui.com/components/)
- 📱 [MediaPipe Web 문서](https://developers.google.com/mediapipe)
- ⚡ [Vite 공식 문서](https://vitejs.dev/)

---

**다음**: [단계 2 - UI 프레임워크 구축](./mobile_app_development_guide.md#단계-2-반응형-uiux-프레임워크-구축)
