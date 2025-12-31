# 춤마루 모바일 웹앱 기술 스택 비교

## 개요

Streamlit 기반 데스크톱 앱을 모바일 웹앱으로 전환하기 위한 기술 스택을 비교 분석합니다.

---

## 🎯 평가 기준

| 기준 | 가중치 | 설명 |
|------|--------|------|
| 모바일 최적화 | ⭐⭐⭐⭐⭐ | 터치, 제스처, 성능 |
| 개발 속도 | ⭐⭐⭐⭐ | 학습 곡선, 생산성 |
| MediaPipe 호환성 | ⭐⭐⭐⭐⭐ | JavaScript 라이브러리 지원 |
| PWA 지원 | ⭐⭐⭐⭐ | 오프라인, 설치 |
| 커뮤니티/생태계 | ⭐⭐⭐ | 라이브러리, 문서 |
| 번들 크기 | ⭐⭐⭐⭐ | 초기 로딩 속도 |

---

## 옵션 1: React + Vite ⭐ 추천

### 장점
✅ **모바일 최적화**: React Native Web 컴포넌트 재사용 가능
✅ **개발 속도**: 풍부한 UI 라이브러리 (Material-UI, Ant Design, DaisyUI)
✅ **MediaPipe**: 공식 예제가 React 기반
✅ **PWA**: vite-plugin-pwa로 간편한 설정
✅ **생태계**: 가장 큰 커뮤니티, 무수한 라이브러리
✅ **Vite**: 빠른 HMR, 최적화된 빌드
✅ **TypeScript**: 타입 안전성 (선택사항)

### 단점
❌ 번들 크기가 Vue보다 약간 큼 (React + ReactDOM)
❌ 상태 관리 라이브러리 별도 필요 (Zustand, Redux)

### 번들 크기 (gzip)
- React + ReactDOM: ~45KB
- Router: ~10KB
- UI 라이브러리: ~50KB (DaisyUI)
- **총 기본**: ~105KB

### 적합성 점수: 95/100

### 샘플 코드
```jsx
import { useState, useEffect } from 'react'
import { PoseLandmarker } from '@mediapipe/tasks-vision'

function PoseTest() {
  const [pose, setPose] = useState(null)

  useEffect(() => {
    // MediaPipe 초기화
  }, [])

  return (
    <div className="container mx-auto p-4">
      <button className="btn btn-primary">
        웹캠 시작
      </button>
    </div>
  )
}
```

---

## 옵션 2: Vue.js + Vite

### 장점
✅ **가벼움**: 번들 크기가 React보다 작음
✅ **학습 곡선**: 단순하고 직관적
✅ **반응성**: Composition API로 깔끔한 코드
✅ **PWA**: Vue CLI PWA 플러그인
✅ **Vite**: React와 동일한 빌드 도구

### 단점
❌ MediaPipe 공식 예제가 적음
❌ 모바일 UI 라이브러리가 React보다 적음
❌ 커뮤니티가 React보다 작음

### 번들 크기 (gzip)
- Vue 3: ~35KB
- Router: ~8KB
- UI 라이브러리: ~40KB (Vuetify)
- **총 기본**: ~83KB

### 적합성 점수: 85/100

### 샘플 코드
```vue
<script setup>
import { ref, onMounted } from 'vue'
import { PoseLandmarker } from '@mediapipe/tasks-vision'

const pose = ref(null)

onMounted(() => {
  // MediaPipe 초기화
})
</script>

<template>
  <div class="container">
    <button @click="startWebcam" class="btn">
      웹캠 시작
    </button>
  </div>
</template>
```

---

## 옵션 3: Vanilla JavaScript + Tailwind CSS

### 장점
✅ **초경량**: 프레임워크 오버헤드 없음
✅ **성능**: 최고 성능 (Virtual DOM 없음)
✅ **학습 필요 없음**: 순수 JavaScript
✅ **번들 크기**: 가장 작음

### 단점
❌ 개발 속도 느림 (컴포넌트 재사용 어려움)
❌ 상태 관리 복잡
❌ 라우팅 직접 구현 필요
❌ 코드 유지보수 어려움

### 번들 크기 (gzip)
- Tailwind CSS: ~10KB (필요한 클래스만)
- **총 기본**: ~10KB + 앱 코드

### 적합성 점수: 60/100

### 샘플 코드
```javascript
import { PoseLandmarker } from '@mediapipe/tasks-vision'

class PoseApp {
  constructor() {
    this.pose = null
    this.init()
  }

  init() {
    document.getElementById('start-btn')
      .addEventListener('click', () => this.startWebcam())
  }

  startWebcam() {
    // 웹캠 로직
  }
}

new PoseApp()
```

---

## 옵션 4: Next.js (React 프레임워크)

### 장점
✅ **SEO**: SSR/SSG 지원
✅ **라우팅**: 파일 기반 자동 라우팅
✅ **최적화**: 이미지, 폰트 자동 최적화
✅ **API Routes**: 백엔드 통합 가능

### 단점
❌ **오버킬**: 단순 PWA에는 과함
❌ **번들 크기**: 큼
❌ **복잡성**: 서버 컴포넌트 개념 추가
❌ **SSR 불필요**: 카메라 앱은 CSR만으로 충분

### 적합성 점수: 70/100

---

## 옵션 5: Svelte + SvelteKit

### 장점
✅ **초경량**: 컴파일러 기반 (런타임 작음)
✅ **성능**: Virtual DOM 없음
✅ **간결한 문법**: 가장 적은 코드량

### 단점
❌ **생태계**: React/Vue보다 작음
❌ **MediaPipe 예제**: 거의 없음
❌ **모바일 UI 라이브러리**: 선택지 적음
❌ **학습 필요**: 새로운 프레임워크 학습

### 적합성 점수: 75/100

---

## 📊 종합 비교표

| 항목 | React + Vite | Vue + Vite | Vanilla JS | Next.js | Svelte |
|------|--------------|------------|------------|---------|--------|
| 모바일 최적화 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 개발 속도 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| MediaPipe 호환 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| PWA 지원 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 생태계 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 번들 크기 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **총점** | **95** | **85** | **60** | **70** | **75** |

---

## 🏆 최종 권장: React + Vite

### 선정 이유

1. **MediaPipe 공식 지원**
   - Google MediaPipe 문서의 모든 예제가 React 기반
   - @mediapipe/tasks-vision 라이브러리와 완벽 호환

2. **풍부한 모바일 UI 라이브러리**
   - DaisyUI (Tailwind 기반, 가볍고 예쁨)
   - Material-UI (Google Material Design)
   - Chakra UI (접근성 우수)
   - Ant Design Mobile

3. **PWA 생태계**
   - vite-plugin-pwa (자동 Service Worker 생성)
   - Workbox 통합
   - 오프라인 지원 간편

4. **개발 생산성**
   - React DevTools
   - 풍부한 커뮤니티 리소스
   - Stack Overflow 답변 많음

5. **향후 확장성**
   - React Native로 네이티브 앱 전환 가능
   - Capacitor/Ionic과 통합 가능

---

## 대안 시나리오

### 시나리오 1: 번들 크기가 최우선
→ **Vue.js + Vite** 선택

### 시나리오 2: 최고 성능 + 경량
→ **Svelte** 선택

### 시나리오 3: SEO 중요 (춤 튜토리얼 콘텐츠)
→ **Next.js** 선택

### 시나리오 4: 학습 시간 없음
→ **Vanilla JS** 선택 (비추천)

---

## 선택된 기술 스택 세부사항

### 코어
- **프레임워크**: React 18
- **빌드 도구**: Vite 5
- **언어**: JavaScript (TypeScript 옵션)

### UI/스타일
- **CSS 프레임워크**: Tailwind CSS 3
- **컴포넌트 라이브러리**: DaisyUI
- **애니메이션**: Framer Motion (선택사항)

### 라우팅/상태
- **라우팅**: React Router 6
- **상태 관리**: Zustand (경량) 또는 Jotai

### 카메라/AI
- **MediaPipe**: @mediapipe/tasks-vision
- **웹캠**: react-webcam 또는 네이티브 API

### PWA
- **Service Worker**: vite-plugin-pwa
- **캐싱**: Workbox

### 유틸리티
- **날짜**: date-fns
- **아이콘**: Heroicons 또는 Lucide React
- **제스처**: @use-gesture/react

---

## 마이그레이션 경로

```
Streamlit (Python)
    ↓
[데이터 구조 분석]
    ↓
React Components (JavaScript)
    ↓
MediaPipe Web API
    ↓
PWA (모바일 웹앱)
    ↓
[선택사항] React Native (네이티브 앱)
```

---

## 참고 자료

- [React 공식 문서](https://react.dev/)
- [Vite 공식 문서](https://vitejs.dev/)
- [MediaPipe Web](https://developers.google.com/mediapipe/solutions/vision/pose_landmarker/web_js)
- [Tailwind CSS](https://tailwindcss.com/)
- [DaisyUI](https://daisyui.com/)
- [Zustand](https://github.com/pmndrs/zustand)

---

**결론**: React + Vite는 춤마루 모바일 웹앱에 가장 적합한 기술 스택입니다.
