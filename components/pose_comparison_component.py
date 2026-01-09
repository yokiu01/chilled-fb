"""
Pose Comparison Client-Side Component
=====================================
클라이언트(브라우저)에서 MediaPipe 실행 + 전문가 자세 비교
WebRTC/STUN/TURN 불필요 - 모든 처리가 브라우저에서 이루어짐

주요 특징:
- MediaPipe Pose를 JavaScript로 브라우저에서 직접 실행
- 서버로 영상을 전송하지 않아 STUN/TURN 서버 불필요
- Streamlit Cloud 배포 시 연결 문제 해결

평가 시스템:
- 실시간 점수: 최근 10프레임 이동 평균 (사용자에게 표시)
- 싸이클 점수: 7초간 평균 (내부 성공 판정용)
- 피드백: 3초마다 업데이트 (빈번한 변경 방지)
- 성공 조건: 싸이클 평균 80점 이상

작성일: 2026-01-10
"""

import streamlit as st
import streamlit.components.v1 as components
import json
from typing import Optional, Dict, Any, List


def pose_comparison_component(
    expert_landmarks: List[Dict[str, Any]],
    action_name: str = "동작",
    key: str = "pose_comparison",
    height: int = 360,
    width: int = 480,
    target_score: int = 80,
    cycle_duration: float = 7.0,
    lang: str = "ko",
) -> None:
    """
    클라이언트 측 자세 비교 컴포넌트

    브라우저에서 MediaPipe를 실행하여 사용자 자세를 감지하고,
    전문가 자세와 비교하여 실시간 피드백을 제공합니다.

    Parameters
    ----------
    expert_landmarks : List[Dict[str, Any]]
        전문가 자세의 랜드마크 리스트. 각 랜드마크는 x, y, z, visibility 키를 가진 dict
    action_name : str
        동작 이름 (현재 미사용, 향후 확장용)
    key : str
        컴포넌트 고유 키 (현재 미사용, components.html은 key 미지원)
    height : int
        비디오 영역 높이 (픽셀)
    width : int
        비디오 영역 최대 너비 (픽셀)
    target_score : int
        성공 판정 기준 점수 (기본 80점)
    cycle_duration : float
        한 싸이클 시간 (초). 이 시간 동안의 평균으로 성공 판정
    lang : str
        언어 설정 ('ko' 또는 'en')

    Returns
    -------
    None
        Streamlit에 HTML 컴포넌트를 직접 렌더링

    Notes
    -----
    - HTTPS 또는 localhost 환경에서만 카메라 접근 가능
    - MediaPipe Pose (Full 모델, complexity=1) 사용
    - 점수 계산: 8개 주요 관절 각도 비교
    """

    # =========================================================================
    # 전문가 랜드마크를 JSON으로 변환 (JavaScript에서 사용)
    # =========================================================================
    expert_landmarks_json = json.dumps(expert_landmarks) if expert_landmarks else "null"

    # =========================================================================
    # 다국어 텍스트 정의
    # =========================================================================
    texts = {
        "ko": {
            "start": "START",
            "stop": "STOP",
            "loading": "로딩 중...",
            "no_pose": "전신이 보이게 서주세요",
            "pose_detected": "자세 감지됨",
            "perfect": "완벽해요!",
            "good": "좋아요!",
            "keep_going": "조금만 더!",
            "camera_error": "카메라 접근 실패",
            "https_required": "HTTPS 연결이 필요합니다",
            "retry": "다시 시도",
            "success": "성공!",
            "score_unit": "점",
            # 관절 이름 (피드백 메시지용)
            "joints": {
                "left_elbow": "왼팔꿈치",
                "right_elbow": "오른팔꿈치",
                "left_knee": "왼무릎",
                "right_knee": "오른무릎",
                "left_shoulder": "왼어깨",
                "right_shoulder": "오른어깨",
                "left_hip": "왼골반",
                "right_hip": "오른골반"
            },
            # 교정 피드백 접미사
            "bend_more": "° 더 구부리기",
            "extend_more": "° 더 펴기",
            "lower_more": "° 더 내리기",
            "raise_more": "° 더 올리기",
        },
        "en": {
            "start": "START",
            "stop": "STOP",
            "loading": "Loading...",
            "no_pose": "Stand where your full body is visible",
            "pose_detected": "Pose detected",
            "perfect": "Perfect!",
            "good": "Good!",
            "keep_going": "Keep going!",
            "camera_error": "Camera failed",
            "https_required": "HTTPS required",
            "retry": "Retry",
            "success": "Success!",
            "score_unit": "pts",
            "joints": {
                "left_elbow": "L.Elbow",
                "right_elbow": "R.Elbow",
                "left_knee": "L.Knee",
                "right_knee": "R.Knee",
                "left_shoulder": "L.Shoulder",
                "right_shoulder": "R.Shoulder",
                "left_hip": "L.Hip",
                "right_hip": "R.Hip"
            },
            "bend_more": "° bend more",
            "extend_more": "° extend more",
            "lower_more": "° lower",
            "raise_more": "° raise",
        }
    }

    t = texts.get(lang, texts["ko"])
    texts_json = json.dumps(t, ensure_ascii=False)

    # 전체 높이 = 비디오 + 피드백 영역 + 정지 버튼 (최소화)
    total_height = height + 120

    # =========================================================================
    # HTML/CSS/JavaScript 코드
    # =========================================================================
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            /* ================================================================
               기본 스타일 리셋 및 전역 설정
               ================================================================ */
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: transparent;
            }}

            /* ================================================================
               메인 컨테이너 - 최대 너비 제한 및 중앙 정렬
               ================================================================ */
            .wrapper {{
                width: 100%;
                max-width: {width}px;
                margin: 0 auto;
            }}

            /* ================================================================
               비디오 컨테이너 - 4:3 비율 유지, 둥근 모서리
               ================================================================ */
            .video-container {{
                position: relative;
                width: 100%;
                aspect-ratio: 4 / 3;  /* 비율 왜곡 방지 */
                background: #1a1a2e;
                border-radius: 12px;
                overflow: hidden;
            }}

            /* 실제 비디오 요소는 숨김 (캔버스에 그림) */
            #video {{ display: none; }}

            /* 캔버스 - 비디오 위에 스켈레톤 오버레이 */
            #canvas {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
            }}

            /* ================================================================
               상태 표시등 - 우상단 작은 원 (빨강: 미감지, 초록: 감지)
               ================================================================ */
            .status-indicator {{
                position: absolute;
                top: 8px;
                right: 8px;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: #ff6b6b;  /* 기본: 빨강 (미감지) */
                z-index: 10;
            }}

            .status-indicator.active {{
                background: #6bcb77;  /* 활성: 초록 (감지됨) */
                animation: pulse 1.5s infinite;
            }}

            @keyframes pulse {{
                0%, 100% {{ opacity: 1; transform: scale(1); }}
                50% {{ opacity: 0.7; transform: scale(1.2); }}
            }}

            /* ================================================================
               시작 버튼 - 비디오 중앙에 표시 (시작 전에만)
               ================================================================ */
            .start-btn-area {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                z-index: 20;
            }}

            /* 공통 버튼 스타일 */
            .main-btn {{
                padding: 14px 32px;
                font-size: 15px;
                font-weight: 600;
                color: white;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.2s;
            }}

            .start-btn {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}

            .stop-btn {{
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
                width: 100%;
            }}

            .main-btn:hover {{ transform: scale(1.02); }}

            /* ================================================================
               중지 버튼 영역 - 피드백 아래에 표시 (실행 중에만)
               ================================================================ */
            .stop-btn-area {{
                margin-top: 10px;
                display: none;  /* 기본: 숨김 */
            }}

            .stop-btn-area.show {{ display: block; }}

            /* ================================================================
               로딩 스피너 - 카메라 초기화 중 표시
               ================================================================ */
            .loading {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                color: white;
                z-index: 15;
            }}

            .spinner {{
                width: 36px;
                height: 36px;
                border: 3px solid rgba(255,255,255,0.2);
                border-top-color: #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 10px;
            }}

            @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

            /* ================================================================
               에러 메시지 - HTTPS 필요, 카메라 실패 등
               ================================================================ */
            .error-msg {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                color: #ff6b6b;
                padding: 20px;
                font-size: 14px;
                z-index: 15;
            }}

            /* ================================================================
               성공 오버레이 - 싸이클 평균 80점 이상 달성 시
               ================================================================ */
            .success-overlay {{
                position: absolute;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(107, 203, 119, 0.9);
                display: none;
                justify-content: center;
                align-items: center;
                flex-direction: column;
                z-index: 25;
            }}

            .success-overlay.show {{ display: flex; }}
            .success-icon {{ font-size: 40px; margin-bottom: 8px; }}
            .success-text {{ font-size: 20px; font-weight: bold; color: white; }}

            /* ================================================================
               피드백 영역 - 비디오 아래에 점수와 피드백 표시
               ================================================================ */
            .feedback-area {{
                margin-top: 12px;
                padding: 12px 16px;
                background: #f8f9fa;
                border-radius: 10px;
                display: none;  /* 기본: 숨김 */
            }}

            .feedback-area.show {{ display: block; }}

            /* 점수 행 - 점수와 단위를 중앙 정렬 */
            .score-row {{
                display: flex;
                justify-content: center;
                align-items: center;
                margin-bottom: 8px;
                gap: 12px;
            }}

            .score-value {{
                font-size: 32px;
                font-weight: bold;
                line-height: 1;
            }}

            .score-label {{
                font-size: 13px;
                color: #666;
            }}

            /* 점수 바 - 시각적 진행률 표시 */
            .score-bar-container {{
                height: 6px;
                background: #e0e0e0;
                border-radius: 3px;
                overflow: hidden;
                margin-bottom: 8px;
            }}

            .score-bar {{
                height: 100%;
                border-radius: 3px;
                transition: width 0.3s ease, background 0.3s ease;
            }}

            /* 피드백 텍스트 - 교정 안내 메시지 */
            .feedback-text {{
                font-size: 14px;
                color: #333;
                text-align: center;
                min-height: 20px;
            }}
        </style>
    </head>
    <body>
        <!-- ================================================================
             HTML 구조
             - wrapper: 전체 컨테이너
             - video-container: 웹캠 + 스켈레톤 영역
             - feedback-area: 점수 + 피드백 영역
             - stop-btn-area: 중지 버튼 영역
             ================================================================ -->
        <div class="wrapper">
            <div class="video-container">
                <!-- 실제 비디오 (숨김, MediaPipe 입력용) -->
                <video id="video" playsinline></video>
                <!-- 캔버스 (비디오 + 스켈레톤 렌더링) -->
                <canvas id="canvas"></canvas>

                <!-- 자세 감지 상태 표시등 -->
                <div class="status-indicator" id="statusDot"></div>

                <!-- 시작 버튼 (시작 전에만 표시) -->
                <div class="start-btn-area" id="startBtnArea">
                    <button class="main-btn start-btn" id="startBtn">START</button>
                </div>

                <!-- 로딩 스피너 (초기화 중) -->
                <div class="loading" id="loading" style="display: none;">
                    <div class="spinner"></div>
                    <div>Loading...</div>
                </div>

                <!-- 에러 메시지 -->
                <div class="error-msg" id="errorMsg" style="display: none;"></div>

                <!-- 성공 오버레이 (싸이클 평균 80점 이상 시) -->
                <div class="success-overlay" id="successOverlay">
                    <div class="success-icon">🎉</div>
                    <div class="success-text">{t['success']}</div>
                </div>
            </div>

            <!-- 피드백 영역 (비디오 아래) -->
            <div class="feedback-area" id="feedbackArea">
                <div class="score-row">
                    <div class="score-value" id="scoreValue" style="color: #667eea;">0</div>
                    <div class="score-label">{t['score_unit']}</div>
                </div>
                <div class="score-bar-container">
                    <div class="score-bar" id="scoreBar" style="width: 0%; background: #ff6b6b;"></div>
                </div>
                <div class="feedback-text" id="feedbackText">{t['pose_detected']}</div>
            </div>

            <!-- 중지 버튼 (비디오 외부, 실행 중에만 표시) -->
            <div class="stop-btn-area" id="stopBtnArea">
                <button class="main-btn stop-btn" id="stopBtn">STOP</button>
            </div>
        </div>

        <!-- ================================================================
             MediaPipe 라이브러리 (CDN)
             - camera_utils: 카메라 제어
             - drawing_utils: 스켈레톤 그리기 (현재 직접 구현)
             - pose: 자세 감지 모델
             ================================================================ -->
        <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js"></script>

        <script>
            // ================================================================
            // 상수 설정
            // ================================================================
            const EXPERT_LANDMARKS = {expert_landmarks_json};  // 전문가 자세 랜드마크
            const TARGET_SCORE = {target_score};               // 성공 기준 점수
            const CYCLE_DURATION = {cycle_duration};           // 싸이클 시간 (초)
            const TEXTS = {texts_json};                        // 다국어 텍스트

            // ================================================================
            // DOM 요소 참조
            // ================================================================
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            const startBtn = document.getElementById('startBtn');
            const stopBtn = document.getElementById('stopBtn');
            const startBtnArea = document.getElementById('startBtnArea');
            const stopBtnArea = document.getElementById('stopBtnArea');
            const loadingEl = document.getElementById('loading');
            const errorMsg = document.getElementById('errorMsg');
            const statusDot = document.getElementById('statusDot');
            const feedbackArea = document.getElementById('feedbackArea');
            const scoreEl = document.getElementById('scoreValue');
            const scoreBar = document.getElementById('scoreBar');
            const feedbackText = document.getElementById('feedbackText');
            const successOverlay = document.getElementById('successOverlay');

            // ================================================================
            // 상태 변수
            // ================================================================
            let pose = null;      // MediaPipe Pose 인스턴스
            let camera = null;    // Camera 인스턴스
            let isRunning = false;

            // ================================================================
            // 평가 시스템 변수
            // ================================================================
            const scoreHistory = [];     // 이동 평균용 최근 점수들
            const cycleScores = [];      // 싸이클 동안의 점수들
            let lastFeedbackTime = 0;    // 마지막 피드백 업데이트 시간 (ms)
            let cycleStartTime = 0;      // 싸이클 시작 시간 (ms)
            let successShown = false;    // 성공 표시 여부
            let currentFeedback = '';    // 현재 피드백 메시지

            const SCORE_HISTORY_SIZE = 10;   // 이동 평균 윈도우 크기
            const FEEDBACK_INTERVAL = 3000;  // 피드백 업데이트 간격 (ms)

            // ================================================================
            // MediaPipe 스켈레톤 연결 정의
            // 숫자는 MediaPipe Pose 랜드마크 인덱스
            // ================================================================
            const POSE_CONNECTIONS = [
                [11, 12],  // 어깨-어깨
                [11, 13], [13, 15],  // 왼팔: 어깨-팔꿈치-손목
                [12, 14], [14, 16],  // 오른팔: 어깨-팔꿈치-손목
                [11, 23], [12, 24],  // 몸통: 어깨-골반
                [23, 24],  // 골반-골반
                [23, 25], [25, 27],  // 왼다리: 골반-무릎-발목
                [24, 26], [26, 28]   // 오른다리: 골반-무릎-발목
            ];

            // ================================================================
            // 보안 컨텍스트 확인 (HTTPS 또는 localhost 필요)
            // ================================================================
            function checkSecureContext() {{
                if (window.isSecureContext) return true;
                if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') return true;
                return false;
            }}

            // ================================================================
            // 미디어 디바이스 API 지원 확인
            // ================================================================
            function checkMediaDevices() {{
                return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
            }}

            // ================================================================
            // 랜드마크 정규화
            // - 골반 중심을 원점으로 이동
            // - 어깨 너비로 스케일 정규화
            // - 체형, 카메라 거리에 관계없이 일관된 비교 가능
            // ================================================================
            function normalizeLandmarks(landmarks) {{
                if (!landmarks || landmarks.length < 33) return null;

                // 골반 중심점 계산
                const hipLeft = landmarks[23], hipRight = landmarks[24];
                const hipCenterX = (hipLeft.x + hipRight.x) / 2;
                const hipCenterY = (hipLeft.y + hipRight.y) / 2;
                const hipCenterZ = (hipLeft.z + hipRight.z) / 2;

                // 어깨 너비 계산 (스케일 기준)
                const shoulderLeft = landmarks[11], shoulderRight = landmarks[12];
                const shoulderWidth = Math.sqrt(
                    Math.pow(shoulderRight.x - shoulderLeft.x, 2) +
                    Math.pow(shoulderRight.y - shoulderLeft.y, 2) +
                    Math.pow(shoulderRight.z - shoulderLeft.z, 2)
                ) || 1;  // 0으로 나누기 방지

                // 정규화된 랜드마크 반환
                return landmarks.map(lm => ({{
                    x: (lm.x - hipCenterX) / shoulderWidth,
                    y: (lm.y - hipCenterY) / shoulderWidth,
                    z: (lm.z - hipCenterZ) / shoulderWidth,
                    visibility: lm.visibility || 1
                }}));
            }}

            // ================================================================
            // 세 점 사이의 각도 계산 (도 단위)
            // p2가 꼭지점
            // ================================================================
            function calculateAngle(p1, p2, p3) {{
                // p2에서 p1, p3로 향하는 벡터
                const v1 = {{ x: p1.x - p2.x, y: p1.y - p2.y, z: p1.z - p2.z }};
                const v2 = {{ x: p3.x - p2.x, y: p3.y - p2.y, z: p3.z - p2.z }};

                // 내적
                const dot = v1.x * v2.x + v1.y * v2.y + v1.z * v2.z;

                // 벡터 크기
                const mag1 = Math.sqrt(v1.x * v1.x + v1.y * v1.y + v1.z * v1.z);
                const mag2 = Math.sqrt(v2.x * v2.x + v2.y * v2.y + v2.z * v2.z);

                // 코사인 값 (범위 제한)
                let cosAngle = dot / (mag1 * mag2 + 1e-6);
                cosAngle = Math.max(-1, Math.min(1, cosAngle));

                // 라디안 -> 도
                return Math.acos(cosAngle) * (180 / Math.PI);
            }}

            // ================================================================
            // 주요 8개 관절 각도 계산
            // - 팔꿈치 (좌/우): 어깨-팔꿈치-손목
            // - 무릎 (좌/우): 골반-무릎-발목
            // - 어깨 (좌/우): 골반-어깨-팔꿈치
            // - 골반 (좌/우): 어깨-골반-무릎
            // ================================================================
            function calculateJointAngles(landmarks) {{
                if (!landmarks) return {{}};
                const angles = {{}};
                const MIN_VIS = 0.5;  // 최소 가시성 임계값

                // 관절 정의: [이름, [세 점의 인덱스]]
                const joints = [
                    {{ name: 'left_elbow', points: [11, 13, 15] }},
                    {{ name: 'right_elbow', points: [12, 14, 16] }},
                    {{ name: 'left_knee', points: [23, 25, 27] }},
                    {{ name: 'right_knee', points: [24, 26, 28] }},
                    {{ name: 'left_shoulder', points: [23, 11, 13] }},
                    {{ name: 'right_shoulder', points: [24, 12, 14] }},
                    {{ name: 'left_hip', points: [11, 23, 25] }},
                    {{ name: 'right_hip', points: [12, 24, 26] }}
                ];

                joints.forEach(({{ name, points }}) => {{
                    const [i1, i2, i3] = points;
                    // 세 점 모두 가시성이 충분한 경우에만 계산
                    if (landmarks[i1].visibility >= MIN_VIS &&
                        landmarks[i2].visibility >= MIN_VIS &&
                        landmarks[i3].visibility >= MIN_VIS) {{
                        angles[name] = calculateAngle(landmarks[i1], landmarks[i2], landmarks[i3]);
                    }}
                }});
                return angles;
            }}

            // ================================================================
            // 자세 비교 및 점수 계산
            //
            // 점수 계산 방식:
            // - 각 관절별 각도 차이를 점수로 변환
            // - 10도 이하: 100점
            // - 45도 이상: 0점
            // - 그 사이: 비선형 감소 (지수 1.5)
            // ================================================================
            function comparePoses(userLandmarks, expertLandmarks) {{
                if (!userLandmarks || !expertLandmarks) return {{ score: 0, feedback: '' }};

                // 랜드마크 정규화
                const userNorm = normalizeLandmarks(userLandmarks);
                const expertNorm = normalizeLandmarks(expertLandmarks);
                if (!userNorm || !expertNorm) return {{ score: 0, feedback: '' }};

                // 각도 계산
                const userAngles = calculateJointAngles(userNorm);
                const expertAngles = calculateJointAngles(expertNorm);
                const jointScores = {{}};
                const angleDiffs = {{}};

                // 각 관절별 점수 계산
                Object.keys(userAngles).forEach(joint => {{
                    if (expertAngles[joint] !== undefined) {{
                        const diff = Math.abs(userAngles[joint] - expertAngles[joint]);
                        angleDiffs[joint] = {{ diff, user: userAngles[joint], expert: expertAngles[joint] }};

                        // 각도 차이를 점수로 변환 (비선형)
                        let score;
                        if (diff <= 10) score = 100;
                        else if (diff >= 45) score = 0;
                        else score = 100 * (1 - Math.pow((diff - 10) / 35, 1.5));
                        jointScores[joint] = score;
                    }}
                }});

                // 전체 점수 (관절별 점수의 평균)
                const scores = Object.values(jointScores);
                const overallScore = scores.length > 0 ? scores.reduce((a, b) => a + b) / scores.length : 0;

                // 피드백 생성 (가장 문제되는 관절에 대해)
                let feedback = '';
                const sortedDiffs = Object.entries(angleDiffs).sort((a, b) => b[1].diff - a[1].diff);
                if (sortedDiffs.length > 0 && sortedDiffs[0][1].diff >= 15) {{
                    const [joint, data] = sortedDiffs[0];
                    const jointName = TEXTS.joints[joint] || joint;
                    const isElbowOrKnee = joint.includes('elbow') || joint.includes('knee');
                    const diff = Math.round(data.diff);

                    // 사용자 각도가 더 크면 구부리기/내리기, 작으면 펴기/올리기
                    if (data.user > data.expert) {{
                        feedback = jointName + ' ' + diff + (isElbowOrKnee ? TEXTS.bend_more : TEXTS.lower_more);
                    }} else {{
                        feedback = jointName + ' ' + diff + (isElbowOrKnee ? TEXTS.extend_more : TEXTS.raise_more);
                    }}
                }}

                return {{ score: Math.round(overallScore), feedback, angleDiffs }};
            }}

            // ================================================================
            // 이동 평균 계산 (최근 10프레임)
            // - 점수 변동을 부드럽게 하여 사용자 경험 개선
            // ================================================================
            function getSmoothedScore(newScore) {{
                scoreHistory.push(newScore);
                if (scoreHistory.length > SCORE_HISTORY_SIZE) {{
                    scoreHistory.shift();  // 가장 오래된 점수 제거
                }}
                return Math.round(scoreHistory.reduce((a, b) => a + b) / scoreHistory.length);
            }}

            // ================================================================
            // 싸이클 점수 업데이트 (내부 성공 판정용)
            // - 7초 동안 점수를 누적하여 평균 계산
            // - 평균 80점 이상이면 성공 표시
            // ================================================================
            function updateCycleScore(score, currentTime) {{
                // 싸이클 시작
                if (cycleStartTime === 0) {{
                    cycleStartTime = currentTime;
                    cycleScores.length = 0;
                }}

                cycleScores.push(score);

                // 싸이클 완료 체크
                const elapsed = (currentTime - cycleStartTime) / 1000;
                if (elapsed >= CYCLE_DURATION) {{
                    const avgScore = cycleScores.reduce((a, b) => a + b) / cycleScores.length;

                    // 싸이클 평균이 목표 점수 이상이면 성공
                    if (avgScore >= TARGET_SCORE && !successShown) {{
                        successShown = true;
                        successOverlay.classList.add('show');
                        setTimeout(() => successOverlay.classList.remove('show'), 2500);
                    }}

                    // 새 싸이클 시작
                    cycleStartTime = currentTime;
                    cycleScores.length = 0;
                }}
            }}

            // ================================================================
            // 피드백 업데이트 여부 확인 (3초 간격)
            // - 너무 빈번한 피드백 변경은 사용자에게 혼란을 줄 수 있음
            // ================================================================
            function shouldUpdateFeedback(currentTime) {{
                if (currentTime - lastFeedbackTime >= FEEDBACK_INTERVAL) {{
                    lastFeedbackTime = currentTime;
                    return true;
                }}
                return false;
            }}

            // ================================================================
            // 점수에 따른 색상 반환
            // - 80점 이상: 초록
            // - 50점 이상: 노랑
            // - 50점 미만: 빨강
            // ================================================================
            function getScoreColor(score) {{
                if (score >= 80) return '#6bcb77';
                if (score >= 50) return '#ffd93d';
                return '#ff6b6b';
            }}

            // ================================================================
            // 점수에 따른 메시지 반환
            // ================================================================
            function getScoreMessage(score, feedback) {{
                if (score >= 80) return '🟢 ' + TEXTS.perfect;
                if (score >= 60) return feedback || ('🟡 ' + TEXTS.good);
                return feedback || ('🔴 ' + TEXTS.keep_going);
            }}

            // ================================================================
            // MediaPipe 결과 처리 콜백
            // - 매 프레임마다 호출
            // - 비디오 렌더링, 스켈레톤 그리기, 점수 계산
            // ================================================================
            function onResults(results) {{
                // 캔버스 크기 조정
                canvas.width = canvas.offsetWidth;
                canvas.height = canvas.offsetHeight;

                // 비디오 프레임 그리기 (좌우 반전 - 거울 모드)
                ctx.save();
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.translate(canvas.width, 0);
                ctx.scale(-1, 1);
                ctx.drawImage(results.image, 0, 0, canvas.width, canvas.height);
                ctx.restore();

                const currentTime = Date.now();

                if (results.poseLandmarks) {{
                    // 랜드마크 좌우 반전 (거울 모드에 맞춤)
                    const landmarks = results.poseLandmarks.map(lm => ({{
                        x: 1 - lm.x, y: lm.y, z: lm.z, visibility: lm.visibility
                    }}));

                    // 스켈레톤 그리기 (선)
                    ctx.strokeStyle = '#00FF00';
                    ctx.lineWidth = 2;
                    POSE_CONNECTIONS.forEach(([s, e]) => {{
                        if (landmarks[s].visibility > 0.5 && landmarks[e].visibility > 0.5) {{
                            ctx.beginPath();
                            ctx.moveTo(landmarks[s].x * canvas.width, landmarks[s].y * canvas.height);
                            ctx.lineTo(landmarks[e].x * canvas.width, landmarks[e].y * canvas.height);
                            ctx.stroke();
                        }}
                    }});

                    // 랜드마크 점 그리기
                    landmarks.forEach(lm => {{
                        if (lm.visibility > 0.5) {{
                            ctx.beginPath();
                            ctx.arc(lm.x * canvas.width, lm.y * canvas.height, 3, 0, 2 * Math.PI);
                            ctx.fillStyle = '#FF0000';
                            ctx.fill();
                        }}
                    }});

                    // 상태 표시등 활성화
                    statusDot.classList.add('active');

                    // 전문가 자세와 비교
                    if (EXPERT_LANDMARKS) {{
                        const result = comparePoses(landmarks, EXPERT_LANDMARKS);

                        // 이동 평균 점수 (실시간 표시용)
                        const smoothedScore = getSmoothedScore(result.score);

                        // 싸이클 점수 (내부 성공 판정용)
                        updateCycleScore(smoothedScore, currentTime);

                        // UI 업데이트 (실시간 점수 표시)
                        scoreEl.textContent = smoothedScore;
                        scoreEl.style.color = getScoreColor(smoothedScore);

                        scoreBar.style.width = smoothedScore + '%';
                        scoreBar.style.background = getScoreColor(smoothedScore);

                        // 피드백 (3초 간격으로만 업데이트)
                        if (shouldUpdateFeedback(currentTime)) {{
                            currentFeedback = result.feedback;
                            feedbackText.textContent = getScoreMessage(smoothedScore, currentFeedback);
                        }}
                    }}
                }} else {{
                    // 자세 미감지
                    statusDot.classList.remove('active');
                    if (shouldUpdateFeedback(currentTime)) {{
                        feedbackText.textContent = TEXTS.no_pose;
                    }}
                }}
            }}

            // ================================================================
            // 카메라 시작
            // ================================================================
            async function startCamera() {{
                // HTTPS/localhost 확인
                if (!checkSecureContext()) {{
                    errorMsg.innerHTML = TEXTS.https_required + '<br><small>localhost 또는 HTTPS 필요</small>';
                    errorMsg.style.display = 'block';
                    startBtnArea.style.display = 'none';
                    return;
                }}

                // 미디어 디바이스 API 확인
                if (!checkMediaDevices()) {{
                    errorMsg.innerHTML = TEXTS.camera_error + '<br><small>카메라 지원 안 됨</small>';
                    errorMsg.style.display = 'block';
                    startBtnArea.style.display = 'none';
                    return;
                }}

                // 로딩 표시
                loadingEl.style.display = 'block';
                startBtnArea.style.display = 'none';
                errorMsg.style.display = 'none';

                try {{
                    // MediaPipe Pose 초기화
                    pose = new Pose({{
                        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${{file}}`
                    }});
                    pose.setOptions({{
                        modelComplexity: 1,        // 0=Lite, 1=Full, 2=Heavy
                        smoothLandmarks: true,     // 랜드마크 스무딩
                        minDetectionConfidence: 0.5,
                        minTrackingConfidence: 0.5
                    }});
                    pose.onResults(onResults);

                    // 카메라 초기화
                    camera = new Camera(video, {{
                        onFrame: async () => {{
                            if (pose && isRunning) await pose.send({{ image: video }});
                        }},
                        width: 640,
                        height: 480
                    }});

                    await camera.start();
                    isRunning = true;

                    // UI 업데이트
                    loadingEl.style.display = 'none';
                    feedbackArea.classList.add('show');
                    stopBtnArea.classList.add('show');

                    // 평가 변수 초기화
                    scoreHistory.length = 0;
                    cycleScores.length = 0;
                    cycleStartTime = 0;
                    lastFeedbackTime = 0;
                    successShown = false;

                }} catch (error) {{
                    console.error('Camera error:', error);
                    loadingEl.style.display = 'none';
                    errorMsg.innerHTML = TEXTS.camera_error + '<br><small>' + error.message + '</small>';
                    errorMsg.style.display = 'block';
                    startBtnArea.style.display = 'block';
                }}
            }}

            // ================================================================
            // 카메라 중지 및 리소스 정리
            // - 재시작 시 문제가 없도록 완전히 정리
            // ================================================================
            function stopCamera() {{
                isRunning = false;

                // 카메라 스트림 정리
                if (camera) {{
                    camera.stop();
                    camera = null;
                }}

                // 비디오 스트림 트랙 정리 (재시작 시 필요)
                if (video.srcObject) {{
                    video.srcObject.getTracks().forEach(track => track.stop());
                    video.srcObject = null;
                }}

                // MediaPipe pose 정리
                if (pose) {{
                    pose.close();
                    pose = null;
                }}

                // UI 초기화
                feedbackArea.classList.remove('show');
                stopBtnArea.classList.remove('show');
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                startBtnArea.style.display = 'block';

                // 점수 초기화
                scoreEl.textContent = '0';
                scoreEl.style.color = '#667eea';
                scoreBar.style.width = '0%';
                feedbackText.textContent = TEXTS.pose_detected;
            }}

            // ================================================================
            // 이벤트 리스너 등록
            // ================================================================
            startBtn.addEventListener('click', startCamera);
            stopBtn.addEventListener('click', stopCamera);
        </script>
    </body>
    </html>
    """

    # Streamlit에 HTML 컴포넌트 렌더링
    components.html(html_code, height=total_height)
