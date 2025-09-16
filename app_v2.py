import streamlit as st
import cv2
import numpy as np
from PIL import Image
import mediapipe as mp
import time
import math
import os
import base64

# 페이지 설정
st.set_page_config(
    page_title="춤마루 🎭",
    page_icon="💃",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# MediaPipe 초기화
@st.cache_resource
def load_mediapipe():
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    return mp_pose, mp_drawing, pose

# 세션 스테이트 초기화
if 'quiz_answers' not in st.session_state:
    st.session_state.quiz_answers = []
if 'dna_type' not in st.session_state:
    st.session_state.dna_type = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'landing'
if 'current_pose' not in st.session_state:
    st.session_state.current_pose = 0
if 'pose_attempts' not in st.session_state:
    st.session_state.pose_attempts = 0
if 'pose_success' not in st.session_state:
    st.session_state.pose_success = False
if 'captured_image' not in st.session_state:
    st.session_state.captured_image = None

# 춤 DNA 퀴즈 데이터
quiz_questions = [
    {
        "question": "음악이 나오면 나는...",
        "options": {
            "A": "몸이 저절로 물 흐르듯 움직여요 🌊 (vibe 타는 스타일)",
            "B": "순간 터지는 포인트 동작으로 어필! ⚡ (킬링파트 장인)"
        }
    },
    {
        "question": "춤 출 때 나는...",
        "options": {
            "A": "발바닥 단단히 붙이고 안정감 있게 💪 (그라운딩 퀸)",
            "B": "중력 무시하고 붕 떠있는 느낌 ☁️ (에어리 요정)"
        }
    },
    {
        "question": "친구와 춤 출 때 나는...",
        "options": {
            "A": "내 세계에 몰입해서 혼자만의 무드 🌙 (나홀로 아티스트)",
            "B": "다같이 텐션 맞춰가며 파티타임! 🎉 (분위기 메이커)"
        }
    },
    {
        "question": "나의 리듬감은...",
        "options": {
            "A": "잔잔한 파도처럼 길고 깊게 🌊 (chill한 웨이브)",
            "B": "불꽃처럼 짧고 강렬하게! 🔥 (핫한 비트)"
        }
    },
    {
        "question": "몸을 움직일 때 나는...",
        "options": {
            "A": "손끝 발끝까지 섬세하게 표현 ✨ (디테일 장인)",
            "B": "확실하게 딱딱 끊어주는 스타일 ⚡ (칼군무 마스터)"
        }
    },
    {
        "question": "춤을 배운다면 나는...",
        "options": {
            "A": "천천히 느낌 살려가며 배우고 싶어요 🍃 (감성 충전)",
            "B": "빨리 따라 하면서 텐션 올리고 싶어! 🔥 (에너지 뿜뿜)"
        }
    },
    {
        "question": "무대에 선다면 나는...",
        "options": {
            "A": "은은하게 스며드는 존재감 ✨ (시크한 카리스마)",
            "B": "한 번에 시선 강탈하는 임팩트! 💫 (어텐션 킬러)"
        }
    },
    {
        "question": "춤에서 더 중요한 건...",
        "options": {
            "A": "부드럽게 이어지는 플로우 🌊 (연결의 미학)",
            "B": "박자에 딱 맞는 강한 임팩트 💓 (리듬의 정석)"
        }
    }
]

# DNA 타입 정의
dna_types = {
    'flow': {
        'name': '🌊 Flow (흐름파)',
        'description': '부드럽고 연결감을 중시하는 당신은 물처럼 자연스러운 춤을 춥니다.',
        'color': '#4FC3F7',
        'video_url': 'https://www.youtube.com/watch?v=example1'
    },
    'burst': {
        'name': '⚡ Burst (폭발파)',
        'description': '강렬하고 순간적인 에너지를 가진 당신은 번개처럼 임팩트 있는 춤을 춥니다.',
        'color': '#FFD54F',
        'video_url': 'https://www.youtube.com/watch?v=example2'
    },
    'ground': {
        'name': '🌍 Ground (대지파)',
        'description': '안정감 있고 중심이 잡힌 당신은 대지처럼 든든한 춤을 춥니다.',
        'color': '#A1887F',
        'video_url': 'https://www.youtube.com/watch?v=example3'
    },
    'air': {
        'name': '☁️ Air (공중파)',
        'description': '가볍고 떠오르는 느낌을 가진 당신은 구름처럼 자유로운 춤을 춥니다.',
        'color': '#E1BEE7',
        'video_url': 'https://www.youtube.com/watch?v=example4'
    },
    'solo': {
        'name': '🌙 Solo (독주파)',
        'description': '개인적 몰입을 중시하는 당신은 달처럼 신비로운 춤을 춥니다.',
        'color': '#90A4AE',
        'video_url': 'https://www.youtube.com/watch?v=example5'
    },
    'harmony': {
        'name': '🎉 Harmony (화합파)',
        'description': '협조적 어울림을 좋아하는 당신은 태양처럼 밝은 춤을 춥니다.',
        'color': '#FFB74D',
        'video_url': 'https://www.youtube.com/watch?v=example6'
    },
    'grace': {
        'name': '✨ Grace (우아파)',
        'description': '세련되고 은은한 당신은 별처럼 우아한 춤을 춥니다.',
        'color': '#F8BBD9',
        'video_url': 'https://www.youtube.com/watch?v=example7'
    },
    'power': {
        'name': '🔥 Power (열정파)',
        'description': '역동적이고 강인한 당신은 불꽃처럼 열정적인 춤을 춥니다.',
        'color': '#FF8A65',
        'video_url': 'https://www.youtube.com/watch?v=example8'
    }
}

# 한국무용 기본 동작 정의
korean_poses = [
    {
        "name": "🙏 합장 (Prayer Pose)",
        "description": "두 손을 가슴 앞에서 모아 합장하는 동작",
        "instruction": "두 손을 가슴 앞에서 모아주세요",
        "check_function": "check_prayer_pose"
    },
    {
        "name": "🌅 해돋이 자세 (Sunrise Pose)",
        "description": "두 팔을 하늘 높이 들어 올리는 동작",
        "instruction": "두 팔을 하늘 높이 올려주세요",
        "check_function": "check_arms_up_pose"
    },
    {
        "name": "🦢 백조 자세 (Swan Pose)",
        "description": "한 팔을 옆으로 우아하게 뻗는 동작",
        "instruction": "오른팔을 옆으로 우아하게 뻗어주세요",
        "check_function": "check_swan_pose"
    },
    {
        "name": "🌸 꽃잎 자세 (Petal Pose)",
        "description": "두 팔을 아래로 부드럽게 늘어뜨리는 동작",
        "instruction": "두 팔을 자연스럽게 아래로 내려주세요",
        "check_function": "check_petal_pose"
    },
    {
        "name": "🎭 인사 자세 (Bow Pose)",
        "description": "고개를 숙여 정중하게 인사하는 동작",
        "instruction": "고개를 숙여 정중하게 인사해주세요",
        "check_function": "check_bow_pose"
    }
]

def calculate_angle(a, b, c):
    """세 점으로 각도 계산"""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
        
    return angle

def check_prayer_pose(landmarks):
    """합장 자세 확인"""
    try:
        # 양손 끝점
        left_wrist = landmarks[mp.solutions.pose.PoseLandmark.LEFT_WRIST]
        right_wrist = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_WRIST]
        
        # 손목 사이의 거리
        distance = abs(left_wrist.x - right_wrist.x)
        
        # 양 손이 가슴 앞에서 가까이 있는지 확인
        if distance < 0.1:  # 거리가 가까우면 성공
            return True, 95
        elif distance < 0.15:
            return False, 70
        else:
            return False, 30
    except:
        return False, 0

def check_arms_up_pose(landmarks):
    """팔 들어올리기 자세 확인"""
    try:
        left_shoulder = landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
        left_wrist = landmarks[mp.solutions.pose.PoseLandmark.LEFT_WRIST]
        right_shoulder = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]
        right_wrist = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_WRIST]
        
        # 양 팔이 어깨보다 위에 있는지 확인
        left_up = left_wrist.y < left_shoulder.y - 0.1
        right_up = right_wrist.y < right_shoulder.y - 0.1
        
        if left_up and right_up:
            return True, 90
        elif left_up or right_up:
            return False, 60
        else:
            return False, 20
    except:
        return False, 0

def check_swan_pose(landmarks):
    """백조 자세 확인 (오른팔 옆으로)"""
    try:
        right_shoulder = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]
        right_elbow = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_ELBOW]
        right_wrist = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_WRIST]
        
        # 팔이 옆으로 뻗어있는지 확인
        arm_extended = right_wrist.x > right_shoulder.x + 0.15
        arm_height = abs(right_wrist.y - right_shoulder.y) < 0.1
        
        if arm_extended and arm_height:
            return True, 85
        elif arm_extended:
            return False, 65
        else:
            return False, 25
    except:
        return False, 0

def check_petal_pose(landmarks):
    """꽃잎 자세 확인 (팔 아래로)"""
    try:
        left_shoulder = landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
        left_wrist = landmarks[mp.solutions.pose.PoseLandmark.LEFT_WRIST]
        right_shoulder = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]
        right_wrist = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_WRIST]
        
        # 양 팔이 어깨보다 아래에 있는지 확인
        left_down = left_wrist.y > left_shoulder.y + 0.1
        right_down = right_wrist.y > right_shoulder.y + 0.1
        
        if left_down and right_down:
            return True, 88
        elif left_down or right_down:
            return False, 55
        else:
            return False, 15
    except:
        return False, 0

def check_bow_pose(landmarks):
    """인사 자세 확인 (고개 숙이기)"""
    try:
        nose = landmarks[mp.solutions.pose.PoseLandmark.NOSE]
        left_shoulder = landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]
        
        # 어깨 중점
        shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2
        
        # 코가 어깨보다 아래에 있는지 확인 (고개 숙임)
        head_bowed = nose.y > shoulder_center_y - 0.05
        
        if head_bowed:
            return True, 80
        else:
            return False, 30
    except:
        return False, 0

def check_pose(landmarks, pose_name):
    """동작 확인 메인 함수"""
    pose_functions = {
        "check_prayer_pose": check_prayer_pose,
        "check_arms_up_pose": check_arms_up_pose,
        "check_swan_pose": check_swan_pose,
        "check_petal_pose": check_petal_pose,
        "check_bow_pose": check_bow_pose
    }
    
    current_pose = korean_poses[st.session_state.current_pose]
    check_function = pose_functions[current_pose["check_function"]]
    
    return check_function(landmarks)

def calculate_dna_type(answers):
    """답변을 기반으로 DNA 타입 계산"""
    scores = {
        'flow': 0, 'burst': 0, 'ground': 0, 'air': 0,
        'solo': 0, 'harmony': 0, 'grace': 0, 'power': 0
    }
    
    # 각 질문의 A/B 답변에 따라 점수 배분
    answer_mapping = [
        {'A': ['flow'], 'B': ['burst']},
        {'A': ['ground'], 'B': ['air']},
        {'A': ['solo'], 'B': ['harmony']},
        {'A': ['flow'], 'B': ['power']},
        {'A': ['grace'], 'B': ['burst']},
        {'A': ['grace'], 'B': ['power']},
        {'A': ['grace'], 'B': ['burst']},
        {'A': ['flow'], 'B': ['power']}
    ]
    
    for i, answer in enumerate(answers):
        if i < len(answer_mapping):
            for dna_type in answer_mapping[i][answer]:
                scores[dna_type] += 1
    
    # 가장 높은 점수의 타입 반환
    return max(scores.items(), key=lambda x: x[1])[0]

def landing_page():
    """랜딩 페이지"""
    # 메인 헤더
    st.markdown("""
    <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; margin-bottom: 2rem;'>
        <h1 style='color: white; font-size: 3.5rem; margin-bottom: 1rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>
            🎭 춤마루 🎭
        </h1>
        <h2 style='color: rgba(255,255,255,0.9); margin-bottom: 1.5rem; font-size: 1.5rem;'>
            나의 춤 DNA를 찾아보세요!
        </h2>
        <p style='color: rgba(255,255,255,0.8); font-size: 1.1rem; line-height: 1.6;'>
            한국의 몸짓을 MZ세대 감성으로 재해석한 특별한 경험<br>
            ✨ 8가지 질문으로 알아보는 나만의 춤 스타일 ✨
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 기능 소개 섹션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem; background: white; border-radius: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <div style='font-size: 2.5rem; margin-bottom: 1rem;'>🧬</div>
            <h3 style='color: #333; margin-bottom: 1rem;'>DNA 분석</h3>
            <p style='color: #666; font-size: 0.9rem;'>8가지 재미있는 질문으로<br>나만의 춤 성향 발견</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem; background: white; border-radius: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <div style='font-size: 2.5rem; margin-bottom: 1rem;'>💃</div>
            <h3 style='color: #333; margin-bottom: 1rem;'>동작 체험</h3>
            <p style='color: #666; font-size: 0.9rem;'>전문가 영상과 함께<br>한국 전통 몸짓 따라하기</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem; background: white; border-radius: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <div style='font-size: 2.5rem; margin-bottom: 1rem;'>🎨</div>
            <h3 style='color: #333; margin-bottom: 1rem;'>밈 생성</h3>
            <p style='color: #666; font-size: 0.9rem;'>나만의 춤 영상으로<br>재미있는 밈 만들기</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # CTA 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🧬 내 춤 DNA 찾기", type="primary", use_container_width=True, key="start_quiz"):
            st.session_state.current_page = 'quiz'
            st.rerun()
    
    # 하단 설명
    st.markdown("""
    <div style='text-align: center; margin-top: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 10px;'>
        <p style='color: #666; margin: 0; font-size: 0.9rem;'>
            💡 <strong>소요시간:</strong> 약 3-5분 | 
            📱 <strong>호환성:</strong> 웹캠 지원 브라우저 | 
            🎯 <strong>난이도:</strong> 누구나 쉽게
        </p>
    </div>
    """, unsafe_allow_html=True)

def quiz_page():
    """퀴즈 페이지"""
    # 헤더 디자인
    st.markdown("""
    <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 2rem;'>
        <h1 style='color: white; margin: 0; font-size: 2rem;'>🧬 춤 DNA 분석 퀴즈</h1>
        <p style='color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0;'>나만의 춤 스타일을 찾아보세요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    current_q_num = len(st.session_state.quiz_answers)
    progress = current_q_num / len(quiz_questions)
    
    # 프로그레스 바 개선
    st.markdown(f"""
    <div style='margin: 1rem 0;'>
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
            <span style='font-weight: bold; color: #667eea;'>질문 {current_q_num + 1}/{len(quiz_questions)}</span>
            <span style='color: #888;'>{int(progress * 100)}% 완료</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(progress)
    
    # 이전 버튼 (첫 번째 질문이 아닐 때만 표시)
    if current_q_num > 0:
        col_back, col_space = st.columns([1, 4])
        with col_back:
            if st.button("⬅️ 이전", key="back_button"):
                st.session_state.quiz_answers.pop()  # 마지막 답변 제거
                st.rerun()
    
    if current_q_num < len(quiz_questions):
        question = quiz_questions[current_q_num]
        
        # 질문 카드 디자인
        st.markdown(f"""
        <div style='background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 2rem 0;'>
            <h2 style='text-align: center; color: #333; margin-bottom: 1.5rem; font-size: 1.5rem;'>
                {question['question']}
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        # 힌트 텍스트 추가
        hint_texts = [
            "💡 본능적으로 끌리는 답을 선택해주세요!",
            "🎵 음악을 상상하며 답해보세요!",
            "💃 친구들과 함께 있는 상황을 떠올려보세요!",
            "🌊 나만의 리듬을 생각해보세요!",
            "✨ 몸의 움직임을 상상해보세요!",
            "📚 학습 스타일을 떠올려보세요!",
            "🎭 무대 위의 나를 상상해보세요!",
            "💫 춤의 본질에 대해 생각해보세요!"
        ]
        
        if current_q_num < len(hint_texts):
            st.markdown(f"""
            <div style='text-align: center; margin: 1rem 0; padding: 1rem; background: #f8f9fa; border-radius: 10px; border-left: 4px solid #667eea;'>
                <p style='margin: 0; color: #666; font-style: italic;'>{hint_texts[current_q_num]}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 선택지 버튼 개선 - 큰 버튼으로 통합
        st.markdown("<div style='margin: 2rem 0;'>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            # A 선택지 - 하나의 큰 버튼으로 통합
            button_html = f"""
            <div style='margin-bottom: 1rem;'>
                <div style='background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); padding: 1.5rem; border-radius: 15px; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border: 2px solid transparent; transition: all 0.3s ease;'>
                    <div style='color: #333; font-size: 1.1rem; font-weight: bold; line-height: 1.4;'>
                        {question['options']['A']}
                    </div>
                </div>
            </div>
            """
            st.markdown(button_html, unsafe_allow_html=True)
            
            # 투명 버튼으로 클릭 감지
            if st.button("선택 A", key=f"A_{current_q_num}", use_container_width=True, 
                        help=question['options']['A']):
                st.session_state.quiz_answers.append('A')
                st.rerun()
        
        with col2:
            # B 선택지 - 하나의 큰 버튼으로 통합
            button_html = f"""
            <div style='margin-bottom: 1rem;'>
                <div style='background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%); padding: 1.5rem; border-radius: 15px; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border: 2px solid transparent; transition: all 0.3s ease;'>
                    <div style='color: #333; font-size: 1.1rem; font-weight: bold; line-height: 1.4;'>
                        {question['options']['B']}
                    </div>
                </div>
            </div>
            """
            st.markdown(button_html, unsafe_allow_html=True)
            
            # 투명 버튼으로 클릭 감지
            if st.button("선택 B", key=f"B_{current_q_num}", use_container_width=True,
                        help=question['options']['B']):
                st.session_state.quiz_answers.append('B')
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 응답한 질문들 미리보기 (선택사항)
        if current_q_num > 0:
            st.markdown("---")
            with st.expander(f"📋 지금까지의 답변 ({current_q_num}개)"):
                for i, answer in enumerate(st.session_state.quiz_answers):
                    prev_question = quiz_questions[i]
                    selected_option = prev_question['options'][answer]
                    st.write(f"**{i+1}.** {prev_question['question']}")
                    st.write(f"→ {selected_option}")
    
    else:
        # 퀴즈 완료 페이지
        st.markdown("""
        <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; margin: 2rem 0;'>
            <h1 style='color: white; font-size: 2.5rem; margin-bottom: 1rem;'>🎉 퀴즈 완료!</h1>
            <p style='color: rgba(255,255,255,0.9); font-size: 1.2rem; margin-bottom: 2rem;'>
                8개의 질문에 모두 답변해주셨습니다.<br>
                이제 당신만의 춤 DNA를 확인해보세요!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 퀴즈 완료
        dna_type = calculate_dna_type(st.session_state.quiz_answers)
        st.session_state.dna_type = dna_type
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("🔄 다시 하기", use_container_width=True):
                st.session_state.quiz_answers = []
                st.rerun()
        
        with col2:
            if st.button("🎉 결과 확인하기", type="primary", use_container_width=True):
                st.session_state.current_page = 'result'
                st.rerun()
        
        with col3:
            if st.button("🏠 처음으로", use_container_width=True):
                st.session_state.quiz_answers = []
                st.session_state.dna_type = None
                st.session_state.current_page = 'landing'
                st.rerun()

def result_page():
    """결과 페이지"""
    if st.session_state.dna_type:
        dna_info = dna_types[st.session_state.dna_type]
        
        st.markdown(f"""
        <div style='text-align: center; padding: 3rem; background: white; border-radius: 20px; margin: 2rem 0; border: 4px solid {dna_info['color']}; box-shadow: 0 8px 16px rgba(0,0,0,0.1);'>
            <h1 style='font-size: 2.5rem; margin-bottom: 1.5rem; color: {dna_info['color']}; font-weight: bold;'>
                {dna_info['name']}
            </h1>
            <p style='font-size: 1.3rem; color: #333; font-weight: 500; line-height: 1.6; background: #f8f9fa; padding: 1rem; border-radius: 10px;'>
                {dna_info['description']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🎥 전문가 영상 보기")
        
        # 38초 전문가 영상 플레이스홀더
        st.markdown("""
        <div style='text-align: center; padding: 2rem; background: #f8f9fa; border-radius: 15px; border: 2px solid #667eea; margin: 1rem 0;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>🎬</div>
            <h4 style='color: #667eea; margin-bottom: 1rem;'>전문가 시연 영상 (38초)</h4>
            <p style='color: #666; font-size: 0.9rem;'>여러 동작을 연결한 완성된 시연</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 영상 파일 표시 (절대 경로 사용)
        video_path = os.path.join(os.getcwd(), "videos", "expert_dance_18sec.mp4")
        
        if os.path.exists(video_path):
            # 1차: Streamlit 기본 방식
            video_success = False
            try:
                st.video(video_path)
                video_success = True
            except Exception as e:
                st.warning(f"기본 영상 플레이어 오류: {str(e)}")
                
            # 2차: HTML5 비디오 (기본 방식 실패 시)
            if not video_success:
                try:
                    st.info("대체 플레이어로 영상을 로드합니다...")
                    with open(video_path, "rb") as video_file:
                        video_bytes = video_file.read()
                        video_base64 = base64.b64encode(video_bytes).decode()
                        
                    # 더 안정적인 HTML5 비디오
                    video_html = f"""
                    <div style="text-align: center; margin: 20px 0;">
                        <video width="100%" height="400" controls preload="auto" 
                               style="max-width: 100%; background: #000; border-radius: 10px;">
                            <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
                            <p>브라우저가 비디오를 지원하지 않습니다.</p>
                        </video>
                    </div>
                    """
                    st.markdown(video_html, unsafe_allow_html=True)
                except Exception as e2:
                    st.error(f"영상 로딩 실패: {str(e2)}")
                    st.info("🎬 영상 파일에 문제가 있을 수 있습니다. 파일을 다시 확인해주세요.")
        else:
            st.info("🎬 전문가 시연 영상이 여기에 표시됩니다")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("💃 함께 만들어볼까요?", type="primary", use_container_width=True):
                st.session_state.current_page = 'dance'
                st.rerun()

def dance_page():
    """동작 인식 페이지"""
    # 상단 네비게이션
    col_nav1, col_nav2, col_nav3 = st.columns([1, 3, 1])
    with col_nav1:
        if st.button("⬅️ 이전", key="dance_back"):
            st.session_state.current_page = 'result'
            st.rerun()
    with col_nav3:
        if st.button("🏠 홈", key="dance_home"):
            st.session_state.quiz_answers = []
            st.session_state.dna_type = None
            st.session_state.current_page = 'landing'
            st.rerun()
    
    # 메인 헤더
    st.markdown("""
    <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin: 1rem 0;'>
        <h1 style='color: white; margin: 0; font-size: 2.5rem;'>💃 동작 따라하기</h1>
        <p style='color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 1.1rem;'>웹캠을 통해 한국 전통 몸짓을 체험해보세요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 현재 DNA 타입 표시
    if st.session_state.dna_type:
        dna_info = dna_types[st.session_state.dna_type]
        st.markdown(f"""
        <div style='text-align: center; padding: 1.5rem; background: white; border-radius: 12px; margin: 1rem 0; border: 3px solid {dna_info['color']}; box-shadow: 0 4px 8px rgba(0,0,0,0.1);'>
            <p style='margin: 0; color: #333; font-size: 1.2rem; font-weight: bold;'>
                <strong style='color: {dna_info['color']};'>당신의 춤 DNA:</strong> {dna_info['name']}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # 현재 동작 정보
    current_pose = korean_poses[st.session_state.current_pose]
    
    # 진행상황 표시
    st.markdown(f"""
    <div style='margin: 1rem 0;'>
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
            <span style='font-weight: bold; color: #667eea;'>동작 {st.session_state.current_pose + 1}/{len(korean_poses)}</span>
            <span style='color: #888;'>시도: {st.session_state.pose_attempts}/3</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    progress = st.session_state.current_pose / len(korean_poses)
    st.progress(progress)
    
    # 현재 동작 설명
    st.markdown(f"""
    <div style='background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 2rem 0;'>
        <h2 style='text-align: center; color: #333; margin-bottom: 1rem;'>
            {current_pose['name']}
        </h2>
        <p style='text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 1rem;'>
            {current_pose['description']}
        </p>
        <div style='text-align: center; padding: 2rem; background: #667eea; border-radius: 12px; border: 3px solid #4c63d2; box-shadow: 0 4px 8px rgba(0,0,0,0.1);'>
            <p style='margin: 0; color: white; font-weight: bold; font-size: 1.2rem;'>
                📋 {current_pose['instruction']}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 영상 영역 - 전문가 시범과 사용자 웹캠
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("### 🎥 전문가 시범 영상")
        
        # 동작별 시범 영상 - 5초컷 영상들 (모든 동작에 같은 영상 사용)
        current_pose_videos = {
            0: "videos/expert_dance_5sec.mp4",  # 합장 시범
            1: "videos/expert_dance_5sec.mp4",  # 해돋이 시범
            2: "videos/expert_dance_5sec.mp4",  # 백조 시범
            3: "videos/expert_dance_5sec.mp4",  # 꽃잎 시범
            4: "videos/expert_dance_5sec.mp4"   # 인사 시범
        }
        
        # 현재 동작의 시범 영상 표시
        if st.session_state.current_pose in current_pose_videos:
            st.markdown(f"**{current_pose['name']} 시범**")
            # 시범 영상 플레이스홀더 (실제 영상 URL로 교체 예정)
            st.markdown("""
            <div style='text-align: center; padding: 2rem; background: #e8f4f8; border-radius: 10px; min-height: 200px; display: flex; align-items: center; justify-content: center; border: 2px solid #667eea;'>
                <div>
                    <div style='font-size: 3rem; margin-bottom: 1rem;'>🎬</div>
                    <p style='color: #667eea; font-weight: bold;'>전문가 시범 영상</p>
                    <p style='color: #888; font-size: 0.9rem;'>5초 시범 동작</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 5초 시범 영상 표시 (절대 경로 사용)
            video_path_5sec = os.path.join(os.getcwd(), "videos", "expert_dance_5sec.mp4")
            
            if os.path.exists(video_path_5sec):
                try:
                    st.video(video_path_5sec)
                except Exception as e:
                    st.warning(f"영상 로딩 중 오류: {str(e)}")
                    # 대체 방법: HTML video 태그 사용
                    with open(video_path_5sec, "rb") as video_file:
                        video_bytes = video_file.read()
                        video_base64 = base64.b64encode(video_bytes).decode()
                        video_html = f"""
                        <video width="100%" height="250" controls autoplay loop>
                            <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
                            브라우저가 비디오를 지원하지 않습니다.
                        </video>
                        """
                        st.markdown(video_html, unsafe_allow_html=True)
            else:
                st.info("🎬 전문가 시범 영상이 여기에 표시됩니다")
    
    with col2:
        st.markdown("### 📹 내 웹캠")
        
        # 웹캠 시작/정지 버튼
        if st.button("📷 웹캠 시작", key="start_webcam", use_container_width=True):
            st.session_state.webcam_active = True
            
        # 웹캠 플레이스홀더 (실제 구현시에는 streamlit-webrtc 등 사용)
        webcam_placeholder = st.empty()
        
        # 시뮬레이션용 - 실제로는 웹캠 피드를 여기에 표시
        webcam_placeholder.markdown("""
        <div style='text-align: center; padding: 2rem; background: #f0f0f0; border-radius: 10px; min-height: 200px; display: flex; align-items: center; justify-content: center; border: 2px dashed #ccc;'>
            <div>
                <div style='font-size: 3rem; margin-bottom: 1rem;'>📷</div>
                <p style='color: #666; font-weight: bold;'>사용자 웹캠</p>
                <p style='color: #888; font-size: 0.9rem;'>실시간 포즈 감지</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 동작 체크 영역
    st.markdown("### 🎯 동작 체크")
    
    col3, col4 = st.columns([1, 1])
    
    with col3:
        # 동작 시도 버튼 (시뮬레이션용)
        if st.button("✨ 동작 확인", key="check_pose", use_container_width=True, type="primary"):
            # 시뮬레이션: 랜덤하게 성공/실패 결정
            import random
            success_rate = 0.7  # 70% 성공률
            
            if random.random() < success_rate:
                st.session_state.pose_success = True
                st.session_state.captured_image = f"pose_{st.session_state.current_pose}_success.jpg"
                st.success(f"🎉 {current_pose['name']} 성공!")
                
                # 다음 동작으로 이동
                if st.session_state.current_pose < len(korean_poses) - 1:
                    st.session_state.current_pose += 1
                    st.session_state.pose_attempts = 0
                    time.sleep(1)
                    st.rerun()
                else:
                    # 모든 동작 완료
                    st.session_state.current_page = 'meme'
                    st.rerun()
            else:
                st.session_state.pose_attempts += 1
                
                if st.session_state.pose_attempts >= 3:
                    st.warning("💪 다음 동작으로 넘어가요!")
                    # 다음 동작으로 강제 이동
                    if st.session_state.current_pose < len(korean_poses) - 1:
                        st.session_state.current_pose += 1
                        st.session_state.pose_attempts = 0
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.session_state.current_page = 'meme'
                        st.rerun()
                else:
                    st.error(f"😅 다시 시도해보세요! ({3 - st.session_state.pose_attempts}번 더 가능)")
    
    with col4:
        # 동작 스킵 버튼
        if st.button("⏭️ 다음 동작", key="skip_pose", use_container_width=True):
            if st.session_state.current_pose < len(korean_poses) - 1:
                st.session_state.current_pose += 1
                st.session_state.pose_attempts = 0
                st.rerun()
            else:
                st.session_state.current_page = 'meme'
                st.rerun()
        
        # 포즈 리스트 표시
        st.markdown("### 📋 동작 목록")
        for i, pose in enumerate(korean_poses):
            if i == st.session_state.current_pose:
                st.markdown(f"**👉 {pose['name']}** (현재)")
            elif i < st.session_state.current_pose:
                st.markdown(f"✅ {pose['name']}")
            else:
                st.markdown(f"⏳ {pose['name']}")

def meme_page():
    """밈 생성 페이지"""
    # 상단 네비게이션
    col_nav1, col_nav2, col_nav3 = st.columns([1, 3, 1])
    with col_nav1:
        if st.button("⬅️ 이전", key="meme_back"):
            st.session_state.current_page = 'dance'
            st.rerun()
    with col_nav3:
        if st.button("🏠 홈", key="meme_home"):
            st.session_state.quiz_answers = []
            st.session_state.dna_type = None
            st.session_state.current_page = 'landing'
            st.rerun()
    
    # 완료 축하 헤더
    st.markdown("""
    <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; margin: 1rem 0;'>
        <h1 style='color: white; font-size: 3rem; margin-bottom: 1rem;'>🎉 축하합니다! 🎉</h1>
        <p style='color: rgba(255,255,255,0.9); font-size: 1.3rem; margin-bottom: 1rem;'>
            한국 전통 몸짓 체험을 완료했습니다!
        </p>
        <p style='color: rgba(255,255,255,0.8); font-size: 1.1rem;'>
            나만의 춤 밈이 생성되었어요 ✨
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # DNA 타입과 완료한 동작 수 표시
    if st.session_state.dna_type:
        dna_info = dna_types[st.session_state.dna_type]
        st.markdown(f"""
        <div style='text-align: center; padding: 2.5rem; background: white; border-radius: 15px; margin: 2rem 0; border: 4px solid {dna_info['color']}; box-shadow: 0 8px 16px rgba(0,0,0,0.15);'>
            <h3 style='margin: 0 0 1rem 0; color: {dna_info['color']}; font-weight: bold; font-size: 1.3rem;'>🧬 당신의 춤 DNA</h3>
            <h2 style='margin: 0 0 1.5rem 0; color: #333; font-weight: bold; font-size: 1.8rem;'>{dna_info['name']}</h2>
            <p style='margin: 0 0 1.5rem 0; color: #666; font-size: 1.1rem; font-weight: 500; line-height: 1.5; background: #f8f9fa; padding: 1rem; border-radius: 8px;'>{dna_info['description']}</p>
            <div style='background: {dna_info['color']}22; padding: 1rem; border-radius: 8px; border: 2px solid {dna_info['color']}66;'>
                <p style='margin: 0; color: #333; font-size: 1rem; font-weight: bold;'>
                    완료한 동작: {st.session_state.current_pose + 1}/{len(korean_poses)}개
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 밈 프리뷰 영역
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🎨 나만의 춤 밈")
        
        # 개선된 밈 카드 디자인
        if st.session_state.dna_type:
            dna_info = dna_types[st.session_state.dna_type]
            completed_poses = min(st.session_state.current_pose + 1, len(korean_poses))
            
            st.markdown(f"""
            <div style='position: relative; text-align: center; padding: 2.5rem; background: linear-gradient(135deg, {dna_info['color']}66 0%, {dna_info['color']}88 100%); border-radius: 20px; min-height: 400px; display: flex; align-items: center; justify-content: center; border: 4px solid #fff; box-shadow: 0 12px 24px rgba(0,0,0,0.15);'>
                <div>
                    <div style='font-size: 5rem; margin-bottom: 1.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);'>💃</div>
                    <h2 style='color: #fff; margin-bottom: 1rem; font-size: 1.8rem; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);'>나는 {dna_info['name']}!</h2>
                    <p style='color: #f0f0f0; font-size: 1.2rem; margin-bottom: 1.5rem; font-weight: 500; text-shadow: 1px 1px 2px rgba(0,0,0,0.4);'>#춤마루 #한국전통몸짓</p>
                    <div style='background: rgba(255,255,255,0.9); padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
                        <p style='color: #333; font-size: 1rem; margin: 0; font-weight: bold;'>🏆 완성한 동작: {completed_poses}개</p>
                    </div>
                    <p style='color: #f5f5f5; font-size: 1rem; font-style: italic; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);'>"한국의 몸짓을 현대감각으로!"</p>
                </div>
                <div style='position: absolute; top: 15px; right: 20px; background: rgba(255,255,255,0.9); padding: 0.5rem; border-radius: 5px;'>
                    <span style='color: #333; font-size: 0.8rem; font-weight: bold;'>춤마루</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='text-align: center; padding: 2rem; background: #f0f0f0; border-radius: 15px; min-height: 300px;'>
                <p>DNA 타입이 설정되지 않았습니다.</p>
            </div>
            """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("### 📱 공유하기")
        
        # 다운로드 버튼
        st.markdown("""
        <div style='margin-bottom: 1rem;'>
            <button style='width: 100%; padding: 1rem; background: #4CAF50; color: white; border: none; border-radius: 10px; font-size: 1rem; cursor: pointer;'>
                📱 이미지 다운로드
            </button>
        </div>
        """, unsafe_allow_html=True)
        
        # SNS 공유 버튼들
        st.markdown("""
        <div style='display: flex; flex-direction: column; gap: 0.5rem;'>
            <button style='width: 100%; padding: 0.8rem; background: #1DA1F2; color: white; border: none; border-radius: 8px; font-size: 0.9rem; cursor: pointer;'>
                🐦 트위터 공유
            </button>
            <button style='width: 100%; padding: 0.8rem; background: #1877F2; color: white; border: none; border-radius: 8px; font-size: 0.9rem; cursor: pointer;'>
                📘 페이스북 공유
            </button>
            <button style='width: 100%; padding: 0.8rem; background: #E4405F; color: white; border: none; border-radius: 8px; font-size: 0.9rem; cursor: pointer;'>
                📷 인스타그램 공유
            </button>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 통계 정보
        st.markdown("### 📊 체험 결과")
        st.markdown(f"""
        - **DNA 타입**: {dna_info['name'] if st.session_state.dna_type else '미정'}
        - **완료 동작**: {st.session_state.current_pose + 1}개
        - **총 시도**: {st.session_state.pose_attempts}회
        - **성공률**: 85% 🎯
        """)
    
    # 하단 액션 버튼들
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 다른 동작 체험", use_container_width=True):
            # 동작만 리셋하고 다시 체험
            st.session_state.current_pose = 0
            st.session_state.pose_attempts = 0
            st.session_state.pose_success = False
            st.session_state.current_page = 'dance'
            st.rerun()
    
    with col2:
        if st.button("🧬 다른 DNA 찾기", use_container_width=True):
            # 퀴즈부터 다시 시작
            st.session_state.quiz_answers = []
            st.session_state.dna_type = None
            st.session_state.current_pose = 0
            st.session_state.pose_attempts = 0
            st.session_state.current_page = 'quiz'
            st.rerun()
    
    with col3:
        if st.button("🏠 처음으로", use_container_width=True, type="primary"):
            # 전체 리셋
            st.session_state.quiz_answers = []
            st.session_state.dna_type = None
            st.session_state.current_pose = 0
            st.session_state.pose_attempts = 0
            st.session_state.pose_success = False
            st.session_state.captured_image = None
            st.session_state.current_page = 'landing'
            st.rerun()
    
    # 하단 안내
    st.markdown("""
    <div style='text-align: center; margin-top: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 10px;'>
        <p style='color: #666; margin: 0; font-size: 0.9rem;'>
            🎭 <strong>춤마루</strong>와 함께 한국 전통 문화를 현대적으로 체험해보세요!<br>
            더 많은 동작과 기능이 곧 업데이트됩니다. ✨
        </p>
    </div>
    """, unsafe_allow_html=True)

# 메인 앱 로직
def main():
    if st.session_state.current_page == 'landing':
        landing_page()
    elif st.session_state.current_page == 'quiz':
        quiz_page()
    elif st.session_state.current_page == 'result':
        result_page()
    elif st.session_state.current_page == 'dance':
        dance_page()
    elif st.session_state.current_page == 'meme':
        meme_page()

if __name__ == "__main__":
    main()
