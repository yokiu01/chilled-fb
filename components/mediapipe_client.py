"""
MediaPipe Client-Side Component
클라이언트(브라우저)에서 MediaPipe를 실행하여 STUN/TURN 문제 해결
WebRTC 영상 스트리밍 없이 랜드마크 좌표만 서버로 전송
"""

import streamlit as st
import streamlit.components.v1 as components
import json
from typing import Optional, Dict, Any, Callable

def mediapipe_pose_component(
    key: str = "mediapipe_pose",
    height: int = 480,
    width: int = 640,
    show_skeleton: bool = True,
    show_landmarks: bool = True,
    model_complexity: int = 1,  # 0: Lite, 1: Full, 2: Heavy
    min_detection_confidence: float = 0.5,
    min_tracking_confidence: float = 0.5,
    on_pose_detected: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Optional[Dict[str, Any]]:
    """
    클라이언트 측 MediaPipe Pose 컴포넌트

    Args:
        key: 컴포넌트 고유 키
        height: 캔버스 높이
        width: 캔버스 너비
        show_skeleton: 스켈레톤 표시 여부
        show_landmarks: 랜드마크 점 표시 여부
        model_complexity: 모델 복잡도 (0: Lite, 1: Full, 2: Heavy)
        min_detection_confidence: 최소 감지 신뢰도
        min_tracking_confidence: 최소 추적 신뢰도
        on_pose_detected: 포즈 감지 시 콜백 함수

    Returns:
        랜드마크 데이터 딕셔너리 또는 None
    """

    # HTML/JavaScript 코드
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            .container {{
                position: relative;
                width: {width}px;
                height: {height}px;
                margin: 0 auto;
            }}
            #video {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                transform: scaleX(-1);
                display: none;
            }}
            #canvas {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                border-radius: 8px;
            }}
            .status {{
                position: absolute;
                top: 10px;
                left: 10px;
                background: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-family: sans-serif;
                font-size: 12px;
                z-index: 10;
            }}
            .fps {{
                position: absolute;
                top: 10px;
                right: 10px;
                background: rgba(0, 0, 0, 0.7);
                color: #00ff00;
                padding: 5px 10px;
                border-radius: 4px;
                font-family: monospace;
                font-size: 12px;
                z-index: 10;
            }}
            .start-btn {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                padding: 15px 30px;
                font-size: 18px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                z-index: 20;
            }}
            .start-btn:hover {{
                opacity: 0.9;
            }}
            .loading {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: white;
                font-family: sans-serif;
                text-align: center;
                z-index: 15;
            }}
            .loading-spinner {{
                border: 4px solid rgba(255, 255, 255, 0.3);
                border-top: 4px solid white;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 10px;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="container" id="container">
            <video id="video" playsinline></video>
            <canvas id="canvas"></canvas>
            <div class="status" id="status">준비 중...</div>
            <div class="fps" id="fps">FPS: --</div>
            <button class="start-btn" id="startBtn">카메라 시작</button>
            <div class="loading" id="loading" style="display: none;">
                <div class="loading-spinner"></div>
                <div>MediaPipe 로딩 중...</div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js" crossorigin="anonymous"></script>
        <script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js" crossorigin="anonymous"></script>
        <script src="https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js" crossorigin="anonymous"></script>

        <script>
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            const statusEl = document.getElementById('status');
            const fpsEl = document.getElementById('fps');
            const startBtn = document.getElementById('startBtn');
            const loadingEl = document.getElementById('loading');
            const container = document.getElementById('container');

            canvas.width = {width};
            canvas.height = {height};

            let pose = null;
            let camera = null;
            let isRunning = false;
            let lastTime = performance.now();
            let frameCount = 0;
            let fps = 0;

            // FPS 계산
            function updateFPS() {{
                frameCount++;
                const now = performance.now();
                if (now - lastTime >= 1000) {{
                    fps = frameCount;
                    frameCount = 0;
                    lastTime = now;
                    fpsEl.textContent = 'FPS: ' + fps;
                }}
            }}

            // 스켈레톤 연결 정의
            const POSE_CONNECTIONS = [
                [11, 12], [11, 13], [13, 15], [12, 14], [14, 16],  // 팔
                [11, 23], [12, 24], [23, 24],  // 몸통
                [23, 25], [25, 27], [24, 26], [26, 28],  // 다리
                [27, 29], [29, 31], [28, 30], [30, 32],  // 발
                [0, 1], [1, 2], [2, 3], [3, 7], [0, 4], [4, 5], [5, 6], [6, 8],  // 얼굴
                [9, 10],  // 입
            ];

            // 포즈 결과 처리
            function onResults(results) {{
                updateFPS();

                // 캔버스 클리어 및 비디오 그리기 (좌우 반전)
                ctx.save();
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.translate(canvas.width, 0);
                ctx.scale(-1, 1);
                ctx.drawImage(results.image, 0, 0, canvas.width, canvas.height);
                ctx.restore();

                if (results.poseLandmarks) {{
                    const landmarks = results.poseLandmarks;

                    // 좌우 반전된 랜드마크 계산
                    const flippedLandmarks = landmarks.map(lm => ({{
                        x: 1 - lm.x,
                        y: lm.y,
                        z: lm.z,
                        visibility: lm.visibility
                    }}));

                    // 스켈레톤 그리기
                    if ({str(show_skeleton).lower()}) {{
                        ctx.strokeStyle = '#00FF00';
                        ctx.lineWidth = 3;

                        POSE_CONNECTIONS.forEach(([start, end]) => {{
                            const startLm = flippedLandmarks[start];
                            const endLm = flippedLandmarks[end];

                            if (startLm.visibility > 0.5 && endLm.visibility > 0.5) {{
                                ctx.beginPath();
                                ctx.moveTo(startLm.x * canvas.width, startLm.y * canvas.height);
                                ctx.lineTo(endLm.x * canvas.width, endLm.y * canvas.height);
                                ctx.stroke();
                            }}
                        }});
                    }}

                    // 랜드마크 점 그리기
                    if ({str(show_landmarks).lower()}) {{
                        flippedLandmarks.forEach((lm, idx) => {{
                            if (lm.visibility > 0.5) {{
                                ctx.beginPath();
                                ctx.arc(lm.x * canvas.width, lm.y * canvas.height, 5, 0, 2 * Math.PI);
                                ctx.fillStyle = '#FF0000';
                                ctx.fill();
                                ctx.strokeStyle = '#FFFFFF';
                                ctx.lineWidth = 1;
                                ctx.stroke();
                            }}
                        }});
                    }}

                    statusEl.textContent = '포즈 감지됨';
                    statusEl.style.background = 'rgba(0, 128, 0, 0.7)';

                    // Streamlit으로 데이터 전송
                    const data = {{
                        landmarks: flippedLandmarks,
                        timestamp: Date.now(),
                        fps: fps
                    }};

                    // Streamlit Component API
                    if (window.Streamlit) {{
                        window.Streamlit.setComponentValue(data);
                    }}
                }} else {{
                    statusEl.textContent = '포즈를 찾을 수 없음';
                    statusEl.style.background = 'rgba(255, 165, 0, 0.7)';

                    if (window.Streamlit) {{
                        window.Streamlit.setComponentValue({{ landmarks: null, timestamp: Date.now(), fps: fps }});
                    }}
                }}
            }}

            // MediaPipe 초기화
            async function initMediaPipe() {{
                loadingEl.style.display = 'block';
                startBtn.style.display = 'none';

                try {{
                    pose = new Pose({{
                        locateFile: (file) => {{
                            return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${{file}}`;
                        }}
                    }});

                    pose.setOptions({{
                        modelComplexity: {model_complexity},
                        smoothLandmarks: true,
                        enableSegmentation: false,
                        smoothSegmentation: false,
                        minDetectionConfidence: {min_detection_confidence},
                        minTrackingConfidence: {min_tracking_confidence}
                    }});

                    pose.onResults(onResults);

                    // 카메라 시작
                    camera = new Camera(video, {{
                        onFrame: async () => {{
                            if (pose && isRunning) {{
                                await pose.send({{ image: video }});
                            }}
                        }},
                        width: {width},
                        height: {height}
                    }});

                    await camera.start();
                    isRunning = true;
                    loadingEl.style.display = 'none';
                    statusEl.textContent = '카메라 실행 중';

                }} catch (error) {{
                    console.error('MediaPipe 초기화 실패:', error);
                    loadingEl.innerHTML = '<div style="color: red;">카메라 접근 실패<br>카메라 권한을 확인해주세요</div>';

                    // 3초 후 재시도 버튼 표시
                    setTimeout(() => {{
                        loadingEl.style.display = 'none';
                        startBtn.style.display = 'block';
                        startBtn.textContent = '다시 시도';
                    }}, 3000);
                }}
            }}

            // 시작 버튼 클릭
            startBtn.addEventListener('click', initMediaPipe);

            // Streamlit 컴포넌트 초기화
            if (window.Streamlit) {{
                window.Streamlit.setFrameHeight({height + 20});
            }}
        </script>
    </body>
    </html>
    """

    # Streamlit 컴포넌트 렌더링
    result = components.html(html_code, height=height + 30, key=key)

    return result


def mediapipe_pose_hands_component(
    key: str = "mediapipe_pose_hands",
    height: int = 480,
    width: int = 640,
    show_pose_skeleton: bool = True,
    show_hand_skeleton: bool = True,
    model_complexity: int = 1,
) -> Optional[Dict[str, Any]]:
    """
    클라이언트 측 MediaPipe Pose + Hands 컴포넌트
    포즈와 손 랜드마크를 동시에 감지
    """

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            .container {{
                position: relative;
                width: {width}px;
                height: {height}px;
                margin: 0 auto;
                background: #1a1a2e;
                border-radius: 8px;
                overflow: hidden;
            }}
            #video {{ display: none; }}
            #canvas {{
                width: 100%;
                height: 100%;
            }}
            .overlay {{
                position: absolute;
                padding: 8px 12px;
                background: rgba(0, 0, 0, 0.7);
                color: white;
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 12px;
                border-radius: 4px;
                z-index: 10;
            }}
            .status {{ top: 10px; left: 10px; }}
            .fps {{ top: 10px; right: 10px; color: #00ff00; font-family: monospace; }}
            .score {{ bottom: 10px; left: 10px; font-size: 16px; font-weight: bold; }}
            .start-btn {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                padding: 16px 32px;
                font-size: 16px;
                font-weight: 600;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 12px;
                cursor: pointer;
                z-index: 20;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .start-btn:hover {{
                transform: translate(-50%, -50%) scale(1.05);
                box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
            }}
            .loading {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                z-index: 15;
            }}
            .spinner {{
                width: 50px;
                height: 50px;
                border: 4px solid rgba(255,255,255,0.2);
                border-top-color: #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 15px;
            }}
            @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        </style>
    </head>
    <body>
        <div class="container">
            <video id="video" playsinline></video>
            <canvas id="canvas" width="{width}" height="{height}"></canvas>
            <div class="overlay status" id="status">준비 중...</div>
            <div class="overlay fps" id="fps">FPS: --</div>
            <button class="start-btn" id="startBtn">START</button>
            <div class="loading" id="loading" style="display: none;">
                <div class="spinner"></div>
                <div style="color: white; font-family: sans-serif;">MediaPipe 로딩 중...</div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js"></script>

        <script>
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            const statusEl = document.getElementById('status');
            const fpsEl = document.getElementById('fps');
            const startBtn = document.getElementById('startBtn');
            const loadingEl = document.getElementById('loading');

            let pose = null, hands = null, camera = null;
            let isRunning = false;
            let lastPoseResults = null, lastHandsResults = null;
            let frameCount = 0, fps = 0, lastTime = performance.now();

            const POSE_CONNECTIONS = [
                [11,12],[11,13],[13,15],[12,14],[14,16],
                [11,23],[12,24],[23,24],
                [23,25],[25,27],[24,26],[26,28],
                [27,29],[29,31],[28,30],[30,32]
            ];

            const HAND_CONNECTIONS = [
                [0,1],[1,2],[2,3],[3,4],
                [0,5],[5,6],[6,7],[7,8],
                [0,9],[9,10],[10,11],[11,12],
                [0,13],[13,14],[14,15],[15,16],
                [0,17],[17,18],[18,19],[19,20],
                [5,9],[9,13],[13,17]
            ];

            function updateFPS() {{
                frameCount++;
                const now = performance.now();
                if (now - lastTime >= 1000) {{
                    fps = frameCount;
                    frameCount = 0;
                    lastTime = now;
                    fpsEl.textContent = 'FPS: ' + fps;
                }}
            }}

            function drawResults() {{
                ctx.save();
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.translate(canvas.width, 0);
                ctx.scale(-1, 1);
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                ctx.restore();

                let poseData = null, handsData = null;

                // 포즈 그리기
                if (lastPoseResults && lastPoseResults.poseLandmarks) {{
                    const landmarks = lastPoseResults.poseLandmarks.map(lm => ({{
                        x: 1 - lm.x, y: lm.y, z: lm.z, visibility: lm.visibility
                    }}));

                    if ({str(show_pose_skeleton).lower()}) {{
                        ctx.strokeStyle = '#00FF00';
                        ctx.lineWidth = 3;
                        POSE_CONNECTIONS.forEach(([s, e]) => {{
                            if (landmarks[s].visibility > 0.5 && landmarks[e].visibility > 0.5) {{
                                ctx.beginPath();
                                ctx.moveTo(landmarks[s].x * canvas.width, landmarks[s].y * canvas.height);
                                ctx.lineTo(landmarks[e].x * canvas.width, landmarks[e].y * canvas.height);
                                ctx.stroke();
                            }}
                        }});

                        landmarks.forEach((lm, i) => {{
                            if (lm.visibility > 0.5) {{
                                ctx.beginPath();
                                ctx.arc(lm.x * canvas.width, lm.y * canvas.height, 5, 0, 2 * Math.PI);
                                ctx.fillStyle = '#FF0000';
                                ctx.fill();
                            }}
                        }});
                    }}

                    poseData = landmarks;
                }}

                // 손 그리기
                if (lastHandsResults && lastHandsResults.multiHandLandmarks) {{
                    handsData = [];
                    lastHandsResults.multiHandLandmarks.forEach((handLandmarks, idx) => {{
                        const landmarks = handLandmarks.map(lm => ({{
                            x: 1 - lm.x, y: lm.y, z: lm.z
                        }}));
                        handsData.push(landmarks);

                        if ({str(show_hand_skeleton).lower()}) {{
                            const color = idx === 0 ? '#FF6B6B' : '#4ECDC4';
                            ctx.strokeStyle = color;
                            ctx.lineWidth = 2;

                            HAND_CONNECTIONS.forEach(([s, e]) => {{
                                ctx.beginPath();
                                ctx.moveTo(landmarks[s].x * canvas.width, landmarks[s].y * canvas.height);
                                ctx.lineTo(landmarks[e].x * canvas.width, landmarks[e].y * canvas.height);
                                ctx.stroke();
                            }});

                            landmarks.forEach(lm => {{
                                ctx.beginPath();
                                ctx.arc(lm.x * canvas.width, lm.y * canvas.height, 4, 0, 2 * Math.PI);
                                ctx.fillStyle = color;
                                ctx.fill();
                            }});
                        }}
                    }});
                }}

                // 상태 업데이트
                if (poseData) {{
                    statusEl.textContent = '포즈 감지됨' + (handsData ? ' + 손 ' + handsData.length + '개' : '');
                    statusEl.style.background = 'rgba(0, 128, 0, 0.7)';
                }} else {{
                    statusEl.textContent = '포즈를 찾을 수 없음';
                    statusEl.style.background = 'rgba(255, 165, 0, 0.7)';
                }}

                // Streamlit으로 전송
                if (window.Streamlit) {{
                    window.Streamlit.setComponentValue({{
                        pose_landmarks: poseData,
                        hand_landmarks: handsData,
                        timestamp: Date.now(),
                        fps: fps
                    }});
                }}
            }}

            async function initMediaPipe() {{
                loadingEl.style.display = 'block';
                startBtn.style.display = 'none';

                try {{
                    // Pose 초기화
                    pose = new Pose({{
                        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${{file}}`
                    }});
                    pose.setOptions({{
                        modelComplexity: {model_complexity},
                        smoothLandmarks: true,
                        minDetectionConfidence: 0.5,
                        minTrackingConfidence: 0.5
                    }});
                    pose.onResults(r => {{ lastPoseResults = r; }});

                    // Hands 초기화
                    hands = new Hands({{
                        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${{file}}`
                    }});
                    hands.setOptions({{
                        maxNumHands: 2,
                        modelComplexity: 1,
                        minDetectionConfidence: 0.5,
                        minTrackingConfidence: 0.5
                    }});
                    hands.onResults(r => {{ lastHandsResults = r; }});

                    // 카메라 시작
                    camera = new Camera(video, {{
                        onFrame: async () => {{
                            if (!isRunning) return;
                            updateFPS();
                            await Promise.all([
                                pose.send({{ image: video }}),
                                hands.send({{ image: video }})
                            ]);
                            drawResults();
                        }},
                        width: {width},
                        height: {height}
                    }});

                    await camera.start();
                    isRunning = true;
                    loadingEl.style.display = 'none';

                }} catch (error) {{
                    console.error('초기화 실패:', error);
                    loadingEl.innerHTML = '<div style="color: #ff6b6b;">카메라 접근 실패</div>';
                    setTimeout(() => {{
                        loadingEl.style.display = 'none';
                        startBtn.style.display = 'block';
                        startBtn.textContent = '다시 시도';
                    }}, 2000);
                }}
            }}

            startBtn.addEventListener('click', initMediaPipe);

            if (window.Streamlit) {{
                window.Streamlit.setFrameHeight({height + 20});
            }}
        </script>
    </body>
    </html>
    """

    result = components.html(html_code, height=height + 30, key=key)
    return result
