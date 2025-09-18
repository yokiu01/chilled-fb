# 춤마루 (Choomaru) MVP

한국의 몸짓을 MZ세대 감성으로 재해석한 인터랙티브 웹 애플리케이션

## 🎭 프로젝트 개요

춤마루는 전통 한국무용을 현대적으로 재해석하여 젊은 세대가 쉽게 접근할 수 있도록 만든 플랫폼입니다. 간단한 퀴즈를 통해 개인의 "춤 DNA"를 분석하고, 웹캠을 통해 전통 동작을 따라하며, 개인화된 밈을 생성할 수 있습니다.

## ✨ 주요 기능

### 🧬 춤 DNA 분석
- 8개의 MZ세대 친화적 질문
- 8가지 춤 DNA 타입 분류 (Flow, Burst, Ground, Air, Solo, Harmony, Grace, Power)
- 개인 맞춤형 결과 페이지

### 💃 동작 따라하기
- 5가지 한국 전통 동작
  - 🙏 합장 (Prayer Pose)
  - 🌅 해돋이 자세 (Sunrise Pose)
  - 🦢 백조 자세 (Swan Pose)
  - 🌸 꽃잎 자세 (Petal Pose)
  - 🎭 인사 자세 (Bow Pose)
- MediaPipe 기반 포즈 감지 (준비 완료)
- 실시간 피드백 및 진행률 표시

### 🎨 밈 생성 및 공유
- 개인화된 춤 밈 카드 생성
- DNA 타입별 맞춤 디자인
- 소셜미디어 공유 기능

## 🚀 기술 스택

- **Frontend**: Streamlit
- **AI/ML**: MediaPipe (포즈 감지)
- **Image Processing**: OpenCV, PIL
- **Language**: Python 3.11+

## 📦 설치 및 실행

### 1. 프로젝트 클론
```bash
git clone https://github.com/Hellenak68/Choomaru.git
cd choomaru_mvp
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 애플리케이션 실행
```bash
streamlit run app.py
```

### 4. 브라우저 접속
```
http://localhost:8501
```

## 📋 필요 라이브러리

```
streamlit
mediapipe
opencv-python
pillow
numpy
```

## 🎯 사용법

1. **랜딩 페이지**: "내 춤 DNA 찾기" 버튼 클릭
2. **퀴즈**: 8개 질문에 직관적으로 답변
3. **결과 확인**: 개인의 춤 DNA 타입 확인
4. **동작 체험**: 웹캠을 통해 5가지 전통 동작 따라하기
5. **밈 생성**: 완성된 개인 맞춤 밈 카드 다운로드/공유

## 🔮 향후 계획

### 2단계 (고도화)
- 실제 웹캠 연동 (MediaPipe 실시간 포즈 감지)
- 10-20개 확장된 한국무용 동작
- 실제 이미지 합성 밈 생성

### 3단계 (확장)
- 연속 동작 인식 및 정확도 점수화
- 사용자 갤러리 및 커뮤니티 기능
- 콜라보 밈 기능 (사용자 + 전문가 영상 합성)

# 현재 영상 로딩 방식의 한계:
Streamlit: 큰 영상 파일 처리에 한계
Base64 인코딩: 1분 이상 영상은 메모리 부족 위험
브라우저: 대용량 영상 로딩 지연
## 향후 해결 방안:
1. 영상 호스팅 서비스 활용
# YouTube, Vimeo, Cloudinary 등 사용
st.video("https://youtube.com/watch?v=VIDEO_ID")
st.video("https://vimeo.com/VIDEO_ID")
2. 영상 제작 시 고려사항
길이: 30초 이하 권장 (로딩 속도)
해상도: 720P (1080P 대신)
비트레이트: 낮게 설정 (용량 절약)
코덱: H.264 (호환성 최고)
3. 단계별 접근
현재: 18초 영상 (로컬 파일)
1단계: 30초 이하 영상들 (로컬)
2단계: 1분+ 영상 (외부 호스팅)
4. 기술적 개선
청크 로딩: 영상을 작은 조각으로 나누어 로딩
프리뷰: 썸네일 + 클릭 시 전체 영상
압축: 더 강력한 압축 알고리즘
추천: 현재는 18초 영상으로 MVP 완성하고, 향후 1분+ 영상은 YouTube 임베드 방식이 가장 안정적입니다! 🎯

## 👥 개발자

- **기획 및 개발**: Hellenak68
- **AI 코딩 멘토**: Claude AI

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🎉 특별 감사

- MediaPipe 팀의 오픈소스 포즈 감지 라이브러리
- Streamlit 커뮤니티의 웹 앱 프레임워크
- 한국 전통 무용의 아름다움을 현대에 전하는 모든 예술가들

---

**춤마루와 함께 한국의 몸짓을 현대감각으로 체험해보세요! 🎭✨**