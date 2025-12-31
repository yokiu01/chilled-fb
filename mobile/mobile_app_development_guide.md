# 춤마루(Choomaru) 모바일 웹앱 개발 가이드
## Claude Code Agent 단계별 프롬프트 시리즈

---

## 📋 개발 프로세스 개요

```
단계 1: 모바일 앱 요구사항 분석 및 아키텍처 설계
   ↓
단계 2: 반응형 UI/UX 프레임워크 구축
   ↓
단계 3: 모바일 카메라 및 MediaPipe 최적화
   ↓
단계 4: PWA(Progressive Web App) 설정
   ↓
단계 5: 터치 인터페이스 및 제스처 구현
   ↓
단계 6: 성능 최적화 및 리소스 관리
   ↓
단계 7: 크로스 브라우저/디바이스 테스트
   ↓
단계 8: 배포 및 호스팅 설정
   ↓
종합: 통합 및 최종 검증
```

---

## 단계 1: 모바일 앱 요구사항 분석 및 아키텍처 설계

### 목적
현재 Streamlit 기반 데스크톱 웹앱(`app_v16.py`)을 분석하고, 모바일 웹앱으로 전환하기 위한 기술 스택 및 아키텍처를 설계합니다.

### Claude Code Agent 입력문

```
현재 디렉토리의 app_v16.py는 Streamlit 기반 춤 동작 감지 애플리케이션입니다.
다음 작업을 수행해주세요:

1. app_v16.py를 분석하여 다음 정보를 추출하세요:
   - 핵심 기능 목록 (MediaPipe Pose/Hands, 웹캠 처리, 데이터 저장 등)
   - 사용 중인 주요 라이브러리 및 의존성
   - 현재 페이지 구조 및 네비게이션 흐름
   - 세션 상태 관리 방식

2. 모바일 웹앱으로 전환을 위한 기술 스택을 제안하세요:
   - Streamlit은 모바일 최적화가 제한적이므로, 다음 중 하나를 선택:
     a) React + Vite (추천: 빠른 개발, 풍부한 모바일 라이브러리)
     b) Vue.js + Vite
     c) Vanilla JavaScript + Tailwind CSS (가벼움)
   - MediaPipe 웹 라이브러리 사용 (@mediapipe/tasks-vision)
   - PWA 지원을 위한 Service Worker 설정

3. 아키텍처 설계 문서를 작성하세요 (architecture.md):
   - 폴더 구조 제안
   - 컴포넌트 분리 전략
   - 상태 관리 방식 (Context API, Zustand, Pinia 등)
   - API/데이터 흐름 다이어그램
   - 모바일 최적화 전략 (이미지 압축, 레이지 로딩, 코드 스플리팅)

4. requirements_mobile.txt 생성:
   - 개발 서버 및 빌드 도구
   - MediaPipe JavaScript 라이브러리
   - UI 컴포넌트 라이브러리 (Material-UI, Vuetify, DaisyUI 등)
   - PWA 관련 패키지

출력 형식:
- architecture.md: 아키텍처 설계 문서
- tech_stack.md: 기술 스택 선정 이유 및 비교
- migration_plan.md: Streamlit → 모바일 웹앱 마이그레이션 계획
```

### 산출물
- `architecture.md`: 시스템 아키텍처 설계서
- `tech_stack.md`: 기술 스택 결정 문서
- `migration_plan.md`: 마이그레이션 로드맵

---

## 단계 2: 반응형 UI/UX 프레임워크 구축

### 목적
모바일 우선(Mobile-First) 반응형 UI 프레임워크를 구축하고, 기본 레이아웃과 컴포넌트 구조를 생성합니다.

### 이전 단계 연결
`architecture.md`에서 결정된 기술 스택과 컴포넌트 구조를 기반으로 실제 프로젝트를 초기화합니다.

### Claude Code Agent 입력문

```
architecture.md에 정의된 기술 스택을 기반으로 모바일 웹앱 프로젝트를 생성하세요.

1. 프로젝트 초기화:
   - React + Vite 프로젝트 생성 (또는 선택된 프레임워크)
   - 명령어: npm create vite@latest choomaru-mobile -- --template react
   - TypeScript 사용 권장

2. 필수 패키지 설치:
   ```json
   {
     "dependencies": {
       "@mediapipe/tasks-vision": "latest",
       "react-router-dom": "^6.x",
       "tailwindcss": "^3.x",
       "daisyui": "^4.x", // 또는 다른 UI 라이브러리
       "zustand": "^4.x", // 상태 관리
       "react-webcam": "^7.x"
     },
     "devDependencies": {
       "vite-plugin-pwa": "latest",
       "autoprefixer": "^10.x",
       "postcss": "^8.x"
     }
   }
   ```

3. 프로젝트 구조 생성:
   ```
   choomaru-mobile/
   ├── public/
   │   ├── models/          # MediaPipe 모델 파일
   │   ├── icons/           # PWA 아이콘
   │   └── manifest.json
   ├── src/
   │   ├── components/
   │   │   ├── common/      # 공통 컴포넌트
   │   │   │   ├── Header.jsx
   │   │   │   ├── Navigation.jsx
   │   │   │   └── LoadingSpinner.jsx
   │   │   ├── camera/      # 카메라 관련
   │   │   │   ├── WebcamCapture.jsx
   │   │   │   └── CameraControls.jsx
   │   │   └── pose/        # 자세 감지 관련
   │   │       ├── PoseVisualizer.jsx
   │   │       └── HandsVisualizer.jsx
   │   ├── pages/
   │   │   ├── HomePage.jsx
   │   │   ├── PoseTestPage.jsx
   │   │   └── GalleryPage.jsx
   │   ├── stores/
   │   │   └── appStore.js  # Zustand 상태 관리
   │   ├── utils/
   │   │   ├── mediapipe.js
   │   │   └── dataExport.js
   │   ├── styles/
   │   │   └── index.css
   │   ├── App.jsx
   │   └── main.jsx
   ├── tailwind.config.js
   ├── vite.config.js
   └── package.json
   ```

4. Tailwind CSS 및 DaisyUI 설정:
   - tailwind.config.js에 모바일 최적화 설정
   - 커스텀 브레이크포인트 정의 (sm: 640px, md: 768px, lg: 1024px)
   - 다크모드 지원 설정

5. 기본 레이아웃 컴포넌트 생성:
   - Header: 로고, 언어 선택, 메뉴 버튼
   - Navigation: 하단 네비게이션 바 (모바일 우선)
   - Layout: 메인 레이아웃 래퍼

6. 반응형 디자인 가이드라인 문서 작성 (responsive_guide.md):
   - 모바일 (< 768px): 단일 컬럼, 하단 네비게이션
   - 태블릿 (768px - 1024px): 2컬럼 레이아웃
   - 데스크톱 (> 1024px): 사이드바 + 메인 콘텐츠

모든 컴포넌트는 모바일 우선으로 설계하고, touch-friendly UI를 적용하세요.
(예: 최소 터치 타겟 44px, 충분한 간격, 스와이프 제스처 지원)
```

### 산출물
- `choomaru-mobile/` 프로젝트 폴더
- 기본 컴포넌트 구조
- `responsive_guide.md`: 반응형 디자인 가이드

---

## 단계 3: 모바일 카메라 및 MediaPipe 최적화

### 목적
모바일 디바이스의 카메라를 활용하여 MediaPipe Pose/Hands 감지를 구현하고, 성능을 최적화합니다.

### 이전 단계 연결
단계 2에서 생성된 컴포넌트 구조를 활용하여 카메라 및 MediaPipe 기능을 구현합니다.

### Claude Code Agent 입력문

```
모바일 환경에서 MediaPipe Pose 및 Hands 감지를 구현하세요.

1. MediaPipe 모델 파일 준비:
   - public/models/ 폴더에 다음 파일 복사:
     - pose_landmarker_lite.task (기존 models/에서)
     - hand_landmarker.task (기존 models/에서)
   - 모바일 최적화를 위해 lite 버전 사용

2. MediaPipe 초기화 유틸리티 작성 (src/utils/mediapipe.js):
   ```javascript
   import { PoseLandmarker, HandLandmarker, FilesetResolver } from '@mediapipe/tasks-vision';

   export class MediaPipeService {
     async initializePose(options = {}) {
       // PoseLandmarker 초기화
       // 모바일 최적화 설정: delegate: 'GPU' 사용
     }

     async initializeHands(options = {}) {
       // HandLandmarker 초기화
     }

     async detectPose(videoElement, timestamp) {
       // 프레임별 Pose 감지
     }

     async detectHands(videoElement, timestamp) {
       // 프레임별 Hands 감지
     }

     drawLandmarks(canvas, landmarks, type) {
       // Canvas에 랜드마크 그리기
       // Pose: 초록색, Hands: 마젠타색
     }

     cleanup() {
       // 리소스 정리
     }
   }
   ```

3. 모바일 웹캠 컴포넌트 작성 (src/components/camera/WebcamCapture.jsx):
   - react-webcam 또는 네이티브 getUserMedia() API 사용
   - 모바일 디바이스 카메라 권한 요청 처리
   - 전면/후면 카메라 전환 기능
   - 해상도 설정 (모바일: 640x480, 태블릿: 1280x720)
   - 자동 회전 처리 (orientation API)

4. 자세 감지 페이지 구현 (src/pages/PoseTestPage.jsx):
   - WebcamCapture 컴포넌트 통합
   - MediaPipe 초기화 및 실시간 감지 루프
   - Canvas 오버레이로 랜드마크 표시
   - FPS 카운터 표시
   - 상태 관리 (Zustand):
     ```javascript
     const usePoseStore = create((set) => ({
       isWebcamRunning: false,
       enablePose: true,
       enableHands: false,
       poseData: [],
       handData: [],
       settings: {
         detectionConfidence: 0.5,
         trackingConfidence: 0.5
       }
     }));
     ```

5. 성능 최적화:
   - requestAnimationFrame 사용하여 프레임 제어
   - 모바일에서 FPS 제한 (30fps 권장)
   - 메모리 누수 방지: useEffect cleanup
   - Web Worker 활용 고려 (MediaPipe 처리 오프로드)

6. 설정 패널 컴포넌트 (src/components/pose/SettingsPanel.jsx):
   - 감지 신뢰도 슬라이더
   - Pose/Hands 토글
   - 해상도 선택
   - 모바일 친화적 UI (큰 터치 타겟, 슬라이더)

7. 데이터 저장 기능 (src/utils/dataExport.js):
   - app_v16.py의 convert_landmarks_to_csv 로직을 JavaScript로 포팅
   - IndexedDB를 사용한 로컬 저장 (선택사항)
   - Blob API로 CSV/JSON 다운로드

8. 에러 처리:
   - 카메라 권한 거부 시 안내 메시지
   - MediaPipe 로딩 실패 시 폴백
   - 디바이스 미지원 감지 (GPU 없음 등)

모바일 성능을 고려하여 불필요한 렌더링을 최소화하고, React.memo() 및 useMemo()를 적극 활용하세요.
```

### 산출물
- `src/utils/mediapipe.js`: MediaPipe 서비스 클래스
- `src/components/camera/WebcamCapture.jsx`: 웹캠 컴포넌트
- `src/pages/PoseTestPage.jsx`: 자세 감지 페이지
- `src/utils/dataExport.js`: 데이터 내보내기 유틸리티

---

## 단계 4: PWA(Progressive Web App) 설정

### 목적
앱을 PWA로 변환하여 홈 화면 추가, 오프라인 지원, 푸시 알림 등의 네이티브 앱 기능을 제공합니다.

### 이전 단계 연결
단계 3에서 구현된 핵심 기능들을 PWA로 패키징합니다.

### Claude Code Agent 입력문

```
춤마루 모바일 웹앱을 PWA(Progressive Web App)로 변환하세요.

1. Vite PWA 플러그인 설정 (vite.config.js):
   ```javascript
   import { defineConfig } from 'vite'
   import react from '@vitejs/plugin-react'
   import { VitePWA } from 'vite-plugin-pwa'

   export default defineConfig({
     plugins: [
       react(),
       VitePWA({
         registerType: 'autoUpdate',
         includeAssets: ['models/*.task', 'icons/*.png'],
         manifest: {
           name: '춤마루 - Choomaru Dance Pose Tracker',
           short_name: 'Choomaru',
           description: 'AI 기반 춤 동작 감지 및 분석 앱',
           theme_color: '#667eea',
           background_color: '#ffffff',
           display: 'standalone',
           orientation: 'portrait',
           scope: '/',
           start_url: '/',
           icons: [
             {
               src: '/icons/icon-72x72.png',
               sizes: '72x72',
               type: 'image/png'
             },
             {
               src: '/icons/icon-192x192.png',
               sizes: '192x192',
               type: 'image/png',
               purpose: 'any maskable'
             },
             {
               src: '/icons/icon-512x512.png',
               sizes: '512x512',
               type: 'image/png'
             }
           ]
         },
         workbox: {
           globPatterns: ['**/*.{js,css,html,png,jpg,svg,woff2}'],
           runtimeCaching: [
             {
               urlPattern: /^https:\/\/cdn\.jsdelivr\.net\/.*/i,
               handler: 'CacheFirst',
               options: {
                 cacheName: 'mediapipe-cache',
                 expiration: {
                   maxEntries: 10,
                   maxAgeSeconds: 60 * 60 * 24 * 365 // 1년
                 }
               }
             }
           ]
         }
       })
     ]
   })
   ```

2. PWA 아이콘 생성:
   - 춤마루 로고를 기반으로 다양한 크기의 아이콘 생성
   - 필요 크기: 72x72, 96x96, 128x128, 144x144, 152x152, 192x192, 384x384, 512x512
   - public/icons/ 폴더에 저장
   - maskable icon 버전 포함 (안전 영역 고려)

3. Service Worker 커스터마이징 (필요시):
   - MediaPipe 모델 파일 사전 캐싱
   - 오프라인 폴백 페이지
   - Background Sync (데이터 저장 동기화)

4. Install Prompt 구현 (src/components/common/InstallPrompt.jsx):
   - PWA 설치 가능 시 안내 배너 표시
   - beforeinstallprompt 이벤트 활용
   - 사용자가 거부하면 로컬 스토리지에 저장하여 재표시 방지

5. 오프라인 지원:
   - 네트워크 상태 감지 컴포넌트
   - 오프라인 시 UI 업데이트 (배너 표시)
   - 캐시된 데이터로 기본 기능 제공

6. 앱 업데이트 알림:
   - Service Worker 업데이트 감지
   - 사용자에게 새 버전 알림 및 새로고침 버튼 제공

7. iOS Safari 대응:
   - apple-touch-icon 메타 태그 추가 (index.html)
   - apple-mobile-web-app-capable 설정
   - viewport 메타 태그 최적화

8. Android Chrome 대응:
   - theme-color 메타 태그
   - Web Share API 활용 (데이터 공유)

9. PWA 품질 검증:
   - Lighthouse PWA 감사 실행
   - 최소 요구사항 충족 확인:
     - HTTPS 제공
     - manifest.json 유효성
     - Service Worker 등록
     - 모바일 친화적 디자인
     - 빠른 로딩 속도 (< 3초)

모든 설정 후 npm run build 실행하여 PWA 빌드를 테스트하고,
Chrome DevTools의 Application 탭에서 manifest, Service Worker, 캐시 상태를 확인하세요.
```

### 산출물
- `vite.config.js`: PWA 설정
- `public/manifest.json`: 앱 매니페스트
- `public/icons/`: PWA 아이콘 세트
- `src/components/common/InstallPrompt.jsx`: 설치 프롬프트

---

## 단계 5: 터치 인터페이스 및 제스처 구현

### 목적
모바일 환경에 최적화된 터치 인터페이스와 제스처를 구현합니다.

### 이전 단계 연결
단계 2-4에서 구축된 UI 컴포넌트에 터치 인터랙션을 추가합니다.

### Claude Code Agent 입력문

```
모바일 터치 인터페이스 및 제스처 기능을 구현하세요.

1. 터치 제스처 라이브러리 설치:
   - react-use-gesture 또는 use-gesture 설치
   ```bash
   npm install @use-gesture/react
   ```

2. 스와이프 네비게이션 구현:
   - 페이지 간 스와이프로 이동
   - 설정 패널 스와이프로 열기/닫기
   - 예제 (src/components/common/SwipeableDrawer.jsx):
   ```javascript
   import { useSpring, animated } from '@react-spring/web'
   import { useDrag } from '@use-gesture/react'

   function SwipeableDrawer({ isOpen, onClose, children }) {
     const [{ x }, api] = useSpring(() => ({ x: 0 }))

     const bind = useDrag(({ down, movement: [mx], cancel }) => {
       if (mx > 100) {
         cancel()
         onClose()
       }
       api.start({ x: down ? mx : 0 })
     })

     return (
       <animated.div {...bind()} style={{ transform: x.to(x => `translateX(${x}px)`) }}>
         {children}
       </animated.div>
     )
   }
   ```

3. 핀치 줌 기능:
   - 웹캠 영상에 핀치 줌 적용
   - 갤러리 이미지 확대/축소

4. 터치 친화적 UI 개선:
   - 모든 버튼: 최소 44x44px 터치 영역
   - 슬라이더: 터치하기 쉬운 큰 thumb
   - 체크박스/토글: 큰 터치 영역
   - Ripple 효과 추가 (Material Design)

5. 길게 누르기(Long Press) 기능:
   - 갤러리 이미지 길게 눌러 옵션 메뉴 표시
   - 데이터 삭제 확인

6. 햅틱 피드백 (Vibration API):
   ```javascript
   const vibrate = (pattern = [10]) => {
     if ('vibrate' in navigator) {
       navigator.vibrate(pattern)
     }
   }

   // 버튼 클릭 시
   const handleClick = () => {
     vibrate([5])
     // 나머지 로직
   }
   ```

7. 터치 스크롤 최적화:
   - -webkit-overflow-scrolling: touch 적용
   - Momentum scrolling 활성화
   - 스크롤 바운스 제어

8. 제스처 충돌 방지:
   - 웹캠 영상 위 제스처 비활성화
   - 스크롤 vs. 스와이프 구분
   - preventDefault 적절히 사용

9. 접근성(Accessibility) 개선:
   - 터치 영역 시각적 표시 (포커스 상태)
   - 스크린 리더 지원
   - ARIA 레이블 추가

10. 가로/세로 모드 대응:
    - orientation change 이벤트 리스닝
    - 가로 모드 시 레이아웃 조정
    - 웹캠 비율 유지

모든 터치 인터랙션은 부드럽고 자연스러워야 하며,
60fps를 유지하도록 최적화하세요 (transform, opacity만 애니메이션).
```

### 산출물
- `src/components/common/SwipeableDrawer.jsx`: 스와이프 가능한 서랍
- `src/hooks/useGestures.js`: 커스텀 제스처 훅
- 터치 최적화된 UI 컴포넌트들

---

## 단계 6: 성능 최적화 및 리소스 관리

### 목적
모바일 환경의 제한된 리소스(CPU, 메모리, 배터리)에서 최적의 성능을 달성합니다.

### 이전 단계 연결
모든 기능이 구현된 상태에서 성능 병목 지점을 찾아 최적화합니다.

### Claude Code Agent 입력문

```
춤마루 모바일 앱의 성능을 최적화하세요.

1. 번들 크기 최적화:
   - Vite 빌드 분석: npm install -D rollup-plugin-visualizer
   ```javascript
   // vite.config.js
   import { visualizer } from 'rollup-plugin-visualizer'

   export default defineConfig({
     plugins: [
       visualizer({ open: true })
     ],
     build: {
       rollupOptions: {
         output: {
           manualChunks: {
             'mediapipe': ['@mediapipe/tasks-vision'],
             'vendor': ['react', 'react-dom', 'react-router-dom']
           }
         }
       }
     }
   })
   ```
   - 코드 스플리팅: React.lazy() 적용
   ```javascript
   const PoseTestPage = lazy(() => import('./pages/PoseTestPage'))
   const GalleryPage = lazy(() => import('./pages/GalleryPage'))
   ```

2. 이미지 최적화:
   - WebP 포맷 사용
   - 반응형 이미지 (srcset)
   - Lazy loading (loading="lazy")
   - 춤 동작 썸네일: 640px 이하로 리사이즈

3. MediaPipe 최적화:
   - 모바일에서 FPS 제한 (30fps)
   - GPU delegate 활성화
   - 불필요한 프레임 스킵
   ```javascript
   let lastProcessedTime = 0
   const FRAME_INTERVAL = 1000 / 30 // 30fps

   function processFrame(timestamp) {
     if (timestamp - lastProcessedTime >= FRAME_INTERVAL) {
       // MediaPipe 처리
       lastProcessedTime = timestamp
     }
     requestAnimationFrame(processFrame)
   }
   ```

4. 메모리 관리:
   - 웹캠 중지 시 리소스 정리
   ```javascript
   useEffect(() => {
     return () => {
       // Cleanup
       if (webcamRef.current) {
         const stream = webcamRef.current.srcObject
         stream?.getTracks().forEach(track => track.stop())
       }
       mediaPipeService.cleanup()
     }
   }, [])
   ```
   - 데이터 배열 크기 제한 (최대 1000 프레임)
   - 사용하지 않는 모델 언로드

5. 렌더링 최적화:
   - React.memo() 적용 (불필요한 리렌더링 방지)
   - useMemo(), useCallback() 활용
   - Virtual scrolling (긴 리스트)
   - Canvas 오프스크린 렌더링

6. 네트워크 최적화:
   - MediaPipe 모델 파일 gzip 압축
   - HTTP/2 사용
   - CDN 활용 (필요 시)
   - Prefetch/Preload 전략

7. 배터리 절약:
   - 백그라운드 시 웹캠 자동 중지 (Page Visibility API)
   ```javascript
   useEffect(() => {
     const handleVisibilityChange = () => {
       if (document.hidden) {
         // 웹캠 중지
         stopWebcam()
       }
     }
     document.addEventListener('visibilitychange', handleVisibilityChange)
     return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
   }, [])
   ```
   - Wake Lock API 사용 (웹캠 사용 중 화면 꺼짐 방지)

8. 로딩 성능:
   - Skeleton UI 구현 (로딩 중 표시)
   - Critical CSS 인라인
   - 폰트 최적화 (font-display: swap)

9. 성능 모니터링:
   - Web Vitals 측정
   ```javascript
   import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals'

   getCLS(console.log)
   getFID(console.log)
   getFCP(console.log)
   getLCP(console.log)
   getTTFB(console.log)
   ```

10. 성능 벤치마크 문서 작성 (performance_report.md):
    - Lighthouse 점수 (목표: 90+ 모든 항목)
    - 초기 로딩 시간 (목표: < 3초)
    - MediaPipe 처리 FPS (목표: 30fps 안정)
    - 메모리 사용량 (목표: < 150MB)

Chrome DevTools Performance 탭으로 프로파일링을 수행하고,
병목 지점을 문서화하세요.
```

### 산출물
- 최적화된 `vite.config.js`
- `performance_report.md`: 성능 벤치마크 리포트
- 최적화된 컴포넌트들

---

## 단계 7: 크로스 브라우저/디바이스 테스트

### 목적
다양한 모바일 브라우저와 디바이스에서 앱이 정상 작동하는지 검증합니다.

### 이전 단계 연결
최적화가 완료된 앱을 실제 디바이스와 환경에서 테스트합니다.

### Claude Code Agent 입력문

```
춤마루 모바일 앱의 크로스 브라우저/디바이스 호환성을 테스트하고 문제를 해결하세요.

1. 테스트 환경 구성:
   - BrowserStack 또는 LambdaTest 계정 생성 (무료 체험)
   - 로컬 개발 서버를 ngrok으로 외부 노출
   ```bash
   npm install -g ngrok
   ngrok http 5173
   ```

2. 테스트 대상 디바이스/브라우저:
   - iOS:
     - iPhone SE (2세대) - Safari 14+
     - iPhone 12/13 - Safari 15+
     - iPad Air - Safari 15+
   - Android:
     - Samsung Galaxy S21 - Chrome 100+
     - Google Pixel 6 - Chrome 100+
     - OnePlus 9 - Chrome/Samsung Internet
   - 브라우저:
     - Chrome Mobile (최신)
     - Safari iOS (최신)
     - Firefox Mobile
     - Samsung Internet

3. 기능별 테스트 체크리스트 (test_checklist.md 작성):
   ```markdown
   ## 카메라 기능
   - [ ] 카메라 권한 요청 정상 작동
   - [ ] 전면/후면 카메라 전환
   - [ ] 다양한 해상도 지원
   - [ ] 자동 회전 대응

   ## MediaPipe 감지
   - [ ] Pose 랜드마크 정확도
   - [ ] Hands 랜드마크 정확도
   - [ ] 실시간 처리 성능 (30fps 유지)
   - [ ] 메모리 누수 없음 (5분 이상 테스트)

   ## UI/UX
   - [ ] 터치 제스처 반응성
   - [ ] 스와이프 네비게이션
   - [ ] 버튼 터치 영역 적절
   - [ ] 가로/세로 모드 전환

   ## PWA
   - [ ] 홈 화면 추가 가능
   - [ ] 오프라인 동작 (Service Worker)
   - [ ] 설치 프롬프트 표시

   ## 데이터
   - [ ] CSV/JSON 다운로드
   - [ ] 데이터 저장/불러오기
   - [ ] 세션 상태 유지

   ## 성능
   - [ ] 초기 로딩 < 3초
   - [ ] FPS 30 이상 유지
   - [ ] 메모리 사용량 < 150MB
   ```

4. 브라우저별 이슈 해결:
   - iOS Safari:
     - getUserMedia 권한 문제 → HTTPS 필수 확인
     - WebGL 컨텍스트 손실 → 복구 로직 추가
     - 100vh 문제 → CSS calc() 또는 -webkit-fill-available 사용
   - Chrome Android:
     - 백그라운드 탭 성능 저하 → Page Visibility API
   - Samsung Internet:
     - Service Worker 버그 → polyfill 추가

5. 디바이스별 최적화:
   - 저사양 디바이스: 해상도 자동 조정
   - 고주사율 디스플레이: requestAnimationFrame 최적화
   - 노치/펀치홀: safe-area-inset 적용
   ```css
   .header {
     padding-top: env(safe-area-inset-top);
   }
   .navigation {
     padding-bottom: env(safe-area-inset-bottom);
   }
   ```

6. 자동화 테스트 스크립트 작성 (선택사항):
   - Playwright 또는 Cypress를 사용한 E2E 테스트
   ```javascript
   // tests/e2e/pose-test.spec.js
   import { test, expect } from '@playwright/test'

   test('pose detection flow', async ({ page, context }) => {
     await context.grantPermissions(['camera'])
     await page.goto('/')
     await page.click('text=동작 테스트')
     await page.click('text=웹캠 시작')
     await expect(page.locator('.canvas')).toBeVisible()
   })
   ```

7. 접근성 테스트:
   - axe DevTools 실행
   - 스크린 리더 테스트 (iOS VoiceOver, Android TalkBack)
   - 키보드 네비게이션

8. 테스트 결과 문서화 (test_results.md):
   - 각 디바이스/브라우저별 테스트 결과
   - 발견된 이슈 및 해결 방법
   - 미해결 이슈 및 제한사항

모든 주요 디바이스에서 핵심 기능이 정상 작동하는지 확인하고,
호환성 이슈는 polyfill 또는 기능 감지(feature detection)로 해결하세요.
```

### 산출물
- `test_checklist.md`: 테스트 체크리스트
- `test_results.md`: 테스트 결과 리포트
- 브라우저 호환성 수정사항

---

## 단계 8: 배포 및 호스팅 설정

### 목적
모바일 웹앱을 프로덕션 환경에 배포하고, HTTPS, 도메인, CDN을 설정합니다.

### 이전 단계 연결
테스트가 완료된 앱을 실제 사용자가 접근할 수 있도록 배포합니다.

### Claude Code Agent 입력문

```
춤마루 모바일 웹앱을 프로덕션 환경에 배포하세요.

1. 빌드 최적화:
   ```bash
   npm run build
   ```
   - dist/ 폴더 생성 확인
   - 번들 크기 확인 (gzip 압축 후 < 500KB 권장)
   - Source map 제거 또는 분리

2. 호스팅 플랫폼 선택 및 배포:

   **옵션 A: Vercel (추천 - 가장 간편)**
   ```bash
   npm install -g vercel
   vercel --prod
   ```
   - vercel.json 설정:
   ```json
   {
     "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }],
     "headers": [
       {
         "source": "/models/(.*)",
         "headers": [
           { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
         ]
       }
     ]
   }
   ```

   **옵션 B: Netlify**
   ```bash
   npm install -g netlify-cli
   netlify deploy --prod
   ```
   - netlify.toml 설정:
   ```toml
   [build]
     publish = "dist"
     command = "npm run build"

   [[redirects]]
     from = "/*"
     to = "/index.html"
     status = 200

   [[headers]]
     for = "/models/*"
     [headers.values]
       Cache-Control = "public, max-age=31536000, immutable"
   ```

   **옵션 C: GitHub Pages**
   - vite.config.js에 base 설정
   ```javascript
   export default defineConfig({
     base: '/choomaru-mobile/',
     // ...
   })
   ```
   - gh-pages 패키지 사용
   ```bash
   npm install -D gh-pages
   npm run build
   npx gh-pages -d dist
   ```

3. 커스텀 도메인 설정:
   - 도메인 구매 (예: choomaru.app)
   - DNS 설정:
     - A 레코드 또는 CNAME 레코드 추가
     - Vercel/Netlify 제공 IP/도메인 연결
   - HTTPS 자동 설정 확인 (Let's Encrypt)

4. 환경 변수 설정:
   - .env.production 파일 생성
   ```
   VITE_API_URL=https://api.choomaru.app
   VITE_ANALYTICS_ID=G-XXXXXXXXXX
   ```
   - 호스팅 플랫폼에 환경 변수 등록

5. CDN 설정 (선택사항):
   - MediaPipe 모델 파일을 Cloudflare CDN에 업로드
   - 로딩 속도 개선

6. 분석 및 모니터링 설정:
   - Google Analytics 4 통합
   ```javascript
   // src/utils/analytics.js
   import ReactGA from 'react-ga4'

   export const initGA = () => {
     ReactGA.initialize(import.meta.env.VITE_ANALYTICS_ID)
   }

   export const logPageView = () => {
     ReactGA.send({ hitType: "pageview", page: window.location.pathname })
   }
   ```
   - Sentry 에러 트래킹 (선택사항)
   ```bash
   npm install @sentry/react
   ```

7. robots.txt 및 sitemap.xml 생성:
   - public/robots.txt
   ```
   User-agent: *
   Allow: /
   Sitemap: https://choomaru.app/sitemap.xml
   ```
   - public/sitemap.xml (페이지 목록)

8. 보안 헤더 설정:
   - Content-Security-Policy
   - X-Frame-Options
   - Permissions-Policy (camera 권한)

9. 성능 검증:
   - 배포된 URL에서 Lighthouse 실행
   - PageSpeed Insights 점수 확인
   - 목표: Performance 90+, PWA 100

10. 배포 문서 작성 (deployment_guide.md):
    - 배포 URL
    - 배포 프로세스
    - CI/CD 파이프라인 설정 (GitHub Actions)
    - 롤백 절차
    - 모니터링 대시보드 링크

GitHub Actions를 사용한 자동 배포 워크플로우도 설정하세요:
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run build
      - uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```
```

### 산출물
- 배포된 프로덕션 앱 URL
- `deployment_guide.md`: 배포 가이드
- CI/CD 파이프라인 설정

---

## 종합 프롬프트: 모든 단계 통합 및 최종 검증

### 목적
모든 개발 단계를 종합하여 완성된 모바일 웹앱을 검증하고, 최종 문서를 작성합니다.

### Claude Code Agent 입력문

```
춤마루 모바일 웹앱의 모든 개발 단계를 통합하고 최종 검증을 수행하세요.

1. 전체 기능 통합 검증:
   - 모든 페이지 간 네비게이션 정상 작동 확인
   - 데이터 흐름 검증 (상태 관리 → UI → 로컬 저장)
   - MediaPipe Pose/Hands 동시 작동 테스트
   - PWA 기능 전체 확인 (설치, 오프라인, 알림)

2. 최종 성능 벤치마크:
   - Lighthouse CI 실행하여 점수 측정
   ```bash
   npm install -g @lhci/cli
   lhci autorun --upload.target=temporary-public-storage
   ```
   - 목표 달성 확인:
     - Performance: 90+
     - Accessibility: 90+
     - Best Practices: 90+
     - SEO: 90+
     - PWA: 100

3. 모바일 디바이스 실제 테스트:
   - QR 코드 생성하여 실제 디바이스에서 접속
   - 최소 3개 디바이스에서 전체 기능 테스트
   - 테스트 시나리오:
     1. 앱 접속 → 홈 화면 추가
     2. 동작 테스트 페이지 진입 → 카메라 권한 허용
     3. Pose 감지 활성화 → 정상 작동 확인
     4. Hands 토글 → 동시 감지 확인
     5. 데이터 저장 → CSV 다운로드
     6. 네트워크 끊기 → 오프라인 동작 확인

4. 종합 문서 작성:

   **README.md 업데이트:**
   ```markdown
   # 춤마루 (Choomaru) - Mobile Web App

   ## 소개
   AI 기반 춤 동작 감지 및 분석 모바일 웹앱

   ## 주요 기능
   - MediaPipe Pose/Hands 실시간 감지
   - PWA 지원 (홈 화면 추가, 오프라인)
   - 터치 최적화 UI
   - 데이터 내보내기 (CSV/JSON)

   ## 기술 스택
   - React 18 + Vite
   - MediaPipe Tasks Vision
   - Tailwind CSS + DaisyUI
   - Zustand (상태 관리)
   - Workbox (Service Worker)

   ## 설치 및 실행
   ```bash
   npm install
   npm run dev
   ```

   ## 빌드
   ```bash
   npm run build
   npm run preview
   ```

   ## 배포
   - Production URL: https://choomaru.app
   - Staging URL: https://staging.choomaru.app

   ## 브라우저 지원
   - Chrome Mobile 100+
   - Safari iOS 14+
   - Firefox Mobile 100+

   ## 라이선스
   MIT
   ```

   **USER_GUIDE.md 작성:**
   - 앱 사용 방법 (스크린샷 포함)
   - 기능별 설명
   - FAQ
   - 문제 해결 가이드

   **CONTRIBUTING.md 작성:**
   - 개발 환경 설정
   - 코드 스타일 가이드
   - Pull Request 프로세스

5. 버전 관리:
   - package.json 버전 업데이트 (1.0.0)
   - CHANGELOG.md 작성
   ```markdown
   # Changelog

   ## [1.0.0] - 2024-XX-XX
   ### Added
   - MediaPipe Pose 및 Hands 실시간 감지
   - PWA 지원
   - 모바일 최적화 UI
   - 데이터 내보내기 기능
   ```

6. 코드 품질 검증:
   - ESLint 실행: `npm run lint`
   - Prettier 포맷팅: `npm run format`
   - TypeScript 타입 체크: `npm run type-check`
   - 테스트 실행: `npm run test`

7. 최종 체크리스트:
   - [ ] 모든 기능 정상 작동
   - [ ] Lighthouse 점수 90+ 달성
   - [ ] 실제 디바이스 테스트 완료
   - [ ] PWA 설치 가능
   - [ ] HTTPS 배포 완료
   - [ ] 문서 작성 완료
   - [ ] GitHub 리포지토리 정리
   - [ ] 프로덕션 모니터링 설정

8. 향후 개선 사항 문서화 (ROADMAP.md):
   ```markdown
   # Roadmap

   ## v1.1 (예정)
   - [ ] 손동작 제스처 인식
   - [ ] 춤 동작 라이브러리 확장
   - [ ] 소셜 공유 기능
   - [ ] 다크 모드 개선

   ## v1.2 (계획)
   - [ ] 멀티플레이어 모드
   - [ ] 동작 비교 분석
   - [ ] 튜토리얼 비디오
   ```

9. 프로젝트 아카이빙:
   - 모든 소스 코드 GitHub에 푸시
   - 릴리즈 노트 작성 (v1.0.0 태그)
   - 배포 환경 백업

10. 최종 리포트 생성 (FINAL_REPORT.md):
    - 프로젝트 개요
    - 달성된 목표
    - 기술적 도전과 해결 방법
    - 성능 지표
    - 학습 내용
    - 감사 인사

모든 단계가 완료되면, 프로젝트가 프로덕션에 배포되고
사용자가 실제로 사용할 수 있는 상태임을 확인하세요.
```

### 최종 산출물
- ✅ 완성된 모바일 웹앱 (프로덕션 배포)
- ✅ 종합 문서 세트 (README, USER_GUIDE, CONTRIBUTING, ROADMAP, CHANGELOG)
- ✅ 성능 벤치마크 리포트
- ✅ 최종 검증 체크리스트
- ✅ GitHub 리포지토리 (버전 관리 완료)

---

## 📊 프로젝트 타임라인 (예상)

| 단계 | 예상 소요 시간 | 난이도 |
|------|---------------|--------|
| 단계 1: 요구사항 분석 | 2-4시간 | 중 |
| 단계 2: UI 프레임워크 | 4-6시간 | 중 |
| 단계 3: MediaPipe 통합 | 6-8시간 | 상 |
| 단계 4: PWA 설정 | 2-3시간 | 중 |
| 단계 5: 터치 인터페이스 | 3-4시간 | 중 |
| 단계 6: 성능 최적화 | 4-6시간 | 상 |
| 단계 7: 테스트 | 3-5시간 | 중 |
| 단계 8: 배포 | 2-3시간 | 하 |
| 종합: 통합 및 검증 | 2-3시간 | 중 |
| **총계** | **28-42시간** | - |

---

## 🎯 핵심 성공 지표

1. **성능**
   - 초기 로딩: < 3초
   - MediaPipe FPS: 30fps 이상
   - Lighthouse Performance: 90+

2. **호환성**
   - iOS Safari 14+ 지원
   - Chrome Mobile 100+ 지원
   - 주요 Android 디바이스 지원

3. **사용성**
   - PWA 설치율: 목표 20%
   - 카메라 권한 승인율: 목표 80%
   - 평균 세션 시간: 목표 5분+

4. **품질**
   - 크리티컬 버그: 0개
   - Lighthouse PWA: 100점
   - 접근성 점수: 90+

---

## 📝 주의사항

1. **각 단계는 순차적으로 진행**하되, 병행 가능한 작업은 동시 진행 가능
2. **이전 단계의 산출물**을 다음 단계에서 참조하므로, 문서화가 중요
3. **모바일 실제 디바이스 테스트**는 필수 (에뮬레이터만으로는 불충분)
4. **성능 최적화**는 지속적으로 모니터링 필요
5. **보안**: HTTPS 필수, 카메라 권한 명확한 안내

---

## 🔗 추가 리소스

- [MediaPipe Web 공식 문서](https://developers.google.com/mediapipe/solutions/vision/pose_landmarker/web_js)
- [PWA 체크리스트](https://web.dev/pwa-checklist/)
- [React 성능 최적화](https://react.dev/learn/render-and-commit)
- [Vite PWA 플러그인](https://vite-pwa-org.netlify.app/)
- [Web Vitals](https://web.dev/vitals/)

---

**생성일**: 2024-XX-XX
**버전**: 1.0
**작성자**: Claude Code Agent Prompt Designer
