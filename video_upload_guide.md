# 춤마루 영상 업로드 가이드 🎬

## 📹 영상 배치 위치

### 1. **38초 전문가 영상** 
**위치**: `결과 페이지` → "🎥 전문가 영상 보기" 섹션
**용도**: DNA 타입 확인 후 시청하는 종합 시연 영상
**코드 위치**: `app.py` 599번째 줄
```python
# st.video("path/to/expert_dance_38sec.mp4")
```

### 2. **5초 시범 동작 영상들** 
**위치**: `동작 따라하기 페이지` → "🎥 전문가 시범 영상" 섹션
**용도**: 각 동작별 개별 시범 (5개 동작)
**코드 위치**: `app.py` 693번째 줄
```python
# st.video(current_pose_videos[st.session_state.current_pose])
```

## 🎯 영상 업로드 방법

### **옵션 1: 로컬 파일 업로드**
```python
# 프로젝트 폴더에 videos 디렉토리 생성
videos/
├── expert_dance_38sec.mp4           # 38초 종합 영상
├── prayer_5sec.mp4           # 합장 시범
├── sunrise_5sec.mp4          # 해돋이 시범
├── swan_5sec.mp4             # 백조 시범
├── petal_5sec.mp4            # 꽃잎 시범
└── bow_5sec.mp4              # 인사 시범
```

### **옵션 2: YouTube 업로드 후 연결**
1. YouTube에 영상 업로드
2. URL 복사하여 코드에 입력

### **옵션 3: 웹 호스팅 (추천)**
- GitHub, Google Drive, Dropbox 등에 업로드
- 직접 링크 사용

## 🔧 코드 수정 방법

### 1. **38초 영상 연결**
```python
# 599번째 줄 수정
st.video("videos/expert_dance_38sec.mp4")
# 또는
st.video("https://youtube.com/watch?v=YOUR_VIDEO_ID")
```

### 2. **5초 시범 영상들 연결**
```python
# 670번째 줄 딕셔너리 수정
current_pose_videos = {
    0: "videos/prayer_5sec.mp4",    # 합장
    1: "videos/sunrise_5sec.mp4",   # 해돋이
    2: "videos/swan_5sec.mp4",      # 백조
    3: "videos/petal_5sec.mp4",     # 꽃잎
    4: "videos/bow_5sec.mp4"        # 인사
}
```

## 📱 현재 화면 구성

### **동작 따라하기 페이지**
```
┌─────────────────┬─────────────────┐
│  🎥 전문가 시범  │   📹 내 웹캠     │
│   (5초 영상)    │   (사용자)      │
└─────────────────┴─────────────────┘
┌─────────────────┬─────────────────┐
│  ✨ 동작 확인    │  ⏭️ 다음 동작   │
│     버튼        │     버튼        │
└─────────────────┴─────────────────┘
```

영상 파일을 준비하시면 바로 연결해드리겠습니다! 🎭✨
