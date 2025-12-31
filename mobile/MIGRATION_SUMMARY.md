# Streamlit → React 모바일 웹앱 마이그레이션 요약

## 📊 마이그레이션 개요

이 문서는 app_v16.py (Streamlit 기반)를 React 모바일 웹앱으로 전환하는 과정을 요약합니다.

---

## 🔄 기술 스택 변환

| 항목 | 기존 (Streamlit) | 신규 (React) |
|------|------------------|--------------|
| **언어** | Python | JavaScript/JSX |
| **프레임워크** | Streamlit | React 18 + Vite |
| **UI 라이브러리** | Streamlit 컴포넌트 | Tailwind CSS + DaisyUI |
| **상태 관리** | st.session_state | Zustand |
| **라우팅** | st.session_state.current_step | React Router |
| **MediaPipe** | mediapipe (Python) | @mediapipe/tasks-vision (JS) |
| **웹캠** | cv2.VideoCapture | getUserMedia API |
| **데이터 저장** | Pandas → CSV | Blob API → CSV/JSON |
| **배포** | Streamlit Cloud | Vercel/Netlify (PWA) |

---

## 📦 주요 컴포넌트 매핑

### Streamlit → React 컴포넌트 변환

| Streamlit 함수/컴포넌트 | React 컴포넌트 | 위치 |
|-------------------------|----------------|------|
| `st.set_page_config()` | `<meta>` tags in index.html | public/index.html |
| `st.markdown()` | `<div>` with Tailwind | 각 컴포넌트 |
| `st.button()` | `<button className="btn">` | UI 컴포넌트 |
| `st.slider()` | `<input type="range">` | SettingsPanel.jsx |
| `st.checkbox()` | `<input type="checkbox">` | SettingsPanel.jsx |
| `st.selectbox()` | `<select>` | SettingsPanel.jsx |
| `st.columns()` | `<div className="grid">` | Layout |
| `st.sidebar` | SwipeableDrawer | SwipeableDrawer.jsx |
| `st.empty()` | `useState()` + conditional render | 각 컴포넌트 |
| `st.rerun()` | `navigate()` (React Router) | 라우팅 |

---

## 🎯 핵심 기능 변환 가이드

### 1. 웹캠 처리

**기존 (Python):**
```python
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

ret, frame = cap.read()
frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
```

**신규 (JavaScript):**
```javascript
const videoConstraints = {
  width: 640,
  height: 480,
  facingMode: "user"
}

<Webcam
  audio={false}
  videoConstraints={videoConstraints}
  ref={webcamRef}
/>

// 프레임 캡처
const imageSrc = webcamRef.current.getScreenshot()
```

---

### 2. MediaPipe 초기화

**기존 (Python):**
```python
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    min_pose_detection_confidence=0.5
)

landmarker = vision.PoseLandmarker.create_from_options(options)
```

**신규 (JavaScript):**
```javascript
import { PoseLandmarker, FilesetResolver } from '@mediapipe/tasks-vision'

const vision = await FilesetResolver.forVisionTasks(
  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision/wasm"
)

const poseLandmarker = await PoseLandmarker.createFromOptions(vision, {
  baseOptions: {
    modelAssetPath: '/models/pose_landmarker_lite.task',
    delegate: "GPU"
  },
  runningMode: "VIDEO",
  minPoseDetectionConfidence: 0.5
})
```

---

### 3. 실시간 감지 루프

**기존 (Python):**
```python
while st.session_state.webcam_running:
    ret, frame = cap.read()
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
    detection_result = landmarker.detect_for_video(mp_image, frame_timestamp_ms)

    # 랜드마크 그리기
    frame_rgb = draw_landmarks_on_image(frame_rgb, detection_result)

    video_placeholder.image(frame_rgb, channels="RGB")
```

**신규 (JavaScript):**
```javascript
const detectPose = useCallback(() => {
  if (!webcamRef.current || !poseLandmarker) return

  const video = webcamRef.current.video
  const timestamp = performance.now()

  poseLandmarker.detectForVideo(video, timestamp, (result) => {
    // Canvas에 랜드마크 그리기
    drawLandmarks(canvasRef.current, result)
  })

  requestAnimationFrame(detectPose)
}, [poseLandmarker])

useEffect(() => {
  if (isRunning) {
    detectPose()
  }
}, [isRunning, detectPose])
```

---

### 4. 상태 관리

**기존 (Python):**
```python
if 'webcam_running' not in st.session_state:
    st.session_state.webcam_running = False

if 'pose_landmarks_data' not in st.session_state:
    st.session_state.pose_landmarks_data = []

# 상태 변경
st.session_state.webcam_running = True
```

**신규 (JavaScript):**
```javascript
// stores/appStore.js
import create from 'zustand'

export const useAppStore = create((set) => ({
  isWebcamRunning: false,
  poseLandmarksData: [],

  setWebcamRunning: (value) => set({ isWebcamRunning: value }),
  addPoseLandmark: (data) => set((state) => ({
    poseLandmarksData: [...state.poseLandmarksData, data]
  }))
}))

// 컴포넌트에서 사용
const { isWebcamRunning, setWebcamRunning } = useAppStore()
```

---

### 5. 데이터 내보내기

**기존 (Python):**
```python
def convert_landmarks_to_csv(pose_landmarks_data, hand_landmarks_data):
    # CSV 생성 로직
    csv_data = # ...
    return csv_data

st.download_button(
    "📥 CSV 다운로드",
    data=csv_data,
    file_name="landmarks.csv",
    mime="text/csv"
)
```

**신규 (JavaScript):**
```javascript
const exportToCSV = (poseData, handData) => {
  // CSV 문자열 생성
  const csvContent = generateCSV(poseData, handData)

  // Blob 생성
  const blob = new Blob([csvContent], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)

  // 다운로드
  const link = document.createElement('a')
  link.href = url
  link.download = `landmarks_${Date.now()}.csv`
  link.click()

  URL.revokeObjectURL(url)
}

<button onClick={() => exportToCSV(poseData, handData)}>
  📥 CSV 다운로드
</button>
```

---

### 6. 랜드마크 그리기

**기존 (Python):**
```python
def draw_landmarks_on_image(rgb_image, detection_result):
    annotated_image = np.copy(rgb_image)
    height, width, _ = annotated_image.shape

    for pose_landmarks in detection_result.pose_landmarks:
        for connection in POSE_CONNECTIONS:
            start_idx, end_idx = connection
            start_landmark = pose_landmarks[start_idx]
            end_landmark = pose_landmarks[end_idx]

            start_point = (int(start_landmark.x * width),
                          int(start_landmark.y * height))
            end_point = (int(end_landmark.x * width),
                        int(end_landmark.y * height))

            cv2.line(annotated_image, start_point, end_point, (0, 255, 0), 2)

    return annotated_image
```

**신규 (JavaScript):**
```javascript
const drawLandmarks = (canvas, result) => {
  const ctx = canvas.getContext('2d')
  const { width, height } = canvas

  ctx.clearRect(0, 0, width, height)

  if (!result.landmarks) return

  for (const landmarks of result.landmarks) {
    // 연결선 그리기
    POSE_CONNECTIONS.forEach(([start, end]) => {
      const startLandmark = landmarks[start]
      const endLandmark = landmarks[end]

      ctx.beginPath()
      ctx.moveTo(startLandmark.x * width, startLandmark.y * height)
      ctx.lineTo(endLandmark.x * width, endLandmark.y * height)
      ctx.strokeStyle = '#00ff00'
      ctx.lineWidth = 2
      ctx.stroke()
    })

    // 랜드마크 점 그리기
    landmarks.forEach((landmark) => {
      ctx.beginPath()
      ctx.arc(landmark.x * width, landmark.y * height, 5, 0, 2 * Math.PI)
      ctx.fillStyle = '#ff0000'
      ctx.fill()
    })
  }
}
```

---

## 🚀 성능 최적화 차이

| 항목 | Streamlit | React PWA |
|------|-----------|-----------|
| **초기 로딩** | 느림 (서버 의존) | 빠름 (정적 파일) |
| **반응 속도** | 느림 (재렌더링) | 빠름 (Virtual DOM) |
| **오프라인** | 불가능 | 가능 (Service Worker) |
| **모바일 최적화** | 제한적 | 완전 최적화 |
| **번들 크기** | N/A (서버) | ~500KB (gzip) |
| **설치** | 불가능 | 가능 (PWA) |

---

## 📱 모바일 최적화 추가 기능

React 앱에서만 가능한 모바일 기능:

1. **터치 제스처**
   - 스와이프 네비게이션
   - 핀치 줌
   - 길게 누르기

2. **PWA 기능**
   - 홈 화면 추가
   - 오프라인 동작
   - 푸시 알림 (선택사항)
   - 백그라운드 동기화

3. **디바이스 API**
   - 화면 회전 대응
   - 햅틱 피드백
   - Wake Lock (화면 켜짐 유지)
   - 전면/후면 카메라 전환

4. **성능**
   - 코드 스플리팅
   - Lazy loading
   - Image optimization
   - Service Worker 캐싱

---

## ⚠️ 주의사항

### 변환 시 고려할 점

1. **비동기 처리**
   - Python의 동기 코드 → JavaScript의 비동기(async/await)

2. **데이터 타입**
   - NumPy 배열 → JavaScript Array/TypedArray
   - Pandas DataFrame → JavaScript Object Array

3. **이미지 처리**
   - OpenCV → Canvas API 또는 OffscreenCanvas

4. **파일 시스템**
   - Python의 파일 쓰기 → Blob API + 다운로드

5. **에러 처리**
   - Streamlit의 st.error() → try-catch + UI 알림

---

## 📚 참고 자료

### Streamlit 문서
- [Streamlit API Reference](https://docs.streamlit.io/library/api-reference)
- [Streamlit Components](https://docs.streamlit.io/library/components)

### React/JavaScript 문서
- [React Documentation](https://react.dev/)
- [MediaPipe Web](https://developers.google.com/mediapipe/solutions/vision/pose_landmarker/web_js)
- [Web APIs](https://developer.mozilla.org/en-US/docs/Web/API)

### 변환 도구
- [Python to JavaScript Syntax Comparison](https://www.codecademy.com/resources/blog/python-vs-javascript/)
- [NumPy to JavaScript](https://github.com/numpy/numpy.js)

---

## ✅ 마이그레이션 체크리스트

- [ ] app_v16.py 전체 분석 완료
- [ ] 핵심 기능 목록 추출
- [ ] React 프로젝트 초기화
- [ ] MediaPipe JavaScript 버전 테스트
- [ ] 웹캠 기능 구현
- [ ] Pose 감지 구현
- [ ] Hands 감지 구현
- [ ] 상태 관리 구현
- [ ] 데이터 저장/내보내기 구현
- [ ] UI/UX 모바일 최적화
- [ ] PWA 설정
- [ ] 성능 최적화
- [ ] 크로스 브라우저 테스트
- [ ] 배포
- [ ] 문서화

---

**결론**: Streamlit 앱의 핵심 로직은 유지하되, UI와 사용자 경험은 모바일에 최적화된 React PWA로 완전히 재구성합니다.
