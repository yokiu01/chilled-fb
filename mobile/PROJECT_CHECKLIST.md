# 춤마루 모바일 웹앱 개발 체크리스트

각 단계별로 완료해야 할 작업을 체크리스트 형식으로 정리했습니다.

---

## 📋 단계 1: 요구사항 분석 및 아키텍처 설계

### 분석 작업
- [ ] app_v16.py 파일 읽기 및 구조 파악
- [ ] 핵심 기능 목록 추출
  - [ ] MediaPipe Pose 감지
  - [ ] MediaPipe Hands 감지
  - [ ] 웹캠 제어 (시작/중지)
  - [ ] 설정 관리 (신뢰도, 해상도)
  - [ ] 데이터 저장 (CSV/JSON)
  - [ ] 랜드마크 시각화
- [ ] 현재 의존성 목록 작성
- [ ] 페이지 플로우 다이어그램 작성

### 기술 스택 결정
- [ ] React vs Vue vs Vanilla JS 비교
- [ ] 상태 관리 라이브러리 선택 (Zustand 권장)
- [ ] UI 라이브러리 선택 (DaisyUI 권장)
- [ ] PWA 도구 선택 (vite-plugin-pwa)

### 문서 작성
- [ ] architecture.md 작성
  - [ ] 폴더 구조 정의
  - [ ] 컴포넌트 계층 구조
  - [ ] 데이터 흐름도
- [ ] tech_stack.md 작성
  - [ ] 선택된 기술과 이유
  - [ ] 대안 및 비교
- [ ] migration_plan.md 작성
  - [ ] Streamlit → React 변환 전략
  - [ ] 단계별 마일스톤

---

## 📋 단계 2: 반응형 UI/UX 프레임워크 구축

### 프로젝트 초기화
- [ ] Vite 프로젝트 생성
  ```bash
  npm create vite@latest choomaru-mobile -- --template react
  ```
- [ ] Git 초기화
  ```bash
  git init
  git add .
  git commit -m "Initial commit"
  ```

### 패키지 설치
- [ ] 코어 의존성
  - [ ] react-router-dom
  - [ ] zustand
  - [ ] @mediapipe/tasks-vision
- [ ] UI 라이브러리
  - [ ] tailwindcss
  - [ ] daisyui
  - [ ] @headlessui/react (선택사항)
- [ ] 유틸리티
  - [ ] react-webcam
  - [ ] @use-gesture/react
- [ ] 개발 도구
  - [ ] vite-plugin-pwa
  - [ ] autoprefixer
  - [ ] postcss

### 폴더 구조 생성
- [ ] src/components/
  - [ ] common/ (Header, Navigation, LoadingSpinner)
  - [ ] camera/ (WebcamCapture, CameraControls)
  - [ ] pose/ (PoseVisualizer, HandsVisualizer, SettingsPanel)
- [ ] src/pages/
  - [ ] HomePage.jsx
  - [ ] PoseTestPage.jsx
  - [ ] GalleryPage.jsx (선택사항)
- [ ] src/stores/
  - [ ] appStore.js
- [ ] src/utils/
  - [ ] mediapipe.js
  - [ ] dataExport.js
- [ ] public/
  - [ ] models/
  - [ ] icons/

### 설정 파일
- [ ] tailwind.config.js 설정
  - [ ] DaisyUI 플러그인 추가
  - [ ] 커스텀 브레이크포인트
  - [ ] 다크모드 설정
- [ ] vite.config.js 기본 설정
  - [ ] 포트 설정
  - [ ] 프록시 설정 (필요시)
- [ ] .gitignore 확인

### 기본 컴포넌트 작성
- [ ] App.jsx (라우터 설정)
- [ ] Layout.jsx (공통 레이아웃)
- [ ] Header.jsx (로고, 메뉴)
- [ ] Navigation.jsx (하단 네비게이션)
- [ ] LoadingSpinner.jsx

### 라우팅 설정
- [ ] React Router 설정
- [ ] 페이지 경로 정의
  - [ ] / (홈)
  - [ ] /pose-test (자세 감지)
  - [ ] /gallery (갤러리, 선택사항)

### 반응형 디자인
- [ ] 모바일 우선 CSS 작성
- [ ] 터치 타겟 크기 확인 (최소 44px)
- [ ] 타이포그래피 스케일 정의
- [ ] 색상 팔레트 정의

### 테스트
- [ ] 개발 서버 실행 확인
- [ ] 라우팅 동작 확인
- [ ] 모바일 시뮬레이터에서 확인 (Chrome DevTools)

---

## 📋 단계 3: 모바일 카메라 및 MediaPipe 최적화

### MediaPipe 모델 준비
- [ ] pose_landmarker_lite.task 복사
- [ ] hand_landmarker.task 복사
- [ ] 모델 파일 경로 확인

### MediaPipe 서비스 구현
- [ ] src/utils/mediapipe.js 작성
  - [ ] MediaPipeService 클래스
  - [ ] initializePose() 메서드
  - [ ] initializeHands() 메서드
  - [ ] detectPose() 메서드
  - [ ] detectHands() 메서드
  - [ ] drawLandmarks() 메서드
  - [ ] cleanup() 메서드

### 웹캠 컴포넌트
- [ ] src/components/camera/WebcamCapture.jsx 작성
  - [ ] getUserMedia() 권한 요청
  - [ ] 전면/후면 카메라 전환
  - [ ] 해상도 설정
  - [ ] 에러 처리

### 자세 감지 페이지
- [ ] src/pages/PoseTestPage.jsx 작성
  - [ ] 웹캠 컴포넌트 통합
  - [ ] MediaPipe 초기화
  - [ ] 실시간 감지 루프 (requestAnimationFrame)
  - [ ] Canvas 오버레이
  - [ ] FPS 카운터

### 상태 관리
- [ ] Zustand 스토어 작성 (src/stores/appStore.js)
  - [ ] isWebcamRunning
  - [ ] enablePose
  - [ ] enableHands
  - [ ] poseData
  - [ ] handData
  - [ ] settings (detectionConfidence, trackingConfidence)

### 설정 패널
- [ ] src/components/pose/SettingsPanel.jsx 작성
  - [ ] 감지 신뢰도 슬라이더
  - [ ] 추적 신뢰도 슬라이더
  - [ ] Pose/Hands 토글
  - [ ] 해상도 선택

### 데이터 저장
- [ ] src/utils/dataExport.js 작성
  - [ ] convertToCSV() 함수
  - [ ] convertToJSON() 함수
  - [ ] downloadFile() 함수

### 성능 최적화
- [ ] FPS 제한 적용 (30fps)
- [ ] React.memo() 적용
- [ ] useMemo() / useCallback() 활용
- [ ] 메모리 누수 방지 (useEffect cleanup)

### 테스트
- [ ] 웹캠 시작/중지 동작 확인
- [ ] Pose 랜드마크 정확도 확인
- [ ] Hands 랜드마크 정확도 확인
- [ ] 성능 모니터링 (Chrome DevTools Performance)
- [ ] 메모리 사용량 확인

---

## 📋 단계 4: PWA 설정

### Vite PWA 플러그인 설정
- [ ] vite-plugin-pwa 설치
- [ ] vite.config.js에 PWA 설정 추가
  - [ ] manifest 정의
  - [ ] workbox 설정
  - [ ] 캐싱 전략

### Manifest 작성
- [ ] public/manifest.json 생성 (또는 vite.config.js에 포함)
  - [ ] name, short_name
  - [ ] description
  - [ ] theme_color, background_color
  - [ ] display: "standalone"
  - [ ] orientation: "portrait"
  - [ ] icons 배열

### 아이콘 생성
- [ ] 72x72 아이콘
- [ ] 96x96 아이콘
- [ ] 128x128 아이콘
- [ ] 144x144 아이콘
- [ ] 152x152 아이콘
- [ ] 192x192 아이콘 (maskable)
- [ ] 384x384 아이콘
- [ ] 512x512 아이콘
- [ ] public/icons/ 폴더에 저장

### Service Worker
- [ ] 자동 생성 확인 (vite-plugin-pwa)
- [ ] 캐싱 전략 테스트
- [ ] MediaPipe 모델 사전 캐싱

### 설치 프롬프트
- [ ] src/components/common/InstallPrompt.jsx 작성
  - [ ] beforeinstallprompt 이벤트 리스닝
  - [ ] 설치 배너 UI
  - [ ] 사용자 거부 시 로컬 스토리지 저장

### 오프라인 지원
- [ ] 네트워크 상태 감지
- [ ] 오프라인 시 UI 표시
- [ ] 캐시된 리소스로 기본 기능 제공

### iOS Safari 대응
- [ ] apple-touch-icon 메타 태그 추가
- [ ] apple-mobile-web-app-capable 설정
- [ ] viewport 메타 태그 최적화

### Android Chrome 대응
- [ ] theme-color 메타 태그
- [ ] Web Share API 통합 (선택사항)

### PWA 검증
- [ ] Lighthouse PWA 감사 실행
- [ ] HTTPS 배포 확인
- [ ] Service Worker 등록 확인
- [ ] Manifest 유효성 확인

---

## 📋 단계 5: 터치 인터페이스 및 제스처 구현

### 제스처 라이브러리 설치
- [ ] @use-gesture/react 설치
- [ ] @react-spring/web 설치 (선택사항)

### 스와이프 네비게이션
- [ ] src/components/common/SwipeableDrawer.jsx 작성
- [ ] 페이지 간 스와이프
- [ ] 설정 패널 스와이프

### 핀치 줌
- [ ] 웹캠 영상 핀치 줌
- [ ] 갤러리 이미지 확대/축소 (선택사항)

### 터치 UI 개선
- [ ] 모든 버튼 터치 영역 44px 이상
- [ ] 슬라이더 thumb 크기 확대
- [ ] 체크박스/토글 터치 영역 확대
- [ ] Ripple 효과 추가

### 길게 누르기
- [ ] 갤러리 이미지 길게 눌러 옵션 (선택사항)
- [ ] 햅틱 피드백 (Vibration API)

### 터치 스크롤 최적화
- [ ] -webkit-overflow-scrolling: touch 적용
- [ ] Momentum scrolling 활성화

### 가로/세로 모드
- [ ] orientation change 이벤트 리스닝
- [ ] 가로 모드 레이아웃 조정

### 접근성
- [ ] 터치 영역 시각적 표시
- [ ] ARIA 레이블 추가
- [ ] 스크린 리더 테스트

---

## 📋 단계 6: 성능 최적화 및 리소스 관리

### 번들 크기 최적화
- [ ] rollup-plugin-visualizer 설치
- [ ] 번들 분석 실행
- [ ] 코드 스플리팅 (React.lazy)
  - [ ] PoseTestPage lazy load
  - [ ] GalleryPage lazy load
- [ ] manualChunks 설정

### 이미지 최적화
- [ ] WebP 포맷 사용
- [ ] 반응형 이미지 (srcset)
- [ ] lazy loading 적용

### MediaPipe 최적화
- [ ] FPS 제한 (30fps)
- [ ] GPU delegate 활성화
- [ ] 프레임 스킵 로직

### 메모리 관리
- [ ] 웹캠 중지 시 리소스 정리
- [ ] MediaPipe 모델 언로드
- [ ] 데이터 배열 크기 제한

### 렌더링 최적화
- [ ] React.memo() 적용
- [ ] useMemo() 적용
- [ ] useCallback() 적용
- [ ] Canvas 오프스크린 렌더링

### 네트워크 최적화
- [ ] MediaPipe 모델 gzip 압축
- [ ] HTTP/2 사용
- [ ] Prefetch/Preload 전략

### 배터리 절약
- [ ] Page Visibility API 구현
- [ ] 백그라운드 시 웹캠 중지
- [ ] Wake Lock API (화면 꺼짐 방지)

### 로딩 성능
- [ ] Skeleton UI 구현
- [ ] Critical CSS 인라인
- [ ] 폰트 최적화 (font-display: swap)

### 성능 모니터링
- [ ] Web Vitals 측정
  - [ ] CLS (Cumulative Layout Shift)
  - [ ] FID (First Input Delay)
  - [ ] FCP (First Contentful Paint)
  - [ ] LCP (Largest Contentful Paint)
  - [ ] TTFB (Time to First Byte)

### 성능 벤치마크
- [ ] Lighthouse 점수 (목표: 90+)
- [ ] 초기 로딩 시간 (목표: < 3초)
- [ ] MediaPipe FPS (목표: 30fps)
- [ ] 메모리 사용량 (목표: < 150MB)

---

## 📋 단계 7: 크로스 브라우저/디바이스 테스트

### 테스트 환경 구성
- [ ] ngrok 설치 및 설정
- [ ] BrowserStack 계정 (선택사항)

### iOS 테스트
- [ ] iPhone SE - Safari 14+
- [ ] iPhone 12/13 - Safari 15+
- [ ] iPad Air - Safari 15+

### Android 테스트
- [ ] Samsung Galaxy S21 - Chrome
- [ ] Google Pixel 6 - Chrome
- [ ] OnePlus 9 - Chrome/Samsung Internet

### 기능 테스트
- [ ] 카메라 권한 요청
- [ ] 전면/후면 카메라 전환
- [ ] Pose 감지 정확도
- [ ] Hands 감지 정확도
- [ ] 터치 제스처
- [ ] PWA 설치
- [ ] 오프라인 동작
- [ ] 데이터 다운로드

### 브라우저별 이슈 해결
- [ ] iOS Safari 이슈
  - [ ] getUserMedia 권한
  - [ ] 100vh 문제
  - [ ] WebGL 컨텍스트
- [ ] Chrome Android 이슈
- [ ] Samsung Internet 이슈

### 디바이스별 최적화
- [ ] 저사양 디바이스 해상도 조정
- [ ] 노치/펀치홀 대응 (safe-area-inset)

### 접근성 테스트
- [ ] axe DevTools 실행
- [ ] iOS VoiceOver 테스트
- [ ] Android TalkBack 테스트
- [ ] 키보드 네비게이션

### 테스트 문서화
- [ ] test_checklist.md 작성
- [ ] test_results.md 작성

---

## 📋 단계 8: 배포 및 호스팅 설정

### 빌드
- [ ] npm run build 실행
- [ ] dist/ 폴더 확인
- [ ] 번들 크기 확인 (< 500KB gzip)
- [ ] Source map 제거

### 호스팅 선택
- [ ] Vercel (권장)
- [ ] Netlify
- [ ] GitHub Pages
- [ ] 기타 (Cloudflare Pages, Firebase)

### 배포 설정
- [ ] 배포 명령어 실행
- [ ] 환경 변수 설정
- [ ] 리다이렉트 규칙 설정
- [ ] 캐시 헤더 설정

### 도메인 설정
- [ ] 커스텀 도메인 구매 (선택사항)
- [ ] DNS 설정
- [ ] HTTPS 인증서 (자동 - Let's Encrypt)

### 분석 설정
- [ ] Google Analytics 4 통합
- [ ] Sentry 에러 트래킹 (선택사항)

### SEO
- [ ] robots.txt 생성
- [ ] sitemap.xml 생성
- [ ] 메타 태그 최적화

### 보안 헤더
- [ ] Content-Security-Policy
- [ ] X-Frame-Options
- [ ] Permissions-Policy

### CI/CD
- [ ] GitHub Actions 워크플로우 설정
- [ ] 자동 배포 파이프라인

### 검증
- [ ] 배포 URL 접속 확인
- [ ] Lighthouse 점수 확인
- [ ] 모바일 디바이스 테스트

### 문서 작성
- [ ] deployment_guide.md 작성
- [ ] 배포 URL 기록
- [ ] 롤백 절차 문서화

---

## 📋 종합: 최종 검증

### 전체 기능 통합
- [ ] 모든 페이지 네비게이션 확인
- [ ] 데이터 흐름 검증
- [ ] Pose + Hands 동시 작동 확인
- [ ] PWA 전체 기능 확인

### 성능 벤치마크
- [ ] Lighthouse CI 실행
- [ ] Performance: 90+
- [ ] Accessibility: 90+
- [ ] Best Practices: 90+
- [ ] SEO: 90+
- [ ] PWA: 100

### 실제 디바이스 테스트
- [ ] QR 코드 생성
- [ ] 최소 3개 디바이스 테스트
- [ ] 전체 시나리오 테스트

### 문서 작성
- [ ] README.md 업데이트
- [ ] USER_GUIDE.md 작성
- [ ] CONTRIBUTING.md 작성
- [ ] CHANGELOG.md 작성
- [ ] ROADMAP.md 작성
- [ ] FINAL_REPORT.md 작성

### 코드 품질
- [ ] ESLint 실행
- [ ] Prettier 포맷팅
- [ ] TypeScript 타입 체크 (선택사항)
- [ ] 테스트 실행

### 최종 체크리스트
- [ ] 모든 기능 정상 작동
- [ ] Lighthouse 90+ 달성
- [ ] 실제 디바이스 테스트 완료
- [ ] PWA 설치 가능
- [ ] HTTPS 배포 완료
- [ ] 문서 작성 완료
- [ ] GitHub 정리
- [ ] 모니터링 설정

### 프로젝트 완료
- [ ] GitHub 릴리즈 (v1.0.0)
- [ ] 팀/사용자 공유
- [ ] 피드백 수집 시스템 준비

---

## ✅ 완료 기준

각 단계는 다음 조건을 모두 충족해야 완료로 간주:

1. ✅ 체크리스트 모든 항목 완료
2. ✅ 코드가 에러 없이 실행
3. ✅ 테스트 통과
4. ✅ 문서화 완료
5. ✅ Git 커밋 및 푸시

---

**Tip**: 각 주요 단계 완료 시마다 Git commit을 하여 롤백 가능하도록 하세요!

```bash
git add .
git commit -m "Complete Step X: [단계명]"
git push
```
