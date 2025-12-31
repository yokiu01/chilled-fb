# 춤마루 모바일 웹앱 개발 문서 인덱스

모바일 웹앱 개발을 위한 모든 문서와 리소스를 한눈에 확인할 수 있는 중앙 인덱스입니다.

---

## 🎯 시작하기

처음 시작하는 분은 아래 순서대로 문서를 읽어주세요:

1. **[빠른 시작 가이드](./QUICK_START_MOBILE.md)** ⭐ 필수
   - 5분 안에 프로젝트 설정
   - 기본 환경 구축
   - 개발 서버 실행

2. **[기술 스택 비교](./TECH_STACK_COMPARISON.md)**
   - React vs Vue vs Vanilla JS
   - 선택 이유 및 근거
   - 대안 시나리오

3. **[전체 개발 가이드](./mobile_app_development_guide.md)** ⭐ 필수
   - 8단계 상세 개발 프로세스
   - 각 단계별 Claude Code Agent 프롬프트
   - 산출물 및 체크리스트

---

## 📚 문서 목록

### 1. 개발 가이드

| 문서 | 설명 | 대상 |
|------|------|------|
| [mobile_app_development_guide.md](./mobile_app_development_guide.md) | 전체 개발 프로세스 (8단계) | 모든 개발자 |
| [QUICK_START_MOBILE.md](./QUICK_START_MOBILE.md) | 5분 빠른 시작 | 처음 시작하는 개발자 |
| [PROJECT_CHECKLIST.md](./PROJECT_CHECKLIST.md) | 단계별 상세 체크리스트 | 진행 상황 추적 |

### 2. 기술 문서

| 문서 | 설명 | 대상 |
|------|------|------|
| [TECH_STACK_COMPARISON.md](./TECH_STACK_COMPARISON.md) | 기술 스택 비교 분석 | 아키텍트, 의사결정자 |
| [MIGRATION_SUMMARY.md](./MIGRATION_SUMMARY.md) | Streamlit → React 변환 가이드 | Python 개발자 |

### 3. 자동화 스크립트

| 파일 | 설명 | 사용법 |
|------|------|--------|
| [setup-mobile-project.sh](./setup-mobile-project.sh) | 프로젝트 자동 설정 (Mac/Linux) | `bash setup-mobile-project.sh` |
| [setup-mobile-project.bat](./setup-mobile-project.bat) | 프로젝트 자동 설정 (Windows) | `setup-mobile-project.bat` |

### 4. 기존 앱 문서 (참고용)

| 파일 | 설명 |
|------|------|
| app_v16.py | 기존 Streamlit 앱 (소스 코드) |
| requirements.txt | Python 의존성 |
| README.md | 기존 앱 README |

---

## 🗺️ 개발 로드맵

```
┌─────────────────────────────────────────────────────────────┐
│                    시작: 문서 읽기                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  1단계: 요구사항 분석 및 아키텍처 설계 (2-4시간)           │
│  - app_v16.py 분석                                         │
│  - 기술 스택 선정                                          │
│  - 문서 작성: architecture.md, tech_stack.md              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2단계: UI/UX 프레임워크 구축 (4-6시간)                    │
│  - React 프로젝트 생성                                     │
│  - 기본 컴포넌트 작성                                      │
│  - 라우팅 설정                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3단계: MediaPipe 통합 (6-8시간)                           │
│  - 웹캠 컴포넌트                                           │
│  - Pose/Hands 감지                                        │
│  - 실시간 시각화                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4단계: PWA 설정 (2-3시간)                                │
│  - Service Worker                                         │
│  - Manifest 설정                                          │
│  - 아이콘 생성                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  5단계: 터치 인터페이스 (3-4시간)                          │
│  - 제스처 구현                                            │
│  - 모바일 UI 최적화                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  6단계: 성능 최적화 (4-6시간)                             │
│  - 번들 크기 최적화                                       │
│  - 메모리 관리                                            │
│  - 렌더링 최적화                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  7단계: 테스트 (3-5시간)                                  │
│  - 크로스 브라우저                                         │
│  - 다양한 디바이스                                        │
│  - 접근성                                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  8단계: 배포 (2-3시간)                                    │
│  - Vercel/Netlify 배포                                   │
│  - 도메인 설정                                            │
│  - CI/CD 구축                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              종합: 최종 검증 및 출시                        │
└─────────────────────────────────────────────────────────────┘
```

**총 예상 시간**: 28-42시간

---

## 🎓 학습 경로

### 초보 개발자
1. React 기초 학습 (3-5일)
   - [React 공식 튜토리얼](https://react.dev/learn)
2. QUICK_START_MOBILE.md 따라하기
3. mobile_app_development_guide.md 단계별 진행

### 중급 개발자
1. TECH_STACK_COMPARISON.md 읽기
2. mobile_app_development_guide.md 단계별 진행
3. 성능 최적화에 집중

### 고급 개발자
1. architecture.md 직접 작성
2. 커스텀 아키텍처 설계
3. 추가 기능 구현 (AI 분석, 소셜 기능 등)

---

## 🛠️ 도구 및 리소스

### 필수 도구
- [Node.js 18+](https://nodejs.org/)
- [VS Code](https://code.visualstudio.com/)
- [Chrome DevTools](https://developer.chrome.com/docs/devtools/)
- [Git](https://git-scm.com/)

### 권장 VS Code 확장
- ES7+ React/Redux/React-Native snippets
- Tailwind CSS IntelliSense
- Prettier
- ESLint
- GitLens

### 디자인 도구
- [Figma](https://www.figma.com/) (UI 디자인)
- [Excalidraw](https://excalidraw.com/) (다이어그램)

### 테스트 도구
- Chrome DevTools (모바일 시뮬레이터)
- [ngrok](https://ngrok.com/) (로컬 서버 외부 노출)
- [BrowserStack](https://www.browserstack.com/) (실제 디바이스 테스트)

---

## 📖 외부 참고 자료

### React 학습
- [React 공식 문서](https://react.dev/)
- [React 패턴 모음](https://www.patterns.dev/posts/react-patterns)

### MediaPipe
- [MediaPipe Web 공식 문서](https://developers.google.com/mediapipe/solutions/vision/pose_landmarker/web_js)
- [MediaPipe 예제](https://codepen.io/collection/gNMeMY)

### PWA
- [PWA 체크리스트](https://web.dev/pwa-checklist/)
- [Workbox 문서](https://developer.chrome.com/docs/workbox/)

### 모바일 웹 최적화
- [Web.dev 성능 가이드](https://web.dev/fast/)
- [Mobile Web Best Practices](https://developer.mozilla.org/en-US/docs/Web/Guide/Mobile)

### Tailwind CSS
- [Tailwind CSS 문서](https://tailwindcss.com/docs)
- [DaisyUI 컴포넌트](https://daisyui.com/components/)

---

## 🤝 기여 가이드

### 문서 개선
문서에 오류나 개선사항이 있다면:
1. GitHub Issue 생성
2. Pull Request 제출
3. 토론 참여

### 코드 기여
1. Fork 저장소
2. 기능 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 커밋 (`git commit -m 'Add amazing feature'`)
4. 푸시 (`git push origin feature/amazing-feature`)
5. Pull Request 생성

---

## ❓ FAQ

### Q: React를 모르는데 시작할 수 있나요?
A: 가능합니다. QUICK_START_MOBILE.md를 따라하면서 React 공식 튜토리얼을 병행하세요.

### Q: 개발 기간은 얼마나 걸리나요?
A: 경험에 따라 다르지만, 풀타임 기준 1-2주 정도 예상됩니다.

### Q: 기존 Streamlit 앱도 유지하나요?
A: 네, app_v16.py는 그대로 유지됩니다. 모바일 앱은 별도 프로젝트입니다.

### Q: iOS와 Android 둘 다 지원하나요?
A: 네, PWA이므로 모든 모바일 브라우저에서 작동합니다.

### Q: 네이티브 앱으로 전환 가능한가요?
A: 가능합니다. React Native나 Capacitor로 쉽게 전환할 수 있습니다.

---

## 📞 지원

### 문제 발생 시
1. PROJECT_CHECKLIST.md의 해당 단계 재확인
2. 브라우저 콘솔 로그 확인
3. GitHub Issues 검색
4. 새 Issue 생성

### 커뮤니티
- GitHub Discussions
- Stack Overflow (태그: react, mediapipe, pwa)

---

## 📊 프로젝트 현황

```
프로젝트: 춤마루 모바일 웹앱
상태: 개발 중
버전: 0.1.0 (계획)
최종 업데이트: 2024-XX-XX

완료:
✅ 문서 작성
✅ 기술 스택 선정
✅ 개발 가이드 작성

진행 예정:
⬜ 프로젝트 초기화
⬜ UI 컴포넌트 개발
⬜ MediaPipe 통합
⬜ PWA 설정
⬜ 배포
```

---

## 🎯 다음 단계

1. **[QUICK_START_MOBILE.md](./QUICK_START_MOBILE.md)** 읽고 프로젝트 생성
2. **[mobile_app_development_guide.md](./mobile_app_development_guide.md)** 단계 1부터 시작
3. **[PROJECT_CHECKLIST.md](./PROJECT_CHECKLIST.md)** 체크하며 진행

---

**행운을 빕니다! 🎭💃**

모바일 웹앱 개발 과정에서 궁금한 점이 있다면 언제든지 문의하세요.
