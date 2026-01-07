# 춤마루 MVP v13 Streamlit (2025.12.XX)
# v13: B2B 시스템 추가 - 단체/학원 계정, 구독 플랜, 강사/학생 관리, 커스텀 동작 세트
# v12 기능 포함: 전문가 유입 시스템 - DNA 타입별 영상 업로드, 피드백, 디지털 평판 시스템
# v11 기능 포함: DNA 갤러리, 전통무용 아카이브 섹션 추가
# v10 기능 포함: 부위별 세부 영상 기능 추가 (메인 영상 + 세부 동작 영상)
# 세부 영상 개수에 따라 자동 레이아웃 변경: 3개 이하(일렬), 4-5개(2줄), 6개 이상(탭)
# 기본/확장/창작 동작 모두 세부 영상 지원
# 완전한 Streamlit 구현 버전 - 10개 질문, 8개 DNA 타입, 12개 기본동작, 6개 확장동작, 8개 창작동작 포함
# 확장/창작 동작에도 웹캠 및 상세 설명 추가, 동작 배우기 페이지 개선
# 밈 템플릿: DNA 영상 배경 + 텍스트 외곽선 효과 + 다운로드 기능
# GIF 밈 생성: 2-3초 움직이는 밈 카드 (소셜 미디어 최적화)
# MediaPipe 실제 구현, 영상 업로드 지원, 웹캠 동작 인식 기능

import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import json
import time
import random
import io
import os
from datetime import datetime
from pathlib import Path
import pandas as pd

# WebRTC (브라우저 카메라 접근 - Streamlit Cloud 필수)
# OpenCV cv2.VideoCapture는 서버에서 실행되므로 클라우드에서 작동 안 함
# WebRTC는 브라우저의 getUserMedia API를 사용하여 카메라 접근
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av
from streamlit_autorefresh import st_autorefresh
import threading

# =============================================================================
# WebRTC 공유 상태 (모듈 레벨 - 리렌더링 간 유지)
# =============================================================================
_webrtc_state_lock = threading.Lock()
_webrtc_shared_state = {
    'action_page': {'timestamp_ms': 0, 'feedback_score': 0, 'feedback_messages': [], 'joint_coverage': 0, 'pose_detected': False},
    'pose_test_page': {'timestamp_ms': 0, 'feedback_score': 0, 'feedback_messages': [], 'joint_coverage': 0, 'pose_detected': False, 'hands_detected': 0}
}

def get_webrtc_state(page_key):
    with _webrtc_state_lock:
        return _webrtc_shared_state.get(page_key, {}).copy()

def update_webrtc_state(page_key, updates):
    with _webrtc_state_lock:
        if page_key in _webrtc_shared_state:
            _webrtc_shared_state[page_key].update(updates)

def reset_webrtc_state(page_key):
    with _webrtc_state_lock:
        if page_key == 'action_page':
            _webrtc_shared_state[page_key] = {'timestamp_ms': 0, 'feedback_score': 0, 'feedback_messages': [], 'joint_coverage': 0, 'pose_detected': False}
        elif page_key == 'pose_test_page':
            _webrtc_shared_state[page_key] = {'timestamp_ms': 0, 'feedback_score': 0, 'feedback_messages': [], 'joint_coverage': 0, 'pose_detected': False, 'hands_detected': 0}

@st.cache_resource
def get_pose_landmarker(detection_conf=0.5, tracking_conf=0.5):
    pose_model_path = os.path.join(os.path.dirname(__file__), "models", "pose_landmarker_lite.task")
    pose_base_options = python.BaseOptions(model_asset_path=pose_model_path)
    pose_options = vision.PoseLandmarkerOptions(
        base_options=pose_base_options,
        running_mode=vision.RunningMode.VIDEO,
        min_pose_detection_confidence=detection_conf,
        min_tracking_confidence=tracking_conf
    )
    return vision.PoseLandmarker.create_from_options(pose_options)

@st.cache_resource
def get_hand_landmarker(detection_conf=0.5, tracking_conf=0.5):
    hand_model_path = os.path.join(os.path.dirname(__file__), "models", "hand_landmarker.task")
    hand_base_options = python.BaseOptions(model_asset_path=hand_model_path)
    hand_options = vision.HandLandmarkerOptions(
        base_options=hand_base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=detection_conf,
        min_tracking_confidence=tracking_conf
    )
    return vision.HandLandmarker.create_from_options(hand_options)

# ==================== 페이지 설정 ====================
st.set_page_config(page_title="춤마루 (Choomaru)", page_icon="💃", layout="wide")

# ==================== 데이터 저장 시스템 ====================
# 데이터 파일 경로
DATA_DIR = Path("data")
EXPERTS_FILE = DATA_DIR / "experts.json"
VIDEOS_FILE = DATA_DIR / "videos.json"
FEEDBACK_FILE = DATA_DIR / "feedback.json"

# B2B 데이터 파일 경로
ORGANIZATIONS_FILE = DATA_DIR / "organizations.json"
SUBSCRIPTIONS_FILE = DATA_DIR / "subscriptions.json"
INSTRUCTORS_FILE = DATA_DIR / "instructors.json"
STUDENTS_FILE = DATA_DIR / "students.json"
GROUPS_FILE = DATA_DIR / "groups.json"
PROGRESS_FILE = DATA_DIR / "progress.json"

# 데이터 디렉토리 생성
DATA_DIR.mkdir(exist_ok=True)

# 전문가 업로드 영상 저장 디렉토리
EXPERT_VIDEOS_DIR = Path("expert_videos")
EXPERT_VIDEOS_DIR.mkdir(exist_ok=True)

def load_json(file_path):
    """JSON 파일 로드"""
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json(file_path, data):
    """JSON 파일 저장"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_experts():
    """전문가 데이터 로드"""
    return load_json(EXPERTS_FILE)

def save_expert(expert_id, expert_data):
    """전문가 데이터 저장"""
    experts = get_experts()
    experts[expert_id] = expert_data
    save_json(EXPERTS_FILE, experts)

def get_videos():
    """영상 데이터 로드"""
    return load_json(VIDEOS_FILE)

def save_video(video_id, video_data):
    """영상 데이터 저장"""
    videos = get_videos()
    videos[video_id] = video_data
    save_json(VIDEOS_FILE, videos)

def get_feedback():
    """피드백 데이터 로드"""
    return load_json(FEEDBACK_FILE)

def save_feedback(feedback_id, feedback_data):
    """피드백 데이터 저장"""
    feedbacks = get_feedback()
    feedbacks[feedback_id] = feedback_data
    save_json(FEEDBACK_FILE, feedbacks)

def calculate_reputation_score(expert_id):
    """전문가 평판 점수 계산"""
    videos = get_videos()
    feedbacks = get_feedback()
    
    expert_videos = [v for v in videos.values() if v.get('expert_id') == expert_id]
    video_ids = [v['id'] for v in expert_videos]
    expert_feedbacks = [f for f in feedbacks.values() if f.get('video_id') in video_ids]
    
    # 평판 점수 계산: (업로드 영상 수 × 10) + (총 좋아요 × 2) + (댓글 수 × 5) + (평점 평균 × 20)
    video_count = len(expert_videos)
    total_likes = sum(1 for f in expert_feedbacks if f.get('type') == 'like')
    comment_count = sum(1 for f in expert_feedbacks if f.get('type') == 'comment')
    ratings = [f.get('rating', 0) for f in expert_feedbacks if f.get('rating')]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    score = (video_count * 10) + (total_likes * 2) + (comment_count * 5) + (avg_rating * 20)
    return int(score)

def get_reputation_level(score):
    """평판 점수에 따른 레벨 반환"""
    if score >= 1000:
        return {"level": "플래티넘", "emoji": "💎", "color": "#E5E4E2"}
    elif score >= 500:
        return {"level": "골드", "emoji": "🥇", "color": "#FFD700"}
    elif score >= 200:
        return {"level": "실버", "emoji": "🥈", "color": "#C0C0C0"}
    else:
        return {"level": "브론즈", "emoji": "🥉", "color": "#CD7F32"}

# ==================== B2B 데이터 관리 함수 ====================

def get_organizations():
    """단체 데이터 로드"""
    return load_json(ORGANIZATIONS_FILE)

def save_organization(org_id, org_data):
    """단체 데이터 저장"""
    orgs = get_organizations()
    orgs[org_id] = org_data
    save_json(ORGANIZATIONS_FILE, orgs)

def get_subscriptions():
    """구독 데이터 로드"""
    return load_json(SUBSCRIPTIONS_FILE)

def save_subscription(sub_id, sub_data):
    """구독 데이터 저장"""
    subs = get_subscriptions()
    subs[sub_id] = sub_data
    save_json(SUBSCRIPTIONS_FILE, subs)

def get_instructors():
    """강사 데이터 로드"""
    return load_json(INSTRUCTORS_FILE)

def save_instructor(instructor_id, instructor_data):
    """강사 데이터 저장"""
    instructors = get_instructors()
    instructors[instructor_id] = instructor_data
    save_json(INSTRUCTORS_FILE, instructors)

def get_students():
    """학생 데이터 로드"""
    return load_json(STUDENTS_FILE)

def save_student(student_id, student_data):
    """학생 데이터 저장"""
    students = get_students()
    students[student_id] = student_data
    save_json(STUDENTS_FILE, students)

def get_groups():
    """그룹 데이터 로드"""
    return load_json(GROUPS_FILE)

def save_group(group_id, group_data):
    """그룹 데이터 저장"""
    groups = get_groups()
    groups[group_id] = group_data
    save_json(GROUPS_FILE, groups)

def get_progress():
    """진행 상황 데이터 로드"""
    return load_json(PROGRESS_FILE)

def save_progress(progress_id, progress_data):
    """진행 상황 데이터 저장"""
    progress = get_progress()
    progress[progress_id] = progress_data
    save_json(PROGRESS_FILE, progress)

# ==================== 구독 플랜 정의 ====================

SUBSCRIPTION_PLANS = {
    "basic": {
        "name": "Basic",
        "price": 50000,  # 월 5만원
        "basic_actions": 5,
        "expanded_actions": 0,
        "creative_actions": 0,
        "custom_actions": False,
        "max_instructors": 2,
        "max_students": 20,
        "features": ["기본 동작 5개", "강사 2명", "학생 20명"]
    },
    "standard": {
        "name": "Standard",
        "price": 100000,  # 월 10만원
        "basic_actions": 8,
        "expanded_actions": 3,
        "creative_actions": 0,
        "custom_actions": False,
        "max_instructors": 5,
        "max_students": 50,
        "features": ["기본 동작 8개", "확장 동작 3개", "강사 5명", "학생 50명"]
    },
    "premium": {
        "name": "Premium",
        "price": 200000,  # 월 20만원
        "basic_actions": 12,
        "expanded_actions": 6,
        "creative_actions": 4,
        "custom_actions": False,
        "max_instructors": 10,
        "max_students": 200,
        "features": ["기본 동작 12개", "확장 동작 6개", "창작 동작 4개", "강사 10명", "학생 200명"]
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 500000,  # 월 50만원
        "basic_actions": 12,
        "expanded_actions": 6,
        "creative_actions": 8,
        "custom_actions": True,
        "max_instructors": -1,  # 무제한
        "max_students": -1,  # 무제한
        "features": ["전체 동작", "커스텀 동작 추가", "무제한 강사/학생", "우선 지원"]
    }
}

# ==================== 다국어 지원 ====================
# 언어 딕셔너리
TRANSLATIONS = {
    'ko': {
        # 공통
        'app_title': '춤마루',
        'app_subtitle': '당신 안에 잠든 K-DNA, 지금 깨어나다',
        'btn_home': '🏠 홈',
        'btn_prev': '← 이전',
        'btn_next': '다음',
        'progress': '진행률',
        
        # Journey 단계
        'journey_1_title': 'K-DNA 발견',
        'journey_1_desc': '10개 질문으로 나만의 춤 성향 분석',
        'journey_2_title': '전통 움직임 체험',
        'journey_2_desc': '한국무용 기본동작 12가지 완주',
        'journey_3_title': '5000년 이야기',
        'journey_3_desc': '전통 속에 숨겨진 깊은 철학 탐구',
        'journey_4_title': 'K-DNA 카드 생성',
        'journey_4_desc': '나만의 춤 정체성을 SNS로 공유',
        
        # 랜딩 페이지
        'landing_hero': '5000년 흘러온 움직임이 드디어 내 몸에서 시작된다',
        'landing_desc': '10가지 일상 질문으로 나만의 춤 DNA를 발견하고,<br>세계가 열광하는 K-무브먼트의 진짜 뿌리를 경험하세요',
        'landing_journey': '춤마루 여정',
        'landing_start': '내 K-DNA 깨우기',
        'landing_stats': '이미 2,347명이 자신만의 춤 유전자를 발견했습니다',
        
        # 테스트 페이지
        'question': '질문',
        'select_answer': '답변을 선택해주세요:',
        'dna_forming': '당신만의 K-DNA가 선명해지고 있어요',
        
        # 결과 페이지
        'your_dna': '당신의 춤 DNA',
        'your_traits': '당신의 특징',
        'expert_video': '맞춤 전통무용 시연',
        'start_movement': '이제 움직임으로 깨워보기',
        'share_result': '결과 공유하기',
        
        # 동작 선택 페이지
        'movement_journey': '움직임 여정 시작',
        'movement_subtitle': '한국무용의 숨겨진 DNA를 깨워보세요',
        'basic_actions': '기본 동작',
        'basic_actions_desc': '한국무용의 핵심 미학을 담은 필수 동작들. 5000년 전통의 움직임 언어를 현대적으로 경험해보세요.',
        'expanded_actions': '확장 동작',
        'expanded_actions_desc': '기본기를 응용한 고급 동작들. 더욱 섬세한 표현력을 경험할 수 있습니다.',
        'creative_actions': '창작 동작',
        'creative_actions_desc': '전통을 현대적으로 재해석한 창작 동작들. K-Culture의 미래를 체험해보세요.',
        'start_basic': '기본 동작 시작하기',
        'try_expanded': '확장 동작 체험하기',
        'try_creative': '창작 동작 체험하기',
        'see_story': '📖 5000년 움직임의 비밀 먼저 보기',
        'story_title': '5000년 움직임의 비밀',
        'story_subtitle': '한국무용에 담긴 깊은 철학',
        'view_detail': '자세히 보기',
        'try_now': '이제 직접 체험해보기',
        'seconds': '초',
        'historical_background': '역사적 배경',
        'badge_earned': '배지 획득!',
        'ai_support': 'AI 동작 분석 지원',
        'special_meme': '완주시 특별 밈 생성',
        'expert_video': '전문가 영상 제공',
        'ai_coming': '2026년 6월 AI 분석 지원',
        'press_button_first': '먼저 \'🎬 GIF 생성하기\' 버튼을 눌러주세요',
        
        # 동작 페이지
        'expert_demo': '전문가 시범',
        'your_movement': '당신의 동작',
        'webcam_guide': '웹캠으로 동작을 따라해보세요',
        'action_complete_manual': '동작 완료 (수동)',
        'ai_judgement': '실제 앱에서는 AI가 자동 판정',
        'pose_not_detected': '자세를 인식할 수 없습니다. 전신이 보이도록 해주세요.',
        'all_complete': '🎉 모든 동작을 완료했습니다!',
        'back_to_select': '동작 선택으로 돌아가기',
        
        # 밈 페이지
        'dna_awakened': 'K-DNA 각성 완료!',
        'actions_completed': '개 동작 완료!',
        'awakened_msg': '당신만의 춤 유전자가 깨어났습니다',
        'share_journey': '지금까지의 여정을 공유해보세요',
        'meme_type': '🎨 밈 카드 유형 선택',
        'static_image': '정적 이미지 (PNG)',
        'animated_gif': '움직이는 GIF (2-3초)',
        'select_style': '원하는 스타일을 선택하세요',
        'style_a': '스타일 A: 그라데이션 박스 (상단/하단 텍스트, 가독성 최고)',
        'style_b': '스타일 B: 네온 스타일 (형광 색상, K-pop 감성)',
        'style_c': '스타일 C: 듀얼 톤 (보라+핑크 컬러 필터, 인스타 감성)',
        'style_d': '스타일 D: 미니멀 (심플 깔끔, 좌측 정렬)',
        'download_png': '📱 PNG 다운로드',
        'download_gif': '🎬 GIF 다운로드',
        'generate_gif': '🎬 GIF 생성하기',
        'share_guide': '📤 SNS 공유 가이드',
        'gif_length': 'GIF 길이 (초)',
        'gif_style': 'GIF 스타일',
        'new_dna': '🔄 새로운 DNA 탐험하기',
        'continue_actions': '➡️ 계속 동작 익히기',
        'see_stories': '📖 전통 이야기 보기',
        
        # DNA 타입 이름
        'dna_meme_master': '밈 장인',
        'dna_mood_curator': '무드 큐레이터',
        'dna_perfect_planner': '갓생 플래너',
        'dna_detail_artisan': '디테일 장인',
        'dna_emotional_filter': '감성 필터',
        'dna_human_resonator': '인간 공명기',
        'dna_party_hero': '파티 히어로',
        'dna_fun_exploder': '흥 폭발러',
        
        # 밈 카드 텍스트
        'meme_i_am': '나는',
        'meme_hashtag': '#춤마루 #K_DNA각성',
        
        # 밈 페이지
        'view_dna_result': '🧬 DNA 결과',
        'practice_movement': '💃 동작 연습',
        'meme_format': '밈 형식',
        'static_image': '정적 이미지 (PNG)',
        'animated_gif': '움직이는 GIF (2-3초)',
        'gif_duration': 'GIF 길이',
        'gif_style': 'GIF 스타일',
        'create_gif': '🎬 GIF 생성하기',
        'download_meme': '💾 밈 다운로드',
        'earned_badges': '획득한 배지',
        'badge_name': '배지명',
        'style_gradient': '스타일 A: 그라데이션 박스',
        'style_neon': '스타일 B: 네온 스타일',
        'style_dualtone': '스타일 C: 듀얼 톤',
        'style_minimal': '스타일 D: 미니멀',
        'congrats_title': '🎉 축하합니다!',
        'congrats_complete': '당신은 12가지 기본 동작을 모두 완료했습니다!',
        'congrats_dna': '당신의 K-DNA가 완전히 각성되었습니다.',
        'congrats_share': '밈을 다운로드해서 친구들과 공유해보세요!',
        'success_full': '축하합니다! 한국무용의 12가지 기본 동작을 모두 완주하셨습니다. 당신은 이제 진정한 K-DNA 마스터입니다. 5000년 전통의 움직임이 당신 안에서 살아 숨쉬고 있어요.',
        'success_partial': '잘하고 있어요! 이미 {count}개의 동작을 마스터했습니다. 계속해서 나만의 춤 DNA를 깨워나가고 있어요.',
        
        # DNA 갤러리
        'dna_gallery_title': '🎭 8가지 K-DNA 타입 갤러리',
        'dna_gallery_subtitle': '당신의 춤 성향은 어떤 타입일까요? 8가지 DNA 타입을 모두 만나보세요',
        'all_dna_types': '모든 DNA 타입',
        'explore_all_dna': '🎭 모든 DNA 타입 탐색',
        'other_dna_types': '🔍 다른 DNA 타입도 궁금하신가요?',
        'view_all_gallery': '전체 갤러리 보기',
        'click_to_watch': '클릭하여 영상 보기',
        
        # 전통무용 아카이브
        'traditional_archive_title': '🎬 전통무용 아카이브',
        'traditional_archive_subtitle': '5000년 역사와 함께하는 전통무용 영상 컬렉션',
        'video_section': '영상 섹션',
        'coming_soon': '곧 공개됩니다',
        'archive_desc': '한국무용의 역사와 이야기가 담긴 영상들을 만나보세요',
        
        # 전문가 시스템
        'expert_system': '전문가 시스템',
        'expert_login': '전문가 로그인',
        'expert_signup': '전문가 가입',
        'expert_logout': '로그아웃',
        'expert_name': '이름',
        'expert_bio': '소개',
        'expert_specialty': '전문 분야',
        'expert_email': '이메일',
        'expert_password': '비밀번호',
        'expert_upload_video': '영상 업로드',
        'expert_my_videos': '내 영상',
        'expert_my_profile': '내 프로필',
        'expert_gallery': '전문가 갤러리',
        'expert_ranking': '전문가 랭킹',
        'video_title': '영상 제목',
        'video_description': '영상 설명',
        'video_dna_type': 'DNA 타입',
        'video_tags': '태그 (쉼표로 구분)',
        'upload_success': '영상이 성공적으로 업로드되었습니다!',
        'like': '좋아요',
        'comment': '댓글',
        'rating': '평점',
        'write_comment': '댓글 작성',
        'submit_comment': '댓글 등록',
        'reputation_score': '평판 점수',
        'reputation_level': '평판 레벨',
        'total_videos': '업로드 영상',
        'total_likes': '총 좋아요',
        'total_comments': '총 댓글',
        'view_profile': '프로필 보기',
        'view_video': '영상 보기',
        'no_videos': '아직 업로드된 영상이 없습니다',
        'no_experts': '등록된 전문가가 없습니다',
        'dna_type_gallery': 'DNA 타입별 갤러리',
        
        # B2B 시스템
        'b2b_system': 'B2B 시스템',
        'org_login': '단체 로그인',
        'org_signup': '단체 가입',
        'org_logout': '로그아웃',
        'org_name': '단체명',
        'org_type': '단체 유형',
        'org_address': '주소',
        'org_phone': '전화번호',
        'org_email': '이메일',
        'org_password': '비밀번호',
        'org_manager': '담당자명',
        'subscription_plan': '구독 플랜',
        'subscription_management': '구독 관리',
        'current_plan': '현재 플랜',
        'upgrade_plan': '플랜 업그레이드',
        'instructor_management': '강사 관리',
        'student_management': '학생 관리',
        'add_instructor': '강사 추가',
        'add_student': '학생 추가',
        'instructor_name': '강사명',
        'instructor_email': '강사 이메일',
        'student_name': '학생명',
        'student_email': '학생 이메일',
        'group_name': '그룹명',
        'group_management': '그룹 관리',
        'custom_actions': '커스텀 동작 설정',
        'select_actions': '동작 선택',
        'dashboard': '대시보드',
        'statistics': '통계',
        'progress_tracking': '진행 상황',
        'action_setup': '동작 세트 설정',
        'max_instructors': '최대 강사 수',
        'max_students': '최대 학생 수',
        'available_actions': '사용 가능한 동작',
        'selected_actions': '선택된 동작',
        'save_settings': '설정 저장',
        'org_dashboard': '단체 대시보드',
        'total_instructors': '전체 강사',
        'total_students': '전체 학생',
        'completion_rate': '완료율',
        'view_details': '상세 보기',
    },
    'en': {
        # Common
        'app_title': 'Choomaru',
        'app_subtitle': 'Awaken the K-DNA within you',
        'btn_home': '🏠 Home',
        'btn_prev': '← Back',
        'btn_next': 'Next',
        'progress': 'Progress',
        
        # Journey Steps
        'journey_1_title': 'Discover K-DNA',
        'journey_1_desc': 'Analyze your dance personality through 10 questions',
        'journey_2_title': 'Experience Traditional Movement',
        'journey_2_desc': 'Complete 12 basic Korean dance movements',
        'journey_3_title': '5000 Years of Stories',
        'journey_3_desc': 'Explore deep philosophy hidden in tradition',
        'journey_4_title': 'Create K-DNA Card',
        'journey_4_desc': 'Share your unique dance identity on SNS',
        
        # Landing Page
        'landing_hero': '5000 Years of Movement, Now Starting in Your Body',
        'landing_desc': 'Discover your unique dance DNA through 10 everyday questions,<br>and experience the true roots of K-Movement that the world is passionate about',
        'landing_journey': 'Choomaru Journey',
        'landing_start': 'Awaken My K-DNA',
        'landing_stats': 'Already 2,347 people have discovered their unique dance genes',
        
        # Test Page
        'question': 'Question',
        'select_answer': 'Please select your answer:',
        'dna_forming': 'Your unique K-DNA is becoming clearer',
        
        # Result Page
        'your_dna': 'Your Dance DNA',
        'your_traits': 'Your Characteristics',
        'expert_video': 'Customized Traditional Dance Performance',
        'start_movement': 'Now Awaken Through Movement',
        'share_result': 'Share Results',
        
        # Action Select Page
        'movement_journey': 'Begin Movement Journey',
        'movement_subtitle': 'Awaken the hidden DNA of Korean dance',
        'basic_actions': 'Basic Actions',
        'basic_actions_desc': 'Essential movements containing the core aesthetics of Korean dance. Experience 5000 years of movement language in a modern way.',
        'expanded_actions': 'Expanded Actions',
        'expanded_actions_desc': 'Advanced movements applying the basics. Experience more delicate expressiveness.',
        'creative_actions': 'Creative Actions',
        'creative_actions_desc': 'Creative movements reinterpreting tradition in a modern way. Experience the future of K-Culture.',
        'start_basic': 'Start Basic Actions',
        'try_expanded': 'Try Expanded Actions',
        'try_creative': 'Try Creative Actions',
        'see_story': '📖 Explore 5000 Years of Movement Secrets First',
        'story_title': '5000 Years of Movement Secrets',
        'story_subtitle': 'Deep Philosophy in Korean Dance',
        'view_detail': 'View Details',
        'try_now': 'Experience It Yourself Now',
        'seconds': 'sec',
        'historical_background': 'Historical Background',
        'badge_earned': 'Badge Earned!',
        'ai_support': 'AI motion analysis support',
        'special_meme': 'Special meme upon completion',
        'expert_video': 'Expert video provided',
        'ai_coming': 'AI analysis support coming June 2026',
        'press_button_first': 'Please press the \'🎬 Create GIF\' button first',
        
        # Action Page
        'expert_demo': 'Expert Demonstration',
        'your_movement': 'Your Movement',
        'webcam_guide': 'Follow the movement with your webcam',
        'action_complete_manual': 'Complete Action (Manual)',
        'ai_judgement': 'AI will auto-judge in the actual app',
        'pose_not_detected': 'Cannot detect pose. Please ensure full body is visible.',
        'all_complete': '🎉 All actions completed!',
        'back_to_select': 'Back to Action Selection',
        
        # Meme Page
        'dna_awakened': 'K-DNA Awakening Complete!',
        'actions_completed': ' actions completed!',
        'awakened_msg': 'Your unique dance gene has awakened',
        'share_journey': 'Share your journey so far',
        'meme_type': '🎨 Select Meme Card Type',
        'static_image': 'Static Image (PNG)',
        'animated_gif': 'Animated GIF (2-3 sec)',
        'select_style': 'Select your preferred style',
        'style_a': 'Style A: Gradient Box (Top/Bottom text, Best readability)',
        'style_b': 'Style B: Neon Style (Fluorescent colors, K-pop vibe)',
        'style_c': 'Style C: Dual Tone (Purple+Pink color filter, Instagram vibe)',
        'style_d': 'Style D: Minimal (Simple & clean, Left aligned)',
        'download_png': '📱 Download PNG',
        'download_gif': '🎬 Download GIF',
        'generate_gif': '🎬 Generate GIF',
        'share_guide': '📤 SNS Sharing Guide',
        'gif_length': 'GIF Length (sec)',
        'gif_style': 'GIF Style',
        'new_dna': '🔄 Explore New DNA',
        'continue_actions': '➡️ Continue Learning Actions',
        'see_stories': '📖 View Traditional Stories',
        
        # DNA Type Names
        'dna_meme_master': 'Meme Master',
        'dna_mood_curator': 'Mood Curator',
        'dna_perfect_planner': 'Perfect Planner',
        'dna_detail_artisan': 'Detail Artisan',
        'dna_emotional_filter': 'Emotional Filter',
        'dna_human_resonator': 'Human Resonator',
        'dna_party_hero': 'Party Hero',
        'dna_fun_exploder': 'Fun Exploder',
        
        # Meme Card Text
        'meme_i_am': "I'm a",
        'meme_hashtag': '#Choomaru #K_DNA_Awakening',
        
        # Meme Page
        'view_dna_result': '🧬 DNA Result',
        'practice_movement': '💃 Practice Movement',
        'meme_format': 'Meme Format',
        'static_image': 'Static Image (PNG)',
        'animated_gif': 'Animated GIF (2-3 sec)',
        'gif_duration': 'GIF Duration',
        'gif_style': 'GIF Style',
        'create_gif': '🎬 Create GIF',
        'download_meme': '💾 Download Meme',
        'earned_badges': 'Earned Badges',
        'badge_name': 'Badge Name',
        'style_gradient': 'Style A: Gradient Box',
        'style_neon': 'Style B: Neon',
        'style_dualtone': 'Style C: Dual Tone',
        'style_minimal': 'Style D: Minimal',
        'congrats_title': '🎉 Congratulations!',
        'congrats_complete': 'You have completed all 12 basic movements!',
        'congrats_dna': 'Your K-DNA has been fully awakened.',
        'congrats_share': 'Download your meme and share it with friends!',
        'success_full': 'Congratulations! You have completed all 12 basic Korean dance movements. You are now a true K-DNA master. 5000 years of traditional movement lives and breathes within you.',
        'success_partial': 'Great job! You have already mastered {count} movements. Keep awakening your unique dance DNA.',
        
        # DNA Gallery
        'dna_gallery_title': '🎭 8 K-DNA Types Gallery',
        'dna_gallery_subtitle': 'What is your dance personality? Explore all 8 DNA types',
        'all_dna_types': 'All DNA Types',
        'explore_all_dna': '🎭 Explore All DNA Types',
        'other_dna_types': '🔍 Curious about other DNA types?',
        'view_all_gallery': 'View Full Gallery',
        'click_to_watch': 'Click to watch video',
        
        # Traditional Archive
        'traditional_archive_title': '🎬 Traditional Dance Archive',
        'traditional_archive_subtitle': 'Traditional dance video collection with 5000 years of history',
        'video_section': 'Video Section',
        'coming_soon': 'Coming Soon',
        'archive_desc': 'Discover videos containing the history and stories of Korean dance',
        
        # Expert System
        'expert_system': 'Expert System',
        'expert_login': 'Expert Login',
        'expert_signup': 'Expert Sign Up',
        'expert_logout': 'Logout',
        'expert_name': 'Name',
        'expert_bio': 'Bio',
        'expert_specialty': 'Specialty',
        'expert_email': 'Email',
        'expert_password': 'Password',
        'expert_upload_video': 'Upload Video',
        'expert_my_videos': 'My Videos',
        'expert_my_profile': 'My Profile',
        'expert_gallery': 'Expert Gallery',
        'expert_ranking': 'Expert Ranking',
        'video_title': 'Video Title',
        'video_description': 'Video Description',
        'video_dna_type': 'DNA Type',
        'video_tags': 'Tags (comma separated)',
        'upload_success': 'Video uploaded successfully!',
        'like': 'Like',
        'comment': 'Comment',
        'rating': 'Rating',
        'write_comment': 'Write Comment',
        'submit_comment': 'Submit Comment',
        'reputation_score': 'Reputation Score',
        'reputation_level': 'Reputation Level',
        'total_videos': 'Total Videos',
        'total_likes': 'Total Likes',
        'total_comments': 'Total Comments',
        'view_profile': 'View Profile',
        'view_video': 'View Video',
        'no_videos': 'No videos uploaded yet',
        'no_experts': 'No experts registered',
        'dna_type_gallery': 'DNA Type Gallery',
        
        # B2B System
        'b2b_system': 'B2B System',
        'org_login': 'Organization Login',
        'org_signup': 'Organization Sign Up',
        'org_logout': 'Logout',
        'org_name': 'Organization Name',
        'org_type': 'Organization Type',
        'org_address': 'Address',
        'org_phone': 'Phone',
        'org_email': 'Email',
        'org_password': 'Password',
        'org_manager': 'Manager Name',
        'subscription_plan': 'Subscription Plan',
        'subscription_management': 'Subscription Management',
        'current_plan': 'Current Plan',
        'upgrade_plan': 'Upgrade Plan',
        'instructor_management': 'Instructor Management',
        'student_management': 'Student Management',
        'add_instructor': 'Add Instructor',
        'add_student': 'Add Student',
        'instructor_name': 'Instructor Name',
        'instructor_email': 'Instructor Email',
        'student_name': 'Student Name',
        'student_email': 'Student Email',
        'group_name': 'Group Name',
        'group_management': 'Group Management',
        'custom_actions': 'Custom Actions Setup',
        'select_actions': 'Select Actions',
        'dashboard': 'Dashboard',
        'statistics': 'Statistics',
        'progress_tracking': 'Progress Tracking',
        'action_setup': 'Action Set Setup',
        'max_instructors': 'Max Instructors',
        'max_students': 'Max Students',
        'available_actions': 'Available Actions',
        'selected_actions': 'Selected Actions',
        'save_settings': 'Save Settings',
        'org_dashboard': 'Organization Dashboard',
        'total_instructors': 'Total Instructors',
        'total_students': 'Total Students',
        'completion_rate': 'Completion Rate',
        'view_details': 'View Details',
    }
}

# 번역 헬퍼 함수
def t(key, lang=None):
    """언어에 맞는 번역 텍스트 반환"""
    if lang is None:
        lang = st.session_state.get('language', 'ko')
    return TRANSLATIONS.get(lang, {}).get(key, key)

# CSS 스타일링
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stButton > button {
        width: 100%;
        border-radius: 20px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    .dna-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    .action-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }
    .success-message {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .journey-step {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
def init_session_state():
    if 'language' not in st.session_state:
        st.session_state.language = 'ko'  # 기본 언어: 한국어
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 'landing'
    if 'answers' not in st.session_state:
        st.session_state.answers = []
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'dna_result' not in st.session_state:
        st.session_state.dna_result = None
    if 'completed_actions' not in st.session_state:
        st.session_state.completed_actions = []
    if 'current_action' not in st.session_state:
        st.session_state.current_action = 0
    if 'current_expanded_action' not in st.session_state:
        st.session_state.current_expanded_action = 0
    if 'current_creative_action' not in st.session_state:
        st.session_state.current_creative_action = 0
    if 'current_story' not in st.session_state:
        st.session_state.current_story = 0
    if 'badges' not in st.session_state:
        st.session_state.badges = []
    if 'consecutive_success' not in st.session_state:
        st.session_state.consecutive_success = 0
    if 'expert_logged_in' not in st.session_state:
        st.session_state.expert_logged_in = False
    if 'expert_id' not in st.session_state:
        st.session_state.expert_id = None
    if 'viewing_expert_id' not in st.session_state:
        st.session_state.viewing_expert_id = None
    if 'viewing_video_id' not in st.session_state:
        st.session_state.viewing_video_id = None
    # B2B 관련 세션 상태
    if 'org_logged_in' not in st.session_state:
        st.session_state.org_logged_in = False
    if 'org_id' not in st.session_state:
        st.session_state.org_id = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None  # 'admin', 'instructor', 'student'
    if 'instructor_id' not in st.session_state:
        st.session_state.instructor_id = None
    if 'student_id' not in st.session_state:
        st.session_state.student_id = None

# 10개 질문 데이터 (한국어)
questions_ko = [
    {
        "id": 1,
        "text": "새로운 여행지를 탐험할 때, 당신은 어떤 사람인가요?",
        "options": {
            "A": "아무도 모르는 숨은 장소를 찾아 나서는 탐험가",
            "B": "이동 경로와 맛집까지 완벽하게 계획하는 플래너", 
            "C": "풍경 하나하나에 담긴 스토리를 상상하는 낭만가",
            "D": "현지 축제나 파티에 무작정 참여하는 분위기 메이커"
        }
    },
    {
        "id": 2,
        "text": "예상치 못한 문제가 발생했을 때, 당신의 반응은?",
        "options": {
            "A": "남들이 생각하지 못한 독창적 아이디어로 해결한다",
            "B": "가장 논리적이고 효율적인 해결책을 찾는다",
            "C": "문제의 원인과 과정을 되짚어보며 자신을 돌아본다", 
            "D": "'다 같이 힘내자!'고 외치며 긍정 에너지를 불어넣는다"
        }
    },
    {
        "id": 3,
        "text": "쇼핑을 할 때 당신의 취향은?",
        "options": {
            "A": "유행에 휩쓸리지 않고 나만의 독특한 스타일을 찾는다",
            "B": "기능성과 실용성을 꼼꼼히 따져보고 구매한다",
            "C": "이 물건이 나에게 어떤 의미를 줄지 상상하며 쇼핑한다",
            "D": "화려한 색상과 과감한 디자인으로 시선을 사로잡는다"
        }
    },
    {
        "id": 4,
        "text": "당신이 가장 중요하게 생각하는 것은?",
        "options": {
            "A": "아무도 가보지 않은 길을 개척하는 자유로움",
            "B": "흔들림 없이 내 삶을 완벽하게 통제하는 것",
            "C": "타인과 깊은 감정을 교류하고 공감하는 것",
            "D": "주변 사람들에게 활기와 긍정적 에너지를 주는 것"
        }
    },
    {
        "id": 5,
        "text": "휴대폰 앨범에 가장 많은 사진은?",
        "options": {
            "A": "직접 찍은 독특한 풍경이나 예술 작품",
            "B": "정리된 계획표나 중요한 정보 캡처",
            "C": "소중한 사람들과의 추억이 담긴 사진",
            "D": "파티나 콘서트 등 흥겨운 현장 분위기"
        }
    },
    {
        "id": 6,
        "text": "고민을 털어놓는 친구에게 당신의 반응은?",
        "options": {
            "A": "'나라면 이렇게 해볼 것 같아'라며 새로운 해결책 제안",
            "B": "'왜 그런 문제가 생겼지?'라며 원인 분석과 논리적 조언",
            "C": "'얼마나 힘들었을까'라며 공감하고 마음을 어루만짐",
            "D": "'일단 맛있는 거 먹고 힘내자!'라며 분위기 전환"
        }
    },
    {
        "id": 7,
        "text": "좋아하는 SNS 콘텐츠는?",
        "options": {
            "A": "창의적인 아이디어가 돋보이는 숏폼 챌린지",
            "B": "전문가가 정확한 정보를 알려주는 콘텐츠",
            "C": "감성적인 분위기와 스토리텔링이 있는 다큐",
            "D": "활발한 소통과 재미있는 에피소드의 라이브 방송"
        }
    },
    {
        "id": 8,
        "text": "혼자 있을 때 주로 하는 것은?",
        "options": {
            "A": "그림을 그리거나 글을 쓰는 등 창작 활동",
            "B": "평소 미뤄뒀던 일들을 체계적으로 정리",
            "C": "영화나 책을 보며 주인공의 감정에 깊이 몰입",
            "D": "신나는 음악을 들으며 아무 생각 없이 몸을 움직임"
        }
    },
    {
        "id": 9,
        "text": "옷장에 가장 많은 스타일은?",
        "options": {
            "A": "남들이 잘 입지 않는 독특하고 개성 있는 옷",
            "B": "깔끔하고 단정하며 어디에나 어울리는 기본 아이템",
            "C": "부드러운 소재와 편안한 핏으로 감성을 자극하는 옷",
            "D": "밝고 화사한 컬러로 에너지가 넘치는 옷"
        }
    },
    {
        "id": 10,
        "text": "당신에게 완벽한 하루란?",
        "options": {
            "A": "머릿속에 떠오른 아이디어를 마음껏 펼친 하루",
            "B": "계획한 일을 모두 완벽하게 해낸 하루",
            "C": "소중한 사람들과 깊은 대화를 나눈 하루",
            "D": "온몸으로 즐기며 스트레스를 날려버린 하루"
        }
    }
]

# 10개 질문 데이터 (영어)
questions_en = [
    {
        "id": 1,
        "text": "When exploring a new travel destination, what kind of person are you?",
        "options": {
            "A": "An explorer seeking hidden places no one knows about",
            "B": "A planner perfectly organizing routes and restaurants",
            "C": "A romantic imagining stories behind every scenery",
            "D": "A mood-maker spontaneously joining local festivals or parties"
        }
    },
    {
        "id": 2,
        "text": "When an unexpected problem occurs, your reaction is?",
        "options": {
            "A": "Solve it with creative ideas others haven't thought of",
            "B": "Find the most logical and efficient solution",
            "C": "Reflect on the cause and process while looking inward",
            "D": "Shout 'Let's all do our best!' and inject positive energy"
        }
    },
    {
        "id": 3,
        "text": "What's your taste when shopping?",
        "options": {
            "A": "Find your unique style without following trends",
            "B": "Carefully check functionality and practicality before buying",
            "C": "Shop while imagining what meaning this item will bring",
            "D": "Catch attention with vibrant colors and bold designs"
        }
    },
    {
        "id": 4,
        "text": "What do you value most?",
        "options": {
            "A": "Freedom to pioneer paths no one has taken",
            "B": "Perfectly controlling my life without wavering",
            "C": "Exchanging deep emotions and empathizing with others",
            "D": "Giving vitality and positive energy to people around me"
        }
    },
    {
        "id": 5,
        "text": "What photos fill your phone album the most?",
        "options": {
            "A": "Unique landscapes or artworks I've taken myself",
            "B": "Organized schedules or important information captures",
            "C": "Photos filled with memories of precious people",
            "D": "Exciting atmosphere from parties or concerts"
        }
    },
    {
        "id": 6,
        "text": "When a friend shares their worries, your reaction is?",
        "options": {
            "A": "'If it were me, I'd try this' - suggesting new solutions",
            "B": "'Why did this problem occur?' - analyzing causes and giving logical advice",
            "C": "'How hard it must have been' - empathizing and comforting",
            "D": "'Let's eat something delicious and cheer up!' - changing the mood"
        }
    },
    {
        "id": 7,
        "text": "What SNS content do you prefer?",
        "options": {
            "A": "Short-form challenges with creative ideas",
            "B": "Content where experts provide accurate information",
            "C": "Documentaries with emotional atmosphere and storytelling",
            "D": "Live broadcasts with active communication and fun episodes"
        }
    },
    {
        "id": 8,
        "text": "What do you mainly do when alone?",
        "options": {
            "A": "Creative activities like drawing or writing",
            "B": "Systematically organizing postponed tasks",
            "C": "Deeply immersing in characters' emotions through movies or books",
            "D": "Moving my body freely while listening to exciting music"
        }
    },
    {
        "id": 9,
        "text": "What style fills your wardrobe the most?",
        "options": {
            "A": "Unique and individual clothes people don't wear often",
            "B": "Clean and neat basic items that go anywhere",
            "C": "Clothes with soft materials and comfortable fit that touch emotions",
            "D": "Bright and colorful clothes overflowing with energy"
        }
    },
    {
        "id": 10,
        "text": "What's a perfect day for you?",
        "options": {
            "A": "A day freely expressing ideas that came to mind",
            "B": "A day perfectly accomplishing all planned tasks",
            "C": "A day having deep conversations with precious people",
            "D": "A day enjoying with my whole body and blowing away stress"
        }
    }
]

# 언어에 따라 질문 선택
def get_questions(lang='ko'):
    return questions_ko if lang == 'ko' else questions_en

questions = questions_ko  # 기본값

# 8가지 DNA 타입 정의 (한국어)
dna_types_ko = {
    "밈 장인": {
        "emoji": "🎭",
        "title": "Meme Master",
        "description": "일상에서 영감을 받아 춤으로 즉흥적인 콘텐츠를 만들어내는 당신. 기발한 아이디어와 엉뚱한 동작 조합으로 '이게 되네?' 싶은 춤을 창조합니다.",
        "characteristics": ["창의적 발상", "즉흥성", "유머 감각", "콘텐츠 크리에이터"],
        "color": "#FF6B35",
        "video_file": "dna-types/meme-master.mp4"
    },
    "무드 큐레이터": {
        "emoji": "✨",
        "title": "Mood Curator", 
        "description": "분위기 좋은 음악이 흘러나오면 곧바로 자신만의 감성을 담은 춤을 추는 당신. 춤의 완성도보다는 그 순간의 느낌과 분위기를 소중히 여깁니다.",
        "characteristics": ["감성적", "분위기 메이커", "예술적 감각", "순간 포착"],
        "color": "#A8E6CF",
        "video_file": "dna-types/mood-curator.mp4"
    },
    "갓생 플래너": {
        "emoji": "📋",
        "title": "Perfect Planner",
        "description": "춤을 추기 전에 모든 동작을 머릿속으로 시뮬레이션하고 완벽한 각도와 동선을 계산하는 당신. '갓생'을 살 듯 춤도 빈틈없이 계획적으로 춥니다.",
        "characteristics": ["완벽주의", "체계적", "목표 지향", "효율성"],
        "color": "#4ECDC4",
        "video_file": "dna-types/perfect-planner.mp4"
    },
    "디테일 장인": {
        "emoji": "🔍",
        "title": "Detail Artisan",
        "description": "남들이 놓치는 미세한 손끝의 떨림이나 발끝의 각도까지 신경 쓰는 완벽주의자. 작은 디테일로 춤에 깊이를 더하고 보는 사람에게 감동을 선사합니다.",
        "characteristics": ["섬세함", "정밀성", "장인정신", "품질 추구"],
        "color": "#B8860B",
        "video_file": "dna-types/detail-artisan.mp4"
    },
    "감성 필터": {
        "emoji": "💫",
        "title": "Emotional Filter",
        "description": "기쁨, 슬픔, 분노 등 모든 감정을 춤으로 표현하는 당신. 춤이 곧 감정 일기이며, 타인과 감정을 교류하는 통로라고 생각합니다.",
        "characteristics": ["감정 표현", "내면 탐구", "예술성", "치유력"],
        "color": "#DDA0DD",
        "video_file": "dna-types/emotional-filter.mp4"
    },
    "인간 공명기": {
        "emoji": "🤝",
        "title": "Human Resonator",
        "description": "타인의 감정이나 분위기에 민감하게 반응하고, 춤을 통해 그 감정에 공감하는 당신. 모두와 함께 춤을 추며 소통하는 것에 가장 큰 즐거움을 느낍니다.",
        "characteristics": ["공감 능력", "소통", "화합", "감정 동조"],
        "color": "#FF69B4",
        "video_file": "dna-types/human-resonator.mp4"
    },
    "파티 히어로": {
        "emoji": "🎉",
        "title": "Party Hero",
        "description": "춤추는 순간 주위 사람들의 시선을 사로잡는 분위기 메이커. 신나는 음악과 함께 모든 에너지를 쏟아내며, 춤으로 파티의 열기를 최고조로 끌어올립니다.",
        "characteristics": ["리더십", "에너지", "사교성", "무대 장악력"],
        "color": "#FFD700",
        "video_file": "dna-types/party-hero.mp4"
    },
    "흥 폭발러": {
        "emoji": "🚀",
        "title": "Fun Exploder",
        "description": "어디서든 춤을 통해 긍정적인 에너지를 발산하는 당신. 춤을 배우는 것보다 그저 신나게 즐기는 것에 더 큰 의미를 두는 유형입니다.",
        "characteristics": ["자유분방", "열정", "긍정성", "에너지 전달"],
        "color": "#FF4500",
        "video_file": "dna-types/fun-explorer.mp4"
    }
}

# 8가지 DNA 타입 정의 (영어)
dna_types_en = {
    "Meme Master": {
        "emoji": "🎭",
        "title": "Meme Master",
        "description": "Inspired by daily life, you create spontaneous dance content. With brilliant ideas and quirky movement combinations, you create dances that make people think 'This actually works?'",
        "characteristics": ["Creative Thinking", "Spontaneity", "Sense of Humor", "Content Creator"],
        "color": "#FF6B35",
        "video_file": "dna-types/meme-master.mp4"
    },
    "Mood Curator": {
        "emoji": "✨",
        "title": "Mood Curator",
        "description": "When good music plays, you immediately dance with your own sensibility. You value the feeling and atmosphere of the moment more than dance perfection.",
        "characteristics": ["Emotional", "Mood Maker", "Artistic Sense", "Moment Capture"],
        "color": "#A8E6CF",
        "video_file": "dna-types/mood-curator.mp4"
    },
    "Perfect Planner": {
        "emoji": "📋",
        "title": "Perfect Planner",
        "description": "Before dancing, you simulate every movement in your mind and calculate perfect angles and movement lines. Like living a 'god-life', you dance with thorough planning.",
        "characteristics": ["Perfectionism", "Systematic", "Goal-Oriented", "Efficiency"],
        "color": "#4ECDC4",
        "video_file": "dna-types/perfect-planner.mp4"
    },
    "Detail Artisan": {
        "emoji": "🔍",
        "title": "Detail Artisan",
        "description": "A perfectionist who pays attention to subtle fingertip trembles and toe angles that others miss. You add depth to dance with small details and move the audience.",
        "characteristics": ["Delicacy", "Precision", "Craftsmanship", "Quality Pursuit"],
        "color": "#B8860B",
        "video_file": "dna-types/detail-artisan.mp4"
    },
    "Emotional Filter": {
        "emoji": "💫",
        "title": "Emotional Filter",
        "description": "You express all emotions through dance - joy, sadness, anger. Dance is your emotional diary and a channel to exchange emotions with others.",
        "characteristics": ["Emotional Expression", "Inner Exploration", "Artistry", "Healing Power"],
        "color": "#DDA0DD",
        "video_file": "dna-types/emotional-filter.mp4"
    },
    "Human Resonator": {
        "emoji": "🤝",
        "title": "Human Resonator",
        "description": "Sensitive to others' emotions and atmosphere, you empathize through dance. You find greatest joy in dancing and communicating with everyone.",
        "characteristics": ["Empathy", "Communication", "Harmony", "Emotional Sync"],
        "color": "#FF69B4",
        "video_file": "dna-types/human-resonator.mp4"
    },
    "Party Hero": {
        "emoji": "🎉",
        "title": "Party Hero",
        "description": "A mood-maker who captivates people's attention when dancing. With exciting music, you pour out all energy and raise the party's heat to its peak through dance.",
        "characteristics": ["Leadership", "Energy", "Sociability", "Stage Presence"],
        "color": "#FFD700",
        "video_file": "dna-types/party-hero.mp4"
    },
    "Fun Exploder": {
        "emoji": "🚀",
        "title": "Fun Exploder",
        "description": "You radiate positive energy through dance anywhere. You find more meaning in simply enjoying energetically than learning dance.",
        "characteristics": ["Free-spirited", "Passion", "Positivity", "Energy Transfer"],
        "color": "#FF4500",
        "video_file": "dna-types/fun-explorer.mp4"
    }
}

# DNA 타입 이름 매핑 (한국어 -> 영어)
dna_type_mapping = {
    "밈 장인": "Meme Master",
    "무드 큐레이터": "Mood Curator",
    "갓생 플래너": "Perfect Planner",
    "디테일 장인": "Detail Artisan",
    "감성 필터": "Emotional Filter",
    "인간 공명기": "Human Resonator",
    "파티 히어로": "Party Hero",
    "흥 폭발러": "Fun Exploder"
}

# 언어에 따라 DNA 타입 데이터 선택
def get_dna_types(lang='ko'):
    return dna_types_ko if lang == 'ko' else dna_types_en

def get_dna_type_name(korean_name, lang='ko'):
    """한국어 DNA 타입 이름을 현재 언어로 변환"""
    if lang == 'ko':
        return korean_name
    else:
        return dna_type_mapping.get(korean_name, korean_name)

dna_types = dna_types_ko  # 기본값

# 12개 기본 동작 정의 (한국어)
basic_actions_ko = [
    {
        "name": "좌우새",
        "description": "어깨와 머리를 좌우로 부드럽게 흔드는 머릿짓",
        "story_card": "작은 흔들림이 파동을 만든다. 내 몸이 파도처럼 흔들리며 춤의 첫 숨결을 열어준다.",
        "historical_note": "조선 정재에서 '좌우새'는 새가 머리를 좌우로 흔드는 모습을 형상화한 동작입니다.",
        "video_file": "basic-actions/left-right-flow.mp4",
        "detail_videos": [
            {"part": "어깨 움직임", "video": None},
            {"part": "머리 각도", "video": None},
            {"part": "시선 처리", "video": None}
        ]
    },
    {
        "name": "감기", 
        "description": "팔을 원형으로 휘감으며 연결하는 동작",
        "story_card": "팔끝이 그리는 원은 흐름의 다리다. 시작과 끝이 이어지며 끊김 없는 리듬이 완성된다.",
        "historical_note": "원형의 움직임은 동양 철학의 순환 사상을 담고 있으며, 궁중무에서 자주 사용되었습니다.",
        "video_file": "basic-actions/arm-circle.mp4",
        "detail_videos": [
            {"part": "팔꿈치 궤적", "video": None},
            {"part": "손목 연결", "video": None}
        ]
    },
    {
        "name": "손목감기",
        "description": "손목을 안팎으로 원을 그리며 감아 올리는 동작", 
        "story_card": "작은 손목에서 큰 에너지가 피어난다. 미세한 움직임이 춤 전체의 결을 바꾼다.",
        "historical_note": "손목의 미세한 움직임은 한국무용의 섬세함을 보여주는 대표적 요소입니다.",
        "video_file": "basic-actions/wrist-circle.mp4",
        "detail_videos": [
            {"part": "손목 각도", "video": None},
            {"part": "손가락 방향", "video": None},
            {"part": "팔 고정", "video": None}
        ]
    },
    {
        "name": "머리감기",
        "description": "머리를 원으로 부드럽게 돌리는 동작",
        "story_card": "머리의 회전은 시야와 생각을 확장시킨다. 원이 커질수록 마음도 더 넓어진다.",
        "historical_note": "머리감기는 자연의 흐름에 몸을 맡기는 한국무용의 핵심 철학을 담고 있습니다.",
        "video_file": "basic-actions/head-circle.mp4",
        "detail_videos": [
            {"part": "목 움직임", "video": None},
            {"part": "시선 이동", "video": None}
        ]
    },
    {
        "name": "바람불기",
        "description": "팔과 손을 바람결처럼 흔드는 동작",
        "story_card": "바람처럼 가볍게, 그러나 보이지 않게 강하게. 손끝에서 세상과 연결되는 길이 열린다.",
        "historical_note": "자연의 바람을 형상화한 이 동작은 인간과 자연의 조화를 추구하는 우리 문화를 보여줍니다.",
        "video_file": "basic-actions/wind-blowing.mp4",
        "detail_videos": [
            {"part": "손가락 흔들림", "video": None},
            {"part": "팔 진폭", "video": None},
            {"part": "어깨 고정", "video": None}
        ]
    },
    {
        "name": "손바닥 뒤집기", 
        "description": "손바닥을 위아래로 간단히 뒤집는 동작",
        "story_card": "뒤집는 순간 세상이 달라진다. 위와 아래가 바뀌며 삶의 관점도 새로워진다.",
        "historical_note": "음양의 전환을 의미하는 동작으로, 변화와 조화의 철학이 담겨 있습니다.",
        "video_file": "basic-actions/palm-flip.mp4",
        "detail_videos": [
            {"part": "손목 회전", "video": None},
            {"part": "손가락 펴기", "video": None}
        ]
    },
    {
        "name": "홑디딤",
        "description": "한 발을 내디으며 중심을 옮기는 기본 걸음",
        "story_card": "단순한 한 발, 그러나 모든 시작은 여기서 열린다. 땅을 딛는 순간 춤은 살아난다.",
        "historical_note": "한국무용의 모든 이동의 기본이 되는 걸음으로, 안정감과 우아함을 동시에 표현합니다.",
        "video_file": "basic-actions/single-step.mp4",
        "detail_videos": [
            {"part": "발 디딤", "video": None},
            {"part": "무게 이동", "video": None},
            {"part": "상체 균형", "video": None}
        ]
    },
    {
        "name": "잔걸음",
        "description": "작게 바닥을 누르거나 살짝 들어 올리는 걸음",
        "story_card": "잔걸음은 땅과의 대화다. 무게를 맡기거나 들어 올리며 삶의 무게와 가벼움을 동시에 담는다.",
        "historical_note": "조심스럽고 절제된 움직임으로 한국 여성의 단아함을 표현하는 대표적 걸음입니다.",
        "video_file": "basic-actions/small-steps.mp4",
        "detail_videos": [
            {"part": "발끝 높이", "video": None},
            {"part": "걸음 간격", "video": None}
        ]
    },
    {
        "name": "굴신",
        "description": "무릎과 몸통을 굽혔다 펴는 동작", 
        "story_card": "굽힘과 펼침 속에 인간의 태도가 담긴다. 겸손히 낮추고 당당히 일어서는 몸짓.",
        "historical_note": "유교 문화의 예의범절이 춤으로 승화된 동작으로, 정중동의 미학을 보여줍니다.",
        "video_file": "basic-actions/bend-stretch.mp4",
        "detail_videos": [
            {"part": "무릎 각도", "video": None},
            {"part": "상체 굽힘", "video": None},
            {"part": "시선 처리", "video": None}
        ]
    },
    {
        "name": "한다리들기",
        "description": "한쪽 다리를 들어 균형을 잡는 동작",
        "story_card": "흔들림 속에서도 균형을 찾아야 한다. 한다리들기는 중심을 지키는 힘을 길러준다.",
        "historical_note": "학이 한 발로 서 있는 모습을 형상화한 동작으로, 고고한 품격을 의미합니다.",
        "video_file": "basic-actions/one-leg-lift.mp4",
        "detail_videos": [
            {"part": "지지발 균형", "video": None},
            {"part": "들린 다리 각도", "video": None},
            {"part": "상체 중심", "video": None}
        ]
    },
    {
        "name": "호흡",
        "description": "숨의 길이를 달리해 동작을 이어주는 원리",
        "story_card": "호흡은 춤의 보이지 않는 심장이다. 긴 호흡은 여유를, 짧은 호흡은 순간을, 겹호흡은 깊이를 만들어낸다.",
        "historical_note": "한국무용에서 호흡은 동작의 생명력을 불어넣는 핵심 요소입니다.",
        "video_file": "basic-actions/breathing.mp4",
        "detail_videos": [
            {"part": "복식 호흡", "video": None},
            {"part": "상체 움직임", "video": None}
        ]
    },
    {
        "name": "궁채",
        "description": "팔을 크게 원으로 굽혀 돌리는 동작",
        "story_card": "원은 끝없는 순환을 상징한다. 팔이 그린 원 안에 세상의 흐름이 담긴다.",
        "historical_note": "큰 원을 그리는 동작으로 우주의 순환과 생명의 흐름을 표현합니다.",
        "video_file": "basic-actions/large-circle.mp4",
        "detail_videos": [
            {"part": "팔 궤적", "video": None},
            {"part": "어깨 회전", "video": None},
            {"part": "손끝 방향", "video": None}
        ]
    }
]

# 12개 기본 동작 정의 (영어)
basic_actions_en = [
    {
        "name": "Left-Right Flow",
        "description": "Gently swaying shoulders and head from side to side",
        "story_card": "Small movements create waves. My body sways like the ocean, opening the first breath of dance.",
        "historical_note": "In Joseon court dance, 'Jwau-sae' represents the movement of a bird shaking its head left and right.",
        "video_file": "basic-actions/left-right-flow.mp4",
        "detail_videos": [
            {"part": "Shoulder movement", "video": None},
            {"part": "Head angle", "video": None},
            {"part": "Eye direction", "video": None}
        ]
    },
    {
        "name": "Arm Circle",
        "description": "Wrapping and connecting arms in circular motion",
        "story_card": "The circle drawn by arm tips is a bridge of flow. Beginning and end connect to complete an unbroken rhythm.",
        "historical_note": "Circular movements embody Eastern philosophy's concept of circulation and were frequently used in court dances.",
        "video_file": "basic-actions/arm-circle.mp4",
        "detail_videos": [
            {"part": "Elbow trajectory", "video": None},
            {"part": "Wrist connection", "video": None}
        ]
    },
    {
        "name": "Wrist Circle",
        "description": "Circling wrists inward and outward",
        "story_card": "Great energy blooms from small wrists. Subtle movements change the texture of the entire dance.",
        "historical_note": "The delicate wrist movement is a signature element showing Korean dance's refinement.",
        "video_file": "basic-actions/wrist-circle.mp4",
        "detail_videos": [
            {"part": "Wrist angle", "video": None},
            {"part": "Finger direction", "video": None},
            {"part": "Arm position", "video": None}
        ]
    },
    {
        "name": "Head Circle",
        "description": "Smoothly rotating the head in a circle",
        "story_card": "Head rotation expands vision and thought. As the circle grows, so does the heart.",
        "historical_note": "Head circles embody Korean dance's core philosophy of entrusting the body to nature's flow.",
        "video_file": "basic-actions/head-circle.mp4",
        "detail_videos": [
            {"part": "Neck movement", "video": None},
            {"part": "Eye tracking", "video": None}
        ]
    },
    {
        "name": "Wind Blowing",
        "description": "Waving arms and hands like a breeze",
        "story_card": "Light as wind, yet invisibly strong. From fingertips opens a path connecting to the world.",
        "historical_note": "This movement visualizing nature's wind shows our culture's pursuit of harmony between human and nature.",
        "video_file": "basic-actions/wind-blowing.mp4",
        "detail_videos": [
            {"part": "Finger wave", "video": None},
            {"part": "Arm amplitude", "video": None},
            {"part": "Shoulder fixation", "video": None}
        ]
    },
    {
        "name": "Palm Flip",
        "description": "Simply flipping palms up and down",
        "story_card": "The moment of flipping changes the world. As up and down switch, life's perspective renews.",
        "historical_note": "A movement representing the transition of yin and yang, containing the philosophy of change and harmony.",
        "video_file": "basic-actions/palm-flip.mp4",
        "detail_videos": [
            {"part": "Wrist rotation", "video": None},
            {"part": "Finger extension", "video": None}
        ]
    },
    {
        "name": "Single Step",
        "description": "Basic walk stepping forward and shifting weight",
        "story_card": "A simple step, yet all beginnings open here. The moment feet touch ground, dance comes alive.",
        "historical_note": "The foundation of all movement in Korean dance, expressing both stability and elegance.",
        "video_file": "basic-actions/single-step.mp4",
        "detail_videos": [
            {"part": "Foot placement", "video": None},
            {"part": "Weight shift", "video": None},
            {"part": "Upper body balance", "video": None}
        ]
    },
    {
        "name": "Small Steps",
        "description": "Small steps pressing or slightly lifting from the floor",
        "story_card": "Small steps are dialogue with the ground. Committing weight or lifting captures both life's heaviness and lightness.",
        "historical_note": "A representative step expressing Korean women's grace through careful and restrained movement.",
        "video_file": "basic-actions/small-steps.mp4",
        "detail_videos": [
            {"part": "Toe height", "video": None},
            {"part": "Step spacing", "video": None}
        ]
    },
    {
        "name": "Bend-Stretch",
        "description": "Bending and extending knees and torso",
        "story_card": "Human attitude is contained in bending and extending. Humbly lowering and confidently rising.",
        "historical_note": "A movement where Confucian etiquette is sublimated into dance, showing the aesthetics of stillness in motion.",
        "video_file": "basic-actions/bend-stretch.mp4",
        "detail_videos": [
            {"part": "Knee angle", "video": None},
            {"part": "Torso bend", "video": None},
            {"part": "Eye focus", "video": None}
        ]
    },
    {
        "name": "One Leg Lift",
        "description": "Lifting one leg to maintain balance",
        "story_card": "Must find balance even in wavering. One leg lift develops the power to maintain center.",
        "historical_note": "Visualizing a crane standing on one foot, symbolizing noble dignity.",
        "video_file": "basic-actions/one-leg-lift.mp4",
        "detail_videos": [
            {"part": "Standing leg balance", "video": None},
            {"part": "Lifted leg angle", "video": None},
            {"part": "Upper body center", "video": None}
        ]
    },
    {
        "name": "Breathing",
        "description": "Principle connecting movements with varying breath lengths",
        "story_card": "Breath is dance's invisible heart. Long breath creates leisure, short breath captures moments, layered breath creates depth.",
        "historical_note": "In Korean dance, breathing is the core element infusing vitality into movements.",
        "video_file": "basic-actions/breathing.mp4",
        "detail_videos": [
            {"part": "Diaphragm breathing", "video": None},
            {"part": "Upper body movement", "video": None}
        ]
    },
    {
        "name": "Large Circle",
        "description": "Bending and rotating arms in a large circle",
        "story_card": "The circle symbolizes endless circulation. Within the circle drawn by arms, the world's flow is contained.",
        "historical_note": "Drawing a large circle expresses the universe's circulation and life's flow.",
        "video_file": "basic-actions/large-circle.mp4",
        "detail_videos": [
            {"part": "Arm trajectory", "video": None},
            {"part": "Shoulder rotation", "video": None},
            {"part": "Fingertip direction", "video": None}
        ]
    }
]

# 언어에 따라 기본 동작 선택
def get_basic_actions(lang='ko'):
    return basic_actions_ko if lang == 'ko' else basic_actions_en

basic_actions = basic_actions_ko  # 기본값

# 확장 동작 (6개) - 한국어
expanded_actions_ko = [
    {
        "name": "겹디딤",
        "description": "두 발을 교차하며 밟는 걸음",
        "story_card": "발과 발이 교차하며 만드는 리듬. 단순한 걸음이 겹치면서 복잡한 아름다움을 만들어낸다.",
        "historical_note": "궁중무에서 정교한 발놀림을 표현하기 위해 발달한 동작으로, 섬세한 균형감을 요구합니다.",
        "video_file": "expanded-actions/double-steps.mp4",
        "detail_videos": [
            {"part": "발 교차", "video": None},
            {"part": "무게 이동", "video": None},
            {"part": "발목 각도", "video": None},
            {"part": "상체 균형", "video": None}
        ]
    },
    {
        "name": "제자리돌기", 
        "description": "같은 자리에 서서 회전하는 동작",
        "story_card": "중심을 지키며 세상을 바라보는 시선이 바뀐다. 내 자리에서 우주를 감싸 안는 회전.",
        "historical_note": "한국무용의 '돌기'는 회전하면서도 중심을 잃지 않는 철학을 담고 있습니다.",
        "video_file": "expanded-actions/spin-in-place.mp4",
        "detail_videos": [
            {"part": "발 피벗", "video": None},
            {"part": "중심축", "video": None},
            {"part": "시선 스포팅", "video": None}
        ]
    },
    {
        "name": "이동하면서돌기",
        "description": "걸음을 옮기며 회전하는 동작", 
        "story_card": "공간을 가로지르며 회전하는 몸. 이동과 회전이 하나 되어 흐름을 만들어낸다.",
        "historical_note": "공간 이동과 회전을 동시에 수행하는 고난도 기술로, 춤의 역동성을 극대화합니다.",
        "video_file": "expanded-actions/moving-spin.mp4",
        "detail_videos": [
            {"part": "발 이동 경로", "video": None},
            {"part": "회전 타이밍", "video": None},
            {"part": "팔 사용", "video": None},
            {"part": "시선 방향", "video": None},
            {"part": "공간 활용", "video": None}
        ]
    },
    {
        "name": "점프하면서돌기",
        "description": "뛰어오르며 회전하는 동작",
        "story_card": "중력을 거스르는 순간, 공중에서 몸이 회전한다. 하늘과 땅 사이에서 자유를 맛본다.",
        "historical_note": "현대 한국무용에 도입된 기교적 동작으로, 전통과 현대의 조화를 보여줍니다.",
        "video_file": "expanded-actions/jumping-spin.mp4",
        "detail_videos": [
            {"part": "점프 발구르기", "video": None},
            {"part": "공중 회전", "video": None},
            {"part": "착지", "video": None},
            {"part": "팔 포지션", "video": None}
        ]
    },
    {
        "name": "연풍대",
        "description": "바람에 흔들리는 버드나무처럼 원을 그리며 회전하는 동작",
        "story_card": "버들가지가 바람에 흔들리듯, 몸 전체가 부드럽게 흐른다. 자연의 유연함을 몸으로 표현하는 순간.",
        "historical_note": "조선시대 춤에서 자연의 움직임을 가장 아름답게 형상화한 대표적 동작입니다.",
        "video_file": "expanded-actions/Yeon-pung-dae.mp4",
        "detail_videos": [
            {"part": "상체 원 그리기", "video": None},
            {"part": "팔 흐름", "video": None},
            {"part": "허리 유연성", "video": None},
            {"part": "발 위치", "video": None},
            {"part": "호흡 연결", "video": None}
        ]
    },
    {
        "name": "치마채기",
        "description": "치마 자락을 들어 움직임을 강조하는 동작",
        "story_card": "치마가 펼쳐지는 순간, 작은 동작이 극적인 시각 효과를 만든다. 옷과 몸이 하나 되는 춤.",
        "historical_note": "한복의 아름다움을 활용한 독특한 한국무용 기법으로, 의상과 춤의 조화를 보여줍니다.",
        "video_file": "expanded-actions/skirt-snatch.mp4",
        "detail_videos": [
            {"part": "손 잡는 위치", "video": None},
            {"part": "들어올리는 각도", "video": None},
            {"part": "상체 움직임", "video": None}
        ]
    }
]

# 확장 동작 (6개) - 영어
expanded_actions_en = [
    {
        "name": "Double Steps",
        "description": "Steps crossing two feet alternately",
        "story_card": "Rhythm created by crossing feet. Simple steps layering to create complex beauty.",
        "historical_note": "Developed in court dance to express intricate footwork, requiring delicate balance.",
        "video_file": "expanded-actions/double-steps.mp4",
        "detail_videos": [
            {"part": "Foot crossing", "video": None},
            {"part": "Weight shift", "video": None},
            {"part": "Ankle angle", "video": None},
            {"part": "Upper body balance", "video": None}
        ]
    },
    {
        "name": "Spin in Place",
        "description": "Rotating while standing in the same spot",
        "story_card": "Maintaining center while perspective on the world changes. Rotation embracing the universe from one's place.",
        "historical_note": "Korean dance's 'spinning' contains the philosophy of rotating without losing center.",
        "video_file": "expanded-actions/spin-in-place.mp4",
        "detail_videos": [
            {"part": "Foot pivot", "video": None},
            {"part": "Center axis", "video": None},
            {"part": "Eye spotting", "video": None}
        ]
    },
    {
        "name": "Moving Spin",
        "description": "Rotating while moving through space",
        "story_card": "Body rotating while traversing space. Movement and rotation become one to create flow.",
        "historical_note": "Advanced technique performing spatial movement and rotation simultaneously, maximizing dance dynamics.",
        "video_file": "expanded-actions/moving-spin.mp4",
        "detail_videos": [
            {"part": "Foot path", "video": None},
            {"part": "Rotation timing", "video": None},
            {"part": "Arm usage", "video": None},
            {"part": "Eye direction", "video": None},
            {"part": "Space utilization", "video": None}
        ]
    },
    {
        "name": "Jumping Spin",
        "description": "Rotating while leaping",
        "story_card": "Moment defying gravity, body rotates in air. Tasting freedom between sky and earth.",
        "historical_note": "Technical movement introduced to modern Korean dance, showing harmony of tradition and modernity.",
        "video_file": "expanded-actions/jumping-spin.mp4",
        "detail_videos": [
            {"part": "Jump takeoff", "video": None},
            {"part": "Air rotation", "video": None},
            {"part": "Landing", "video": None},
            {"part": "Arm position", "video": None}
        ]
    },
    {
        "name": "Willow in Wind",
        "description": "Rotating in circles like a willow swaying in wind",
        "story_card": "Like willow branches swaying in wind, the whole body flows softly. Moment expressing nature's flexibility through body.",
        "historical_note": "Representative movement most beautifully visualizing nature's motion in Joseon dynasty dance.",
        "video_file": "expanded-actions/Yeon-pung-dae.mp4",
        "detail_videos": [
            {"part": "Upper body circle", "video": None},
            {"part": "Arm flow", "video": None},
            {"part": "Waist flexibility", "video": None},
            {"part": "Foot position", "video": None},
            {"part": "Breath connection", "video": None}
        ]
    },
    {
        "name": "Skirt Catch",
        "description": "Lifting skirt hem to emphasize movement",
        "story_card": "Moment skirt unfolds, small movement creates dramatic visual effect. Dance where clothing and body become one.",
        "historical_note": "Unique Korean dance technique utilizing hanbok's beauty, showing harmony of costume and dance.",
        "video_file": "expanded-actions/skirt-snatch.mp4",
        "detail_videos": [
            {"part": "Hand grip position", "video": None},
            {"part": "Lifting angle", "video": None},
            {"part": "Upper body movement", "video": None}
        ]
    }
]

# 언어에 따라 확장 동작 선택
def get_expanded_actions(lang='ko'):
    return expanded_actions_ko if lang == 'ko' else expanded_actions_en

expanded_actions = expanded_actions_ko  # 기본값

# 창작 동작 (8개) - 한국어
creative_actions_ko = [
    {
        "name": "풀업",
        "description": "몸을 위로 길게 끌어올리는 동작",
        "story_card": "땅에서 하늘로 뻗어 오르는 에너지. 중력에 저항하며 몸 전체가 위로 솟구친다.",
        "historical_note": "현대무용에서 유래한 동작으로, 전통무용의 절제미와 대비되는 역동성을 보여줍니다.",
        "video_file": "creative-actions/pull-up.mp4",
        "detail_videos": [
            {"part": "복부 긴장", "video": None},
            {"part": "척추 연장", "video": None},
            {"part": "팔 포지션", "video": None}
        ]
    },
    {
        "name": "인파세/아웃파세",
        "description": "무릎을 굽혀 발끝을 무릎에 붙이고 안팎으로 드는 동작",
        "story_card": "한 발로 선 채 다른 다리로 균형을 찾는다. 내면과 외면을 오가는 움직임의 대화.",
        "historical_note": "발레에서 온 기법이지만 한국무용에서 재해석되어 독특한 미학을 만들어냅니다.",
        "video_file": "creative-actions/in-pase.mp4",
        "detail_videos": [
            {"part": "지지발 균형", "video": None},
            {"part": "무릎 위치", "video": None},
            {"part": "발끝 포인트", "video": None}
        ]
    },
    {
        "name": "턴",
        "description": "몸을 축으로 삼아 위로 세워 회전하는 동작",
        "story_card": "몸이 하나의 축이 되어 빠르게 회전한다. 세상이 돌아가는 것이 아니라 내가 회전하며 세상을 본다.",
        "historical_note": "서양 무용의 턴 기법을 한국무용에 접목한 현대적 표현입니다.",
        "video_file": "creative-actions/up-turn.mp4",
        "detail_videos": [
            {"part": "발 준비 자세", "video": None},
            {"part": "회전축 세우기", "video": None},
            {"part": "시선 스포팅", "video": None},
            {"part": "팔 포지션", "video": None}
        ]
    },
    {
        "name": "점프",
        "description": "바닥을 박차고 공중으로 뛰어오르는 동작",
        "story_card": "땅을 박차는 순간, 잠시나마 자유를 경험한다. 공중에 머무는 짧은 시간이 영원처럼 느껴진다.",
        "historical_note": "전통 한국무용의 절제된 움직임과 대조적인, 현대 무용의 폭발적 에너지를 표현합니다.",
        "video_file": "creative-actions/jump.mp4",
        "detail_videos": [
            {"part": "플리에 준비", "video": None},
            {"part": "도약", "video": None},
            {"part": "공중 자세", "video": None},
            {"part": "착지", "video": None}
        ]
    },
    {
        "name": "롤링",
        "description": "몸을 바닥에 굴리며 회전하는 동작",
        "story_card": "바닥과 하나 되어 굴러간다. 낮아질수록 더 깊이 땅의 에너지를 느낀다.",
        "historical_note": "현대무용의 플로어워크를 한국무용에 도입한 혁신적 시도입니다.",
        "video_file": "creative-actions/rolling.mp4",
        "detail_videos": [
            {"part": "시작 자세", "video": None},
            {"part": "척추 굴림", "video": None},
            {"part": "방향 전환", "video": None},
            {"part": "일어서기", "video": None},
            {"part": "호흡", "video": None}
        ]
    },
    {
        "name": "컨트렉션",
        "description": "복부와 척추를 안으로 수축하는 동작",
        "story_card": "몸을 안으로 수축하며 내면의 힘을 모은다. 팽창 전의 긴장, 폭발 전의 고요.",
        "historical_note": "마사 그레이엄의 현대무용 기법을 기반으로 한 강렬한 표현 방식입니다.",
        "video_file": "creative-actions/contraction.mp4",
        "detail_videos": [
            {"part": "복부 수축", "video": None},
            {"part": "척추 C커브", "video": None},
            {"part": "호흡 조절", "video": None}
        ]
    },
    {
        "name": "웨이브",
        "description": "척추와 몸통을 물결처럼 이어 흐르는 동작",
        "story_card": "파도가 밀려오듯 몸이 물결친다. 척추 하나하나가 순차적으로 움직이며 흐름을 만든다.",
        "historical_note": "동양 무술의 움직임과 현대무용이 결합된 유려한 표현 기법입니다.",
        "video_file": "creative-actions/wave.mp4",
        "detail_videos": [
            {"part": "머리부터 시작", "video": None},
            {"part": "척추 분절 움직임", "video": None},
            {"part": "골반 완성", "video": None},
            {"part": "역방향 웨이브", "video": None},
            {"part": "팔 연결", "video": None}
        ]
    },
    {
        "name": "컴퍼스턴",
        "description": "다리를 축으로 크게 원을 그리며 도는 동작",
        "story_card": "몸이 컴퍼스가 되어 공간에 원을 그린다. 중심은 고정되고 끝은 자유롭게 움직인다.",
        "historical_note": "브레이킹과 현대무용의 기교적 요소를 접목한 역동적 동작입니다.",
        "video_file": "creative-actions/compass-turn.mp4",
        "detail_videos": [
            {"part": "손과 발 지지", "video": None},
            {"part": "다리 스윙", "video": None},
            {"part": "회전 속도", "video": None},
            {"part": "중심 유지", "video": None},
            {"part": "마무리", "video": None},
            {"part": "힘의 분배", "video": None}
        ]
    }
]

# 창작 동작 (8개) - 영어
creative_actions_en = [
    {
        "name": "Pull Up",
        "description": "Movement pulling body upward lengthwise",
        "story_card": "Energy stretching from earth to sky. Entire body surges upward resisting gravity.",
        "historical_note": "Originating from modern dance, showing dynamism contrasting with traditional dance's restraint.",
        "video_file": "creative-actions/pull-up.mp4",
        "detail_videos": [
            {"part": "Core tension", "video": None},
            {"part": "Spine extension", "video": None},
            {"part": "Arm position", "video": None}
        ]
    },
    {
        "name": "Passé In/Out",
        "description": "Bending knee to attach toes to knee, lifting inward and outward",
        "story_card": "Finding balance with one leg while standing on the other. Movement dialogue traveling between inner and outer.",
        "historical_note": "Though from ballet, reinterpreted in Korean dance to create unique aesthetics.",
        "video_file": "creative-actions/in-pase.mp4"
    },
    {
        "name": "Turn",
        "description": "Rotating upward using body as axis",
        "story_card": "Body becomes an axis rotating rapidly. Not the world turning, but I rotate to view the world.",
        "historical_note": "Modern expression grafting Western dance's turn technique onto Korean dance.",
        "video_file": "creative-actions/up-turn.mp4"
    },
    {
        "name": "Jump",
        "description": "Leaping off the ground into the air",
        "story_card": "Moment kicking off ground, briefly experiencing freedom. Short time in air feels like eternity.",
        "historical_note": "Expressing modern dance's explosive energy contrasting with traditional Korean dance's restrained movement.",
        "video_file": "creative-actions/jump.mp4"
    },
    {
        "name": "Rolling",
        "description": "Rolling body on the floor while rotating",
        "story_card": "Rolling as one with the floor. Lower you go, deeper you feel earth's energy.",
        "historical_note": "Innovative attempt introducing modern dance's floorwork to Korean dance.",
        "video_file": "creative-actions/rolling.mp4"
    },
    {
        "name": "Contraction",
        "description": "Contracting abdomen and spine inward",
        "story_card": "Contracting body inward gathers inner strength. Tension before expansion, stillness before explosion.",
        "historical_note": "Intense expression method based on Martha Graham's modern dance technique.",
        "video_file": "creative-actions/contraction.mp4"
    },
    {
        "name": "Wave",
        "description": "Flowing spine and torso in wave-like succession",
        "story_card": "Body ripples like incoming waves. Each vertebra moves sequentially to create flow.",
        "historical_note": "Fluid expression technique combining Eastern martial arts movement with modern dance.",
        "video_file": "creative-actions/wave.mp4"
    },
    {
        "name": "Compass Turn",
        "description": "Drawing large circles with leg as axis while turning",
        "story_card": "Body becomes compass drawing circles in space. Center fixed, extremity moves freely.",
        "historical_note": "Dynamic movement grafting technical elements of breaking and modern dance.",
        "video_file": "creative-actions/compass-turn.mp4"
    }
]

# 언어에 따라 창작 동작 선택
def get_creative_actions(lang='ko'):
    return creative_actions_ko if lang == 'ko' else creative_actions_en

creative_actions = creative_actions_ko  # 기본값

# 스토리 콘텐츠 - 한국어
story_contents_ko = [
    {
        "title": "정중동의 미학",
        "avatar": "🧘‍♀️",
        "content": "고요함 속에 움직임이 있다는 한국무용의 핵심 철학입니다. 겉으로는 잔잔해 보이지만 내면에는 강렬한 에너지가 흐르고 있어요. 마치 잔잔한 호수 표면 아래 깊은 물줄기가 흐르는 것처럼, 한국무용은 절제된 움직임 속에 폭발적인 감정을 숨기고 있습니다.\n\n이런 미학은 현대 K-pop에서도 발견할 수 있어요. BTS의 'Spring Day'에서 보이는 절제된 안무나, 아이유의 차분하면서도 깊은 울림이 있는 퍼포먼스가 바로 정중동의 현대적 해석이라고 할 수 있습니다.",
        "historical_note": "조선시대 궁중무에서 발달한 이 개념은 '움직이지 않는 것 같으나 실제로는 끊임없이 움직이는' 동양 철학의 핵심입니다."
    },
    {
        "title": "자연과의 합일",
        "avatar": "🌿",
        "content": "한국무용의 모든 동작은 자연에서 영감을 받았습니다. '좌우새'는 새의 머리 흔들림을, '바람불기'는 자연의 바람을 형상화했어요. 이는 단순한 모방이 아니라, 인간이 자연의 일부임을 인정하고 조화를 추구하는 동양 철학의 발현입니다.\n\n우리 조상들은 춤을 통해 자연과 대화했어요. 학춤에서는 학의 우아함을, 승무에서는 나비의 가벼움을 표현했죠. 이런 자연 친화적 사고는 현재 전 세계적으로 주목받는 지속가능성과 환경 의식의 선구자적 모습을 보여줍니다.",
        "historical_note": "삼국시대부터 이어진 이 전통은 무속의 자연 숭배 사상과 불교, 도교의 자연관이 융합되어 형성되었습니다."
    },
    {
        "title": "K-pop 속 전통의 흔적",
        "avatar": "🎤",
        "content": "현대 K-pop 안무에는 한국무용의 DNA가 자연스럽게 스며들어 있습니다. BTS의 'Idol'에서 보이는 팔 감기 동작, 블랙핑크 제니의 절제된 손목 움직임, (여자)아이들의 전통적인 라인감... 이 모든 것들이 한국무용에서 온 것이에요.\n\n특히 '손목감기'나 '팔 감기' 같은 미세한 움직임은 서양 댄스에서는 찾아보기 힘든 한국만의 고유한 표현입니다. 이런 동작들이 K-pop을 단순한 팝음악이 아닌, 고유한 문화적 정체성을 가진 예술로 만들어주는 거죠.",
        "historical_note": "1990년대부터 시작된 K-pop과 전통무용의 접목은 이제 전 세계적으로 '한국적인 것'의 상징이 되었습니다."
    },
    {
        "title": "호흡의 철학",
        "avatar": "💨",
        "content": "한국무용에서 호흡은 단순한 숨이 아닙니다. 우주의 기운을 받아들이고 내뿜는 생명의 순환을 의미해요. '긴 호흡'은 여유와 깊이를, '짧은 호흡'은 순간의 강렬함을, '겹호흡'은 복잡한 감정의 층위를 표현합니다.\n\n이런 호흡법은 현대인의 마음을 치유하는 힘이 있어요. 스트레스로 얕아진 호흡을 깊게 만들고, 몸과 마음의 연결을 회복시켜 줍니다. 요가나 명상이 서구에서 주목받는 이유와 같은 맥락이죠.\n\n춤마루에서 경험하는 각 동작의 호흡은 단순한 운동이 아니라, 5000년 전통의 치유법을 체험하는 시간입니다.",
        "historical_note": "조선 후기 실학자들은 이미 호흡과 건강의 관계를 깊이 연구했으며, 이는 현대 스포츠 과학과도 일맥상통합니다."
    }
]

# 스토리 콘텐츠 - 영어
story_contents_en = [
    {
        "title": "Aesthetics of Stillness in Motion",
        "avatar": "🧘‍♀️",
        "content": "Korean dance's core philosophy is that movement exists within stillness. Though appearing calm on the surface, intense energy flows within. Like deep currents flowing beneath a tranquil lake surface, Korean dance conceals explosive emotions within restrained movements.\n\nThis aesthetic can be found in modern K-pop too. The restrained choreography in BTS's 'Spring Day' or IU's calm yet deeply resonant performance can be seen as modern interpretations of stillness in motion.",
        "historical_note": "Developed in Joseon dynasty court dance, this concept is central to Eastern philosophy: 'seeming motionless yet constantly moving'."
    },
    {
        "title": "Unity with Nature",
        "avatar": "🌿",
        "content": "All Korean dance movements are inspired by nature. 'Jwau-sae' visualizes a bird's head shaking, 'Wind Blowing' embodies natural wind. This isn't simple imitation, but manifestation of Eastern philosophy acknowledging humans as part of nature, seeking harmony.\n\nOur ancestors dialogued with nature through dance. Crane dance expressed the crane's elegance, monk dance the butterfly's lightness. This nature-friendly thinking shows pioneering aspects of sustainability and environmental consciousness now gaining global attention.",
        "historical_note": "This tradition from the Three Kingdoms period formed through fusion of shamanic nature worship with Buddhist and Taoist views of nature."
    },
    {
        "title": "Traditional Traces in K-pop",
        "avatar": "🎤",
        "content": "Korean dance's DNA naturally permeates modern K-pop choreography. Arm circle movements in BTS's 'Idol', Jennie of Blackpink's restrained wrist movements, (G)I-DLE's traditional lines... all originate from Korean dance.\n\nEspecially subtle movements like 'wrist circles' or 'arm circles' are unique Korean expressions rarely found in Western dance. These movements make K-pop not just pop music, but art with unique cultural identity.",
        "historical_note": "The grafting of K-pop and traditional dance starting in the 1990s has now become a worldwide symbol of 'Korean-ness'."
    },
    {
        "title": "Philosophy of Breathing",
        "avatar": "💨",
        "content": "In Korean dance, breathing isn't just breath. It signifies life's circulation of receiving and releasing universal energy. 'Long breath' expresses leisure and depth, 'short breath' momentary intensity, 'layered breath' complex emotional layers.\n\nThis breathing method has power to heal modern minds. It deepens breath shallowed by stress, restoring mind-body connection. Same reason yoga and meditation gain attention in the West.\n\nBreathing in each movement you experience at Choomaru isn't just exercise, but time experiencing 5000 years of healing tradition.",
        "historical_note": "Late Joseon practical scholars already deeply researched breathing's relationship to health, aligned with modern sports science."
    }
]

# 언어에 따라 스토리 콘텐츠 선택
def get_story_contents(lang='ko'):
    return story_contents_ko if lang == 'ko' else story_contents_en

story_contents = story_contents_ko  # 기본값

# 배지 시스템
badge_system_ko = {
    3: {"name": "입문자", "emoji": "🌱", "message": "몸이 기억하기 시작했어요", "color": "#22C55E"},
    6: {"name": "수련자", "emoji": "🎋", "message": "당신 안의 한국인이 깨어나고 있어요", "color": "#3B82F6"},
    9: {"name": "달인", "emoji": "🏔️", "message": "이제 진짜 K-무브먼트를 이해하시네요", "color": "#8B5CF6"},
    12: {"name": "마스터", "emoji": "👑", "message": "K-DNA 각성 완료", "color": "#F59E0B"}
}

badge_system_en = {
    3: {"name": "Beginner", "emoji": "🌱", "message": "Your body is starting to remember", "color": "#22C55E"},
    6: {"name": "Practitioner", "emoji": "🎋", "message": "The Korean within you is awakening", "color": "#3B82F6"},
    9: {"name": "Master", "emoji": "🏔️", "message": "You now truly understand K-Movement", "color": "#8B5CF6"},
    12: {"name": "Grand Master", "emoji": "👑", "message": "K-DNA Awakening Complete", "color": "#F59E0B"}
}

def get_badge_system(lang='ko'):
    return badge_system_ko if lang == 'ko' else badge_system_en

badge_system = badge_system_ko  # 기본값

# DNA 분석 함수 (8개 타입 매핑)
def analyze_dna(answers):
    scores = {"A": 0, "B": 0, "C": 0, "D": 0}
    for answer in answers:
        scores[answer] += 1
    
    # 가장 높은 점수 두 개 찾기
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_two = sorted([sorted_scores[0][0], sorted_scores[1][0]])
    combination = " + ".join(top_two)
    
    # 8개 타입 조합에 따른 결과 매핑
    combinations = {
        "A + D": "밈 장인",
        "A + C": "무드 큐레이터", 
        "A + B": "갓생 플래너",
        "B + C": "디테일 장인",
        "C + D": "인간 공명기",
        "B + D": "파티 히어로",
        "C + D": "감성 필터",  # C+D 중복 해결을 위해 점수 차이로 구분
        "A + A": "흥 폭발러",  # 동점 처리
        "B + B": "갓생 플래너",
        "C + C": "감성 필터",
        "D + D": "흥 폭발러"
    }
    
    # 동점인 경우 세밀한 분석
    if sorted_scores[0][1] == sorted_scores[1][1]:
        if sorted_scores[0][1] == sorted_scores[2][1]:  # 3점 동점
            return "밈 장인"  # 기본값
        # C+D 구분 로직
        if combination == "C + D":
            c_score = scores["C"]
            d_score = scores["D"]
            return "감성 필터" if c_score >= d_score else "인간 공명기"
    
    return combinations.get(combination, "밈 장인")

# 세부 영상 표시 함수
def render_detail_videos(detail_videos, main_video_path):
    """
    세부 영상을 개수에 따라 다른 레이아웃으로 표시
    - 3개 이하: 하단 일렬 배치
    - 4-5개: 하단 2줄 배치
    - 6개 이상: 탭 방식
    """
    if not detail_videos or len(detail_videos) == 0:
        return
    
    detail_count = len(detail_videos)
    lang = st.session_state.language
    
    st.markdown("---")
    
    if detail_count <= 3:
        # 3개 이하: 하단 일렬 배치
        st.markdown(f"#### 📹 {'부위별 세부 영상' if lang == 'ko' else 'Detailed Parts'}")
        cols = st.columns(detail_count)
        for idx, detail in enumerate(detail_videos):
            with cols[idx]:
                st.markdown(f"**{detail['part']}**")
                if detail['video']:
                    try:
                        st.video(f"videos/{detail['video']}")
                    except:
                        st.info(f"🎬 {'영상 준비 중' if lang == 'ko' else 'Coming soon'}")
                else:
                    st.info(f"🎬 {'영상 준비 중' if lang == 'ko' else 'Coming soon'}")
    
    elif detail_count <= 5:
        # 4-5개: 하단 2줄 배치
        st.markdown(f"#### 📹 {'부위별 세부 영상' if lang == 'ko' else 'Detailed Parts'}")
        # 첫 번째 줄: 최대 3개
        first_row_count = min(3, detail_count)
        cols1 = st.columns(first_row_count)
        for idx in range(first_row_count):
            with cols1[idx]:
                detail = detail_videos[idx]
                st.markdown(f"**{detail['part']}**")
                if detail['video']:
                    try:
                        st.video(f"videos/{detail['video']}")
                    except:
                        st.info(f"🎬 {'영상 준비 중' if lang == 'ko' else 'Coming soon'}")
                else:
                    st.info(f"🎬 {'영상 준비 중' if lang == 'ko' else 'Coming soon'}")
        
        # 두 번째 줄: 나머지
        if detail_count > 3:
            second_row_count = detail_count - 3
            cols2 = st.columns(second_row_count)
            for idx in range(second_row_count):
                with cols2[idx]:
                    detail = detail_videos[3 + idx]
                    st.markdown(f"**{detail['part']}**")
                    if detail['video']:
                        try:
                            st.video(f"videos/{detail['video']}")
                        except:
                            st.info(f"🎬 {'영상 준비 중' if lang == 'ko' else 'Coming soon'}")
                    else:
                        st.info(f"🎬 {'영상 준비 중' if lang == 'ko' else 'Coming soon'}")
    
    else:
        # 6개 이상: 탭 방식
        st.markdown(f"#### 📹 {'부위별 세부 영상' if lang == 'ko' else 'Detailed Parts'}")
        tab_names = [detail['part'] for detail in detail_videos]
        tabs = st.tabs(tab_names)
        
        for idx, tab in enumerate(tabs):
            with tab:
                detail = detail_videos[idx]
                if detail['video']:
                    try:
                        st.video(f"videos/{detail['video']}")
                    except:
                        st.info(f"🎬 {'영상 준비 중' if lang == 'ko' else 'Coming soon'}")
                else:
                    st.info(f"🎬 {'영상 준비 중' if lang == 'ko' else 'Coming soon'}")

# MediaPipe 초기화
@st.cache_resource
def init_mediapipe():
    """MediaPipe Pose Landmarker 초기화 (새 API)"""
    model_path = os.path.join(os.path.dirname(__file__), "models", "pose_landmarker_lite.task")

    # PoseLandmarker 옵션 설정
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        min_pose_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    landmarker = vision.PoseLandmarker.create_from_options(options)

    # 기존 코드와의 호환성을 위해 landmarker를 두 번 반환
    return landmarker, landmarker

# ==================== 자세 비교 유틸리티 ====================

def get_landmark_value(lm, key):
    """랜드마크에서 값을 가져옴 (dict 또는 객체 모두 지원)"""
    if isinstance(lm, dict):
        return lm.get(key, 0)
    else:
        return getattr(lm, key, 0)

def normalize_landmarks(landmarks):
    """
    좌표계 독립적 비교를 위한 랜드마크 정규화

    방법:
    1. 골반 중심점을 기준점으로 설정 (landmark 23, 24의 중점)
    2. 어깨 너비로 스케일 정규화 (landmark 11, 12 거리)
    3. 모든 좌표를 상대 좌표로 변환
    """
    if not landmarks or len(landmarks) < 33:
        return None

    # 골반 중심점 계산 (landmark 23, 24)
    hip_left = landmarks[23]
    hip_right = landmarks[24]
    hip_center_x = (get_landmark_value(hip_left, 'x') + get_landmark_value(hip_right, 'x')) / 2
    hip_center_y = (get_landmark_value(hip_left, 'y') + get_landmark_value(hip_right, 'y')) / 2
    hip_center_z = (get_landmark_value(hip_left, 'z') + get_landmark_value(hip_right, 'z')) / 2

    # 어깨 너비 계산 (landmark 11, 12)
    shoulder_left = landmarks[11]
    shoulder_right = landmarks[12]
    shoulder_width = np.sqrt(
        (get_landmark_value(shoulder_right, 'x') - get_landmark_value(shoulder_left, 'x'))**2 +
        (get_landmark_value(shoulder_right, 'y') - get_landmark_value(shoulder_left, 'y'))**2 +
        (get_landmark_value(shoulder_right, 'z') - get_landmark_value(shoulder_left, 'z'))**2
    )

    if shoulder_width == 0:
        shoulder_width = 1.0  # 0으로 나누기 방지

    # 정규화된 랜드마크 생성
    normalized = []
    for lm in landmarks:
        lm_x = get_landmark_value(lm, 'x')
        lm_y = get_landmark_value(lm, 'y')
        lm_z = get_landmark_value(lm, 'z')
        lm_vis = get_landmark_value(lm, 'visibility') if (isinstance(lm, dict) or hasattr(lm, 'visibility')) else 1.0
        normalized.append({
            'x': (lm_x - hip_center_x) / shoulder_width,
            'y': (lm_y - hip_center_y) / shoulder_width,
            'z': (lm_z - hip_center_z) / shoulder_width,
            'visibility': lm_vis if lm_vis else 1.0
        })

    return normalized

def calculate_angle(point1, point2, point3):
    """
    3개 점으로 이루는 각도 계산 (point2가 꼭짓점)
    반환: 각도 (도 단위)
    """
    # 벡터 계산
    v1 = np.array([point1['x'] - point2['x'],
                   point1['y'] - point2['y'],
                   point1['z'] - point2['z']])
    v2 = np.array([point3['x'] - point2['x'],
                   point3['y'] - point2['y'],
                   point3['z'] - point2['z']])

    # 벡터의 내적과 크기로 각도 계산
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)  # 부동소수점 오차 보정
    angle = np.arccos(cos_angle)

    return np.degrees(angle)

def calculate_joint_angles(landmarks):
    """
    주요 관절 각도 계산 (visibility 0.3 이상만 포함)

    반환: dict {
        'left_elbow': 각도,
        'right_elbow': 각도,
        'left_knee': 각도,
        'right_knee': 각도,
        'left_shoulder': 각도,
        'right_shoulder': 각도,
        'left_hip': 각도,
        'right_hip': 각도
    }
    """
    if not landmarks:
        return {}

    angles = {}
    MIN_VISIBILITY = 0.3  # 최소 visibility 임계값 (낮춤)

    try:
        # 왼쪽 팔꿈치 (어깨11 - 팔꿈치13 - 손목15)
        if (landmarks[11]['visibility'] >= MIN_VISIBILITY and
            landmarks[13]['visibility'] >= MIN_VISIBILITY and
            landmarks[15]['visibility'] >= MIN_VISIBILITY):
            angles['left_elbow'] = calculate_angle(landmarks[11], landmarks[13], landmarks[15])

        # 오른쪽 팔꿈치 (어깨12 - 팔꿈치14 - 손목16)
        if (landmarks[12]['visibility'] >= MIN_VISIBILITY and
            landmarks[14]['visibility'] >= MIN_VISIBILITY and
            landmarks[16]['visibility'] >= MIN_VISIBILITY):
            angles['right_elbow'] = calculate_angle(landmarks[12], landmarks[14], landmarks[16])

        # 왼쪽 무릎 (골반23 - 무릎25 - 발목27)
        if (landmarks[23]['visibility'] >= MIN_VISIBILITY and
            landmarks[25]['visibility'] >= MIN_VISIBILITY and
            landmarks[27]['visibility'] >= MIN_VISIBILITY):
            angles['left_knee'] = calculate_angle(landmarks[23], landmarks[25], landmarks[27])

        # 오른쪽 무릎 (골반24 - 무릎26 - 발목28)
        if (landmarks[24]['visibility'] >= MIN_VISIBILITY and
            landmarks[26]['visibility'] >= MIN_VISIBILITY and
            landmarks[28]['visibility'] >= MIN_VISIBILITY):
            angles['right_knee'] = calculate_angle(landmarks[24], landmarks[26], landmarks[28])

        # 왼쪽 어깨 (골반23 - 어깨11 - 팔꿈치13)
        if (landmarks[23]['visibility'] >= MIN_VISIBILITY and
            landmarks[11]['visibility'] >= MIN_VISIBILITY and
            landmarks[13]['visibility'] >= MIN_VISIBILITY):
            angles['left_shoulder'] = calculate_angle(landmarks[23], landmarks[11], landmarks[13])

        # 오른쪽 어깨 (골반24 - 어깨12 - 팔꿈치14)
        if (landmarks[24]['visibility'] >= MIN_VISIBILITY and
            landmarks[12]['visibility'] >= MIN_VISIBILITY and
            landmarks[14]['visibility'] >= MIN_VISIBILITY):
            angles['right_shoulder'] = calculate_angle(landmarks[24], landmarks[12], landmarks[14])

        # 왼쪽 고관절 (어깨11 - 골반23 - 무릎25)
        if (landmarks[11]['visibility'] >= MIN_VISIBILITY and
            landmarks[23]['visibility'] >= MIN_VISIBILITY and
            landmarks[25]['visibility'] >= MIN_VISIBILITY):
            angles['left_hip'] = calculate_angle(landmarks[11], landmarks[23], landmarks[25])

        # 오른쪽 고관절 (어깨12 - 골반24 - 무릎26)
        if (landmarks[12]['visibility'] >= MIN_VISIBILITY and
            landmarks[24]['visibility'] >= MIN_VISIBILITY and
            landmarks[26]['visibility'] >= MIN_VISIBILITY):
            angles['right_hip'] = calculate_angle(landmarks[12], landmarks[24], landmarks[26])

    except Exception as e:
        # 디버그: 에러 정보 출력
        import traceback
        print(f"calculate_joint_angles 에러: {e}")
        print(traceback.format_exc())

    return angles

def compare_poses(user_landmarks, expert_landmarks):
    """
    전문가와 사용자 자세 비교

    반환: dict {
        'overall_score': 0-100,
        'joint_scores': {...},
        'feedback': [...]
    }
    """
    if not user_landmarks or not expert_landmarks:
        return {
            'overall_score': 0,
            'joint_scores': {},
            'feedback': ['자세를 인식할 수 없습니다'],
            'joint_coverage_percent': 0
        }

    # 랜드마크 정규화
    user_norm = normalize_landmarks(user_landmarks)
    expert_norm = normalize_landmarks(expert_landmarks)

    if not user_norm or not expert_norm:
        return {
            'overall_score': 0,
            'joint_scores': {},
            'feedback': ['랜드마크 정규화 실패'],
            'joint_coverage_percent': 0
        }

    # 관절 각도 계산
    user_angles = calculate_joint_angles(user_norm)
    expert_angles = calculate_joint_angles(expert_norm)

    # 보이는 관절만 비교 (최소 1개 이상)
    joint_scores = {}
    angle_diffs = {}

    # 사용자와 전문가 양쪽에 모두 있는 관절만 비교
    for joint_name in user_angles.keys():
        if joint_name in expert_angles:
            diff = abs(user_angles[joint_name] - expert_angles[joint_name])
            angle_diffs[joint_name] = diff

            # 점수 계산 (차이가 0도 = 100점, 30도 이상 = 0점)
            score = max(0, 100 - (diff / 30.0) * 100)
            joint_scores[joint_name] = score

    # 비교 가능한 관절이 하나도 없는 경우
    if not joint_scores:
        return {
            'overall_score': 1,
            'joint_scores': {},
            'angle_diffs': {},
            'feedback': ['📸 자세를 조금 더 명확하게 취해주세요'],
            'joint_coverage_percent': 0
        }

    # 전체 점수 계산 (비교된 관절들의 평균)
    overall_score = np.mean(list(joint_scores.values()))

    # 피드백 생성
    feedback = generate_feedback(angle_diffs, user_angles, expert_angles)

    # 관절 감지율 계산 (백분율)
    num_compared = len(joint_scores)
    total_joints = 8  # 전체 관절 수
    joint_coverage_percent = int((num_compared / total_joints) * 100)

    return {
        'overall_score': overall_score,
        'joint_scores': joint_scores,
        'angle_diffs': angle_diffs,
        'feedback': feedback,
        'joint_coverage_percent': joint_coverage_percent
    }

def generate_feedback(angle_diffs, user_angles, expert_angles):
    """
    각도 차이를 기반으로 구체적인 피드백 생성
    """
    feedback = []

    # 관절 이름 한글 매핑
    joint_names_ko = {
        'left_elbow': '왼쪽 팔꿈치',
        'right_elbow': '오른쪽 팔꿈치',
        'left_knee': '왼쪽 무릎',
        'right_knee': '오른쪽 무릎',
        'left_shoulder': '왼쪽 어깨',
        'right_shoulder': '오른쪽 어깨',
        'left_hip': '왼쪽 골반',
        'right_hip': '오른쪽 골반'
    }

    # 차이가 큰 순서대로 정렬
    sorted_diffs = sorted(angle_diffs.items(), key=lambda x: x[1], reverse=True)

    # 상위 3개만 피드백
    for joint_name, diff in sorted_diffs[:3]:
        if diff < 10:  # 10도 미만은 양호
            continue

        korean_name = joint_names_ko.get(joint_name, joint_name)
        user_angle = user_angles.get(joint_name, 0)
        expert_angle = expert_angles.get(joint_name, 0)

        # 방향 결정
        if user_angle > expert_angle:
            if '팔꿈치' in korean_name or '무릎' in korean_name:
                direction = f"{int(diff)}도 더 구부리세요"
            else:
                direction = f"{int(diff)}도 더 내리세요"
        else:
            if '팔꿈치' in korean_name or '무릎' in korean_name:
                direction = f"{int(diff)}도 더 펴세요"
            else:
                direction = f"{int(diff)}도 더 올리세요"

        # 심각도 표시
        if diff > 30:
            severity = "🔴"
        elif diff > 15:
            severity = "🟡"
        else:
            severity = "🟢"

        feedback.append(f"{severity} {korean_name}를 {direction}")

    if not feedback:
        feedback.append("🟢 완벽합니다!")

    return feedback

# 동작 분석 함수 (간단한 예시)
def analyze_movement(pose_landmarks, action_name):
    """
    실제로는 더 복잡한 동작 분석 로직이 들어갈 곳
    현재는 랜덤으로 성공/실패 반환
    """
    # 랜덤 성공/실패 (70% 성공률)
    success = random.random() > 0.3

    if success:
        return {
            "success": True,
            "score": random.randint(85, 98),
            "message": "완벽합니다! 움직임 속에 숨겨진 의미를 느끼셨나요?"
        }
    else:
        return {
            "success": False,
            "score": random.randint(45, 75),
            "message": "아쉬워요! 천천히 따라해보세요."
        }

# 비디오 프레임 캡쳐 함수
def capture_video_frame(video_path, frame_position=0.5):
    """
    비디오에서 특정 위치의 프레임을 캡쳐
    frame_position: 0.0 ~ 1.0 (비디오의 위치 비율)
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        target_frame = int(total_frames * frame_position)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            # BGR to RGB 변환
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(frame)
    except Exception as e:
        print(f"비디오 프레임 캡쳐 오류: {e}")
    
    return None

# 밈 카드 생성 함수 (개선된 버전)
def create_meme_card(dna_type_name, dna_data):
    """DNA 영상 배경을 사용한 밈 카드 생성"""
    width, height = 1080, 1080
    
    # 1. DNA 타입 영상에서 프레임 캡쳐 시도
    video_path = f"videos/{dna_data['video_file']}"
    background = capture_video_frame(video_path, frame_position=0.5)
    
    if background:
        # 이미지 크기 조정 (정사각형으로 크롭)
        bg_width, bg_height = background.size
        
        # 중앙 크롭
        if bg_width > bg_height:
            left = (bg_width - bg_height) // 2
            background = background.crop((left, 0, left + bg_height, bg_height))
        else:
            top = (bg_height - bg_width) // 2
            background = background.crop((0, top, bg_width, top + bg_width))
        
        # 리사이즈
        background = background.resize((width, height), Image.Resampling.LANCZOS)
        
        # 약간 어둡게 (텍스트 가독성 향상)
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.5)
        
        # 약간 블러 효과
        background = background.filter(ImageFilter.GaussianBlur(2))
    else:
        # 영상이 없으면 단색 배경 사용
        background = Image.new('RGB', (width, height), color=dna_data['color'])
    
    # 2. 반투명 오버레이 레이어 추가
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 120))
    background = background.convert('RGBA')
    background = Image.alpha_composite(background, overlay)
    
    # 3. 텍스트 추가
    draw = ImageDraw.Draw(background)
    
    # 폰트 로드 시도
    try:
        # Windows 한글 폰트
        title_font = ImageFont.truetype("malgun.ttf", 90)
        subtitle_font = ImageFont.truetype("malgun.ttf", 60)
        hashtag_font = ImageFont.truetype("malgun.ttf", 45)
    except:
        try:
            # 다른 한글 폰트 시도
            title_font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 90)
            subtitle_font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 60)
            hashtag_font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 45)
        except:
            # 기본 폰트
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            hashtag_font = ImageFont.load_default()
    
    # 언어에 따른 텍스트
    lang = st.session_state.get('language', 'ko')
    
    # 텍스트 위치 및 내용
    texts = [
        {
            "text": f"{t('meme_i_am', lang)} {dna_type_name}!",
            "font": title_font,
            "position": (width//2, height//3),
            "fill": "white"
        },
        {
            "text": f"{dna_data['emoji']} {dna_data['title']}",
            "font": subtitle_font,
            "position": (width//2, height//2),
            "fill": "white"
        },
        {
            "text": t('meme_hashtag', lang),
            "font": hashtag_font,
            "position": (width//2, height*3//4),
            "fill": "#FFD700"
        }
    ]
    
    # 텍스트 그리기 (외곽선 효과)
    for text_info in texts:
        x, y = text_info["position"]
        text = text_info["text"]
        font = text_info["font"]
        
        # 외곽선 (검은색) - 더 두껍게
        outline_range = 4
        for adj_x in range(-outline_range, outline_range + 1):
            for adj_y in range(-outline_range, outline_range + 1):
                if adj_x != 0 or adj_y != 0:
                    try:
                        draw.text((x + adj_x, y + adj_y), text, 
                                fill='black', font=font, anchor='mm')
                    except:
                        draw.text((x + adj_x, y + adj_y), text, 
                                fill='black', font=font)
        
        # 메인 텍스트
        try:
            draw.text((x, y), text, fill=text_info["fill"], font=font, anchor='mm')
        except:
            draw.text((x, y), text, fill=text_info["fill"], font=font)
    
    return background.convert('RGB')

# 스타일 A: 그라데이션 박스
def create_meme_card_gradient_box(dna_type_name, dna_data):
    """그라데이션 박스 스타일 - 상단/하단에 텍스트 박스"""
    width, height = 1080, 1080
    
    # 배경 영상 프레임 가져오기
    video_path = f"videos/{dna_data['video_file']}"
    background = capture_video_frame(video_path, frame_position=0.5)
    
    if background:
        bg_width, bg_height = background.size
        if bg_width > bg_height:
            left = (bg_width - bg_height) // 2
            background = background.crop((left, 0, left + bg_height, bg_height))
        else:
            top = (bg_height - bg_width) // 2
            background = background.crop((0, top, bg_width, top + bg_width))
        background = background.resize((width, height), Image.Resampling.LANCZOS)
        # 블러만 살짝
        background = background.filter(ImageFilter.GaussianBlur(1))
    else:
        background = Image.new('RGB', (width, height), color=dna_data['color'])
    
    background = background.convert('RGBA')
    
    # 상단 그라데이션 박스
    top_box_height = 250
    for i in range(top_box_height):
        alpha = int(200 * (1 - i / top_box_height))  # 200 -> 0
        overlay_line = Image.new('RGBA', (width, 1), (0, 0, 0, alpha))
        background.paste(overlay_line, (0, i), overlay_line)
    
    # 하단 그라데이션 박스
    bottom_box_height = 200
    for i in range(bottom_box_height):
        alpha = int(200 * (i / bottom_box_height))  # 0 -> 200
        overlay_line = Image.new('RGBA', (width, 1), (0, 0, 0, alpha))
        background.paste(overlay_line, (0, height - bottom_box_height + i), overlay_line)
    
    draw = ImageDraw.Draw(background)
    
    # 폰트
    try:
        title_font = ImageFont.truetype("malgun.ttf", 85)
        subtitle_font = ImageFont.truetype("malgun.ttf", 55)
        hashtag_font = ImageFont.truetype("malgun.ttf", 42)
    except:
        title_font = subtitle_font = hashtag_font = ImageFont.load_default()
    
    # 상단 텍스트
    top_texts = [
        {"text": f"나는 {dna_type_name}!", "font": title_font, "y": 80},
        {"text": f"{dna_data['emoji']} {dna_data['title']}", "font": subtitle_font, "y": 165}
    ]
    
    for text_info in top_texts:
        x, y = width//2, text_info["y"]
        text = text_info["text"]
        font = text_info["font"]
        
        # 외곽선
        for adj in [(-3, -3), (-3, 0), (-3, 3), (0, -3), (0, 3), (3, -3), (3, 0), (3, 3)]:
            try:
                draw.text((x + adj[0], y + adj[1]), text, fill='black', font=font, anchor='mm')
            except:
                draw.text((x + adj[0], y + adj[1]), text, fill='black', font=font)
        
        try:
            draw.text((x, y), text, fill='white', font=font, anchor='mm')
        except:
            draw.text((x, y), text, fill='white', font=font)
    
    # 하단 해시태그
    hash_y = height - 100
    for adj in [(-3, -3), (-3, 0), (-3, 3), (0, -3), (0, 3), (3, -3), (3, 0), (3, 3)]:
        try:
            draw.text((width//2 + adj[0], hash_y + adj[1]), "#춤마루 #K_DNA각성", 
                     fill='black', font=hashtag_font, anchor='mm')
        except:
            draw.text((width//2 + adj[0], hash_y + adj[1]), "#춤마루 #K_DNA각성", 
                     fill='black', font=hashtag_font)
    
    try:
        draw.text((width//2, hash_y), "#춤마루 #K_DNA각성", 
                 fill='#FFD700', font=hashtag_font, anchor='mm')
    except:
        draw.text((width//2, hash_y), "#춤마루 #K_DNA각성", 
                 fill='#FFD700', font=hashtag_font)
    
    return background.convert('RGB')

# 스타일 B: 네온 스타일
def create_meme_card_neon(dna_type_name, dna_data):
    """네온 스타일 - 형광 색상 + 글로우 효과"""
    width, height = 1080, 1080
    
    # 배경
    video_path = f"videos/{dna_data['video_file']}"
    background = capture_video_frame(video_path, frame_position=0.5)
    
    if background:
        bg_width, bg_height = background.size
        if bg_width > bg_height:
            left = (bg_width - bg_height) // 2
            background = background.crop((left, 0, left + bg_height, bg_height))
        else:
            top = (bg_height - bg_width) // 2
            background = background.crop((0, top, bg_width, top + bg_width))
        background = background.resize((width, height), Image.Resampling.LANCZOS)
        # 약간만 어둡게 (영상이 보이도록)
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.5)
        background = background.filter(ImageFilter.GaussianBlur(2))
    else:
        background = Image.new('RGB', (width, height), color='#000033')
    
    background = background.convert('RGBA')
    
    # 다크 오버레이 (더 투명하게)
    overlay = Image.new('RGBA', (width, height), (0, 0, 30, 100))
    background = Image.alpha_composite(background, overlay)
    
    draw = ImageDraw.Draw(background)
    
    # 폰트
    try:
        title_font = ImageFont.truetype("malgun.ttf", 85)
        subtitle_font = ImageFont.truetype("malgun.ttf", 55)
        hashtag_font = ImageFont.truetype("malgun.ttf", 42)
    except:
        title_font = subtitle_font = hashtag_font = ImageFont.load_default()
    
    # 네온 색상
    neon_pink = '#FF10F0'
    neon_cyan = '#00FFFF'
    
    texts = [
        {"text": f"나는 {dna_type_name}!", "font": title_font, "y": 150, "color": neon_pink},
        {"text": f"{dna_data['emoji']} {dna_data['title']}", "font": subtitle_font, "y": 240, "color": neon_cyan},
        {"text": "#춤마루 #K_DNA각성", "font": hashtag_font, "y": 900, "color": neon_pink}
    ]
    
    for text_info in texts:
        x, y = width//2, text_info["y"]
        text = text_info["text"]
        font = text_info["font"]
        color = text_info["color"]
        
        # 글로우 효과 (얇게 조정)
        for glow_size in [4, 2]:
            for adj_x in range(-glow_size, glow_size + 1, 2):
                for adj_y in range(-glow_size, glow_size + 1, 2):
                    if adj_x != 0 or adj_y != 0:
                        try:
                            draw.text((x + adj_x, y + adj_y), text, 
                                    fill=color + '30', font=font, anchor='mm')
                        except:
                            pass
        
        # 외곽선 (검은색, 가독성)
        for adj in [(-2, -2), (-2, 0), (-2, 2), (0, -2), (0, 2), (2, -2), (2, 0), (2, 2)]:
            try:
                draw.text((x + adj[0], y + adj[1]), text, 
                         fill='black', font=font, anchor='mm')
            except:
                pass
        
        # 메인 텍스트
        try:
            draw.text((x, y), text, fill=color, font=font, anchor='mm')
        except:
            draw.text((x, y), text, fill=color, font=font)
    
    return background.convert('RGB')

# 스타일 C: 듀얼 톤
def create_meme_card_dualtone(dna_type_name, dna_data):
    """듀얼 톤 스타일 - 컬러 필터 (보라+핑크)"""
    width, height = 1080, 1080
    
    # 배경
    video_path = f"videos/{dna_data['video_file']}"
    background = capture_video_frame(video_path, frame_position=0.5)
    
    if background:
        bg_width, bg_height = background.size
        if bg_width > bg_height:
            left = (bg_width - bg_height) // 2
            background = background.crop((left, 0, left + bg_height, bg_height))
        else:
            top = (bg_height - bg_width) // 2
            background = background.crop((0, top, bg_width, top + bg_width))
        background = background.resize((width, height), Image.Resampling.LANCZOS)
    else:
        background = Image.new('RGB', (width, height), color=dna_data['color'])
    
    background = background.convert('RGBA')
    
    # 듀얼 톤 오버레이 (보라색 + 핑크색 그라데이션)
    for y in range(height):
        ratio = y / height
        r = int(138 + (255 - 138) * ratio)  # 138 -> 255
        g = int(43 + (105 - 43) * ratio)    # 43 -> 105
        b = int(226 + (180 - 226) * ratio)  # 226 -> 180
        overlay_line = Image.new('RGBA', (width, 1), (r, g, b, 100))
        background.paste(overlay_line, (0, y), overlay_line)
    
    draw = ImageDraw.Draw(background)
    
    # 폰트
    try:
        title_font = ImageFont.truetype("malgun.ttf", 90)
        subtitle_font = ImageFont.truetype("malgun.ttf", 60)
        hashtag_font = ImageFont.truetype("malgun.ttf", 45)
    except:
        title_font = subtitle_font = hashtag_font = ImageFont.load_default()
    
    texts = [
        {"text": f"나는 {dna_type_name}!", "font": title_font, "y": 150},
        {"text": f"{dna_data['emoji']} {dna_data['title']}", "font": subtitle_font, "y": 250},
        {"text": "#춤마루 #K_DNA각성", "font": hashtag_font, "y": 900}
    ]
    
    for text_info in texts:
        x, y = width//2, text_info["y"]
        text = text_info["text"]
        font = text_info["font"]
        
        # 외곽선
        for adj in [(-4, -4), (-4, 0), (-4, 4), (0, -4), (0, 4), (4, -4), (4, 0), (4, 4)]:
            try:
                draw.text((x + adj[0], y + adj[1]), text, fill='black', font=font, anchor='mm')
            except:
                pass
        
        try:
            draw.text((x, y), text, fill='white', font=font, anchor='mm')
        except:
            draw.text((x, y), text, fill='white', font=font)
    
    return background.convert('RGB')

# 스타일 D: 미니멀
def create_meme_card_minimal(dna_type_name, dna_data):
    """미니멀 스타일 - 심플하고 깔끔하게"""
    width, height = 1080, 1080
    
    # 배경
    video_path = f"videos/{dna_data['video_file']}"
    background = capture_video_frame(video_path, frame_position=0.5)
    
    if background:
        bg_width, bg_height = background.size
        if bg_width > bg_height:
            left = (bg_width - bg_height) // 2
            background = background.crop((left, 0, left + bg_height, bg_height))
        else:
            top = (bg_height - bg_width) // 2
            background = background.crop((0, top, bg_width, top + bg_width))
        background = background.resize((width, height), Image.Resampling.LANCZOS)
        # 약한 블러 (영상을 더 선명하게)
        background = background.filter(ImageFilter.GaussianBlur(3))
        # 밝기 조정
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.7)
    else:
        background = Image.new('RGB', (width, height), color='#F5F5F5')
    
    background = background.convert('RGBA')
    
    # 반투명 화이트 오버레이 (더 투명하게)
    overlay = Image.new('RGBA', (width, height), (255, 255, 255, 60))
    background = Image.alpha_composite(background, overlay)
    
    draw = ImageDraw.Draw(background)
    
    # 폰트
    try:
        title_font = ImageFont.truetype("malgun.ttf", 75)
        subtitle_font = ImageFont.truetype("malgun.ttf", 52)
        hashtag_font = ImageFont.truetype("malgun.ttf", 38)
    except:
        title_font = subtitle_font = hashtag_font = ImageFont.load_default()
    
    # 텍스트 배치: 제목 위, 해시태그 아래
    texts = [
        {"text": f"나는 {dna_type_name}!", "font": title_font, "y": 120, "align": "center"},
        {"text": f"{dna_data['emoji']} {dna_data['title']}", "font": subtitle_font, "y": 210, "align": "center"},
        {"text": "#춤마루 #K_DNA각성", "font": hashtag_font, "y": 950, "align": "center"}
    ]
    
    for text_info in texts:
        x = width//2
        y = text_info["y"]
        text = text_info["text"]
        font = text_info["font"]
        
        # 부드러운 그림자
        for adj in [(3, 3), (2, 2), (1, 1)]:
            try:
                draw.text((x + adj[0], y + adj[1]), text, 
                         fill='#00000030', font=font, anchor='mm')
            except:
                pass
        
        # 메인 텍스트
        try:
            draw.text((x, y), text, fill='#333333', font=font, anchor='mm')
        except:
            draw.text((x, y), text, fill='#333333', font=font)
    
    return background.convert('RGB')

# GIF 밈 생성 함수
def create_meme_gif(dna_type_name, dna_data, duration=3, fps=10, style='gradient'):
    """
    DNA 영상에서 여러 프레임을 추출해 GIF 생성
    duration: GIF 길이 (초)
    fps: 초당 프레임 수
    style: 'gradient', 'neon', 'dualtone', 'minimal'
    """
    width, height = 1080, 1080
    video_path = f"videos/{dna_data['video_file']}"
    
    # 영상 열기
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    
    # GIF에 사용할 프레임 수
    target_frames = duration * fps
    frames = []
    
    # 폰트 로드
    try:
        title_font = ImageFont.truetype("malgun.ttf", 85)
        subtitle_font = ImageFont.truetype("malgun.ttf", 55)
        hashtag_font = ImageFont.truetype("malgun.ttf", 42)
    except:
        title_font = subtitle_font = hashtag_font = ImageFont.load_default()
    
    # 프레임 추출 및 텍스트 오버레이
    for i in range(target_frames):
        # 영상의 어느 부분을 가져올지 계산 (중간 부분 순환)
        frame_pos = 0.3 + (i / target_frames) * 0.4  # 30%~70% 구간
        frame_number = int(total_frames * frame_pos)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        
        if not ret:
            continue
        
        # BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        
        # 정사각형 크롭
        img_width, img_height = img.size
        if img_width > img_height:
            left = (img_width - img_height) // 2
            img = img.crop((left, 0, left + img_height, img_height))
        else:
            top = (img_height - img_width) // 2
            img = img.crop((0, top, img_width, top + img_width))
        
        # 리사이즈
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # 스타일에 따라 처리
        if style == 'neon':
            # 네온: 어둡고 강렬하게
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.3)  # 더 어둡게
            img = img.filter(ImageFilter.GaussianBlur(3))
            img = img.convert('RGBA')
            # 진한 남색 오버레이
            overlay = Image.new('RGBA', (width, height), (10, 0, 50, 150))
            img = Image.alpha_composite(img, overlay)
            
        elif style == 'dualtone':
            # 듀얼 톤: 강한 컬러 필터
            img = img.convert('RGBA')
            # 전체 이미지에 컬러 필터 적용 (더 빠르고 명확)
            color_overlay = Image.new('RGBA', (width, height))
            pixels = color_overlay.load()
            for y in range(height):
                ratio = y / height
                # 보라색 -> 핑크색 그라데이션 (더 강하게)
                r = int(138 + (255 - 138) * ratio)
                g = int(43 + (105 - 43) * ratio)
                b = int(226 + (180 - 226) * ratio)
                for x in range(width):
                    pixels[x, y] = (r, g, b, 160)  # alpha 160으로 강하게
            img = Image.alpha_composite(img, color_overlay)
            
        elif style == 'minimal':
            # 미니멀: 밝고 깔끔하게
            img = img.filter(ImageFilter.GaussianBlur(5))  # 더 블러
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.8)  # 더 밝게
            img = img.convert('RGBA')
            # 화이트 오버레이 강하게
            overlay = Image.new('RGBA', (width, height), (255, 255, 255, 120))
            img = Image.alpha_composite(img, overlay)
            
        else:  # gradient (기본)
            img = img.filter(ImageFilter.GaussianBlur(1))
            img = img.convert('RGBA')
            # 상단/하단 그라데이션 박스
            top_box_height = 250
            for j in range(top_box_height):
                alpha = int(200 * (1 - j / top_box_height))
                overlay_line = Image.new('RGBA', (width, 1), (0, 0, 0, alpha))
                img.paste(overlay_line, (0, j), overlay_line)
            bottom_box_height = 200
            for j in range(bottom_box_height):
                alpha = int(200 * (j / bottom_box_height))
                overlay_line = Image.new('RGBA', (width, 1), (0, 0, 0, alpha))
                img.paste(overlay_line, (0, height - bottom_box_height + j), overlay_line)
        
        # 텍스트 추가
        draw = ImageDraw.Draw(img)
        
        # 텍스트 위치 (스타일에 따라)
        if style in ['gradient', 'neon', 'dualtone']:
            texts = [
                {"text": f"나는 {dna_type_name}!", "font": title_font, "y": 80},
                {"text": f"{dna_data['emoji']} {dna_data['title']}", "font": subtitle_font, "y": 165},
                {"text": "#춤마루 #K_DNA각성", "font": hashtag_font, "y": height - 100}
            ]
        else:  # minimal
            texts = [
                {"text": f"나는 {dna_type_name}!", "font": title_font, "y": 120},
                {"text": f"{dna_data['emoji']} {dna_data['title']}", "font": subtitle_font, "y": 210},
                {"text": "#춤마루 #K_DNA각성", "font": hashtag_font, "y": 950}
            ]
        
        # 텍스트 그리기 (외곽선 + 메인)
        for text_info in texts:
            x, y = width//2, text_info["y"]
            text = text_info["text"]
            font = text_info["font"]
            
            # 스타일별 텍스트 색상 및 효과
            if style == 'neon':
                # 네온: 형광 색상 + 강한 글로우
                if '춤마루' in text:
                    text_color = '#FF10F0'  # 핑크
                elif '나는' in text:
                    text_color = '#FF10F0'  # 핑크
                else:
                    text_color = '#00FFFF'  # 시안
                
                # 글로우 효과
                for glow in [6, 4, 2]:
                    for adj_x in range(-glow, glow + 1, 2):
                        for adj_y in range(-glow, glow + 1, 2):
                            if adj_x != 0 or adj_y != 0:
                                try:
                                    draw.text((x + adj_x, y + adj_y), text, 
                                            fill=text_color + '40', font=font, anchor='mm')
                                except:
                                    pass
                
                # 검은 외곽선
                for adj in [(-2, -2), (-2, 0), (-2, 2), (0, -2), (0, 2), (2, -2), (2, 0), (2, 2)]:
                    try:
                        draw.text((x + adj[0], y + adj[1]), text, fill='black', font=font, anchor='mm')
                    except:
                        pass
                
            elif style == 'minimal':
                # 미니멀: 검은색 텍스트 + 부드러운 그림자
                text_color = '#222222'
                
                # 그림자
                for adj in [(3, 3), (2, 2)]:
                    try:
                        draw.text((x + adj[0], y + adj[1]), text, 
                                fill='#00000030', font=font, anchor='mm')
                    except:
                        pass
                
            elif style == 'dualtone':
                # 듀얼 톤: 흰색 텍스트 + 검은 외곽선
                text_color = 'white' if '춤마루' not in text else '#FFD700'
                
                # 외곽선
                for adj in [(-3, -3), (-3, 0), (-3, 3), (0, -3), (0, 3), (3, -3), (3, 0), (3, 3)]:
                    try:
                        draw.text((x + adj[0], y + adj[1]), text, fill='black', font=font, anchor='mm')
                    except:
                        pass
                
            else:  # gradient
                # 그라데이션: 흰색 텍스트 + 검은 외곽선 + 골드 해시태그
                text_color = '#FFD700' if '춤마루' in text else 'white'
                
                # 외곽선
                for adj in [(-3, -3), (-3, 0), (-3, 3), (0, -3), (0, 3), (3, -3), (3, 0), (3, 3)]:
                    try:
                        draw.text((x + adj[0], y + adj[1]), text, fill='black', font=font, anchor='mm')
                    except:
                        pass
            
            # 메인 텍스트
            try:
                draw.text((x, y), text, fill=text_color, font=font, anchor='mm')
            except:
                draw.text((x, y), text, fill=text_color, font=font)
        
        # RGB로 변환 후 리스트에 추가
        frames.append(img.convert('RGB'))
    
    cap.release()
    
    if not frames:
        return None
    
    # GIF 생성
    gif_buffer = io.BytesIO()
    frames[0].save(
        gif_buffer,
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / fps),  # ms per frame
        loop=0,  # 무한 반복
        optimize=False  # 최적화 비활성화 (속도 향상)
    )
    
    gif_buffer.seek(0)
    return gif_buffer

# 메인 앱 로직
def main():
    init_session_state()
    
    # 재구성된 사이드바
    with st.sidebar:
        # 최상단: 홈 버튼
        if st.button("🏠 홈으로", type="primary", use_container_width=True):
            st.session_state.current_step = 'landing'
            st.rerun()

        st.markdown("---")

        # 내 K-DNA 깨우기 (테스트 시작)
        if st.button("✨ 내 K-DNA 깨우기", use_container_width=True):
            st.session_state.current_step = 'test'
            st.rerun()

        # DNA 갤러리 메뉴
        if st.button(t('explore_all_dna'), use_container_width=True):
            st.session_state.current_step = 'dna_gallery'
            st.rerun()

        st.markdown("---")

        # 움직임 여정 시작 메뉴
        if st.button(f"💃 {t('movement_journey')}", use_container_width=True):
            st.session_state.current_step = 'action_select'
            st.rerun()

        # 5000년 움직임의 비밀 버튼
        if st.button("📜 5000년 움직임의 비밀", use_container_width=True):
            st.session_state.current_step = 'story'
            st.rerun()

        # 동작 테스트 메뉴
        st.markdown("---")
        st.markdown("### 🎯 동작 테스트")
        if st.button("📹 실시간 자세 감지", use_container_width=True):
            st.session_state.current_step = 'pose_test'
            st.rerun()

        # 전문가 시스템 메뉴
        st.markdown("---")
        st.markdown(f"### 🎭 {t('expert_system')}")

        if st.session_state.expert_logged_in:
            expert = get_experts().get(st.session_state.expert_id, {})
            st.markdown(f"**{expert.get('name', '전문가')}** 님")
            if st.button(t('expert_my_profile'), use_container_width=True):
                st.session_state.current_step = 'expert_profile'
                st.rerun()
            if st.button(t('expert_upload_video'), use_container_width=True):
                st.session_state.current_step = 'expert_upload'
                st.rerun()
            if st.button(t('expert_logout'), use_container_width=True):
                st.session_state.expert_logged_in = False
                st.session_state.expert_id = None
                st.rerun()
        else:
            if st.button(t('expert_login'), use_container_width=True):
                st.session_state.current_step = 'expert_login'
                st.rerun()
            if st.button(t('expert_signup'), use_container_width=True):
                st.session_state.current_step = 'expert_signup'
                st.rerun()

        if st.button(t('expert_gallery'), use_container_width=True):
            st.session_state.current_step = 'expert_gallery'
            st.rerun()
        if st.button(t('expert_ranking'), use_container_width=True):
            st.session_state.current_step = 'expert_ranking'
            st.rerun()

        # B2B 시스템 메뉴
        st.markdown("---")
        st.markdown(f"### 🏢 {t('b2b_system')}")

        if st.session_state.org_logged_in:
            org = get_organizations().get(st.session_state.org_id, {})
            st.markdown(f"**{org.get('name', '단체')}**")
            if st.button(t('org_dashboard'), use_container_width=True):
                st.session_state.current_step = 'org_dashboard'
                st.rerun()
            if st.button(t('subscription_management'), use_container_width=True):
                st.session_state.current_step = 'subscription_management'
                st.rerun()
            if st.button(t('instructor_management'), use_container_width=True):
                st.session_state.current_step = 'instructor_management'
                st.rerun()
            if st.button(t('student_management'), use_container_width=True):
                st.session_state.current_step = 'student_management'
                st.rerun()
            if st.button(t('custom_actions'), use_container_width=True):
                st.session_state.current_step = 'custom_actions_setup'
                st.rerun()
            if st.button(t('org_logout'), use_container_width=True):
                st.session_state.org_logged_in = False
                st.session_state.org_id = None
                st.session_state.user_role = None
                st.rerun()
        else:
            if st.button(t('org_login'), use_container_width=True):
                st.session_state.current_step = 'org_login'
                st.rerun()
            if st.button(t('org_signup'), use_container_width=True):
                st.session_state.current_step = 'org_signup'
                st.rerun()

        # 언어 설정 (최하단)
        st.markdown("---")
        st.markdown("### 🌐 Language / 언어")
        lang_option = st.selectbox(
            "Language / 언어",
            ["🇰🇷 한국어", "🇺🇸 English"],
            index=0 if st.session_state.language == 'ko' else 1,
            key='lang_selector',
            label_visibility="collapsed"
        )

        # 언어 변경 감지
        new_lang = 'ko' if '한국어' in lang_option else 'en'
        if new_lang != st.session_state.language:
            st.session_state.language = new_lang
            st.rerun()
    
    # 헤더
    st.markdown(f"""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #667eea; font-size: 3rem; margin-bottom: 0;'>🎭 {t('app_title')}</h1>
        <p style='color: #666; font-size: 1.2rem;'>{t('app_subtitle')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 단계별 라우팅
    if st.session_state.current_step == 'landing':
        show_landing_page()
    elif st.session_state.current_step == 'test':
        show_test_page()
    elif st.session_state.current_step == 'result':
        show_result_page()
    elif st.session_state.current_step == 'dna_gallery':
        show_dna_gallery_page()
    elif st.session_state.current_step == 'action_select':
        show_action_select_page()
    elif st.session_state.current_step == 'action':
        show_action_page()
    elif st.session_state.current_step == 'expanded_action':
        show_expanded_action_page()
    elif st.session_state.current_step == 'creative_action':
        show_creative_action_page()
    elif st.session_state.current_step == 'story':
        show_story_page()
    elif st.session_state.current_step == 'story_detail':
        show_story_detail_page()
    elif st.session_state.current_step == 'meme':
        show_meme_page()
    elif st.session_state.current_step == 'expert_login':
        show_expert_login_page()
    elif st.session_state.current_step == 'expert_signup':
        show_expert_signup_page()
    elif st.session_state.current_step == 'expert_upload':
        show_expert_upload_page()
    elif st.session_state.current_step == 'expert_profile':
        show_expert_profile_page()
    elif st.session_state.current_step == 'expert_gallery':
        show_expert_gallery_page()
    elif st.session_state.current_step == 'expert_ranking':
        show_expert_ranking_page()
    elif st.session_state.current_step == 'dna_type_gallery':
        show_dna_type_gallery_page()
    elif st.session_state.current_step == 'video_detail':
        show_video_detail_page()
    elif st.session_state.current_step == 'pose_test':
        show_pose_test_page()
    # B2B 페이지 라우팅
    elif st.session_state.current_step == 'org_login':
        show_org_login_page()
    elif st.session_state.current_step == 'org_signup':
        show_org_signup_page()
    elif st.session_state.current_step == 'org_dashboard':
        show_org_dashboard_page()
    elif st.session_state.current_step == 'subscription_management':
        show_subscription_management_page()
    elif st.session_state.current_step == 'instructor_management':
        show_instructor_management_page()
    elif st.session_state.current_step == 'student_management':
        show_student_management_page()
    elif st.session_state.current_step == 'custom_actions_setup':
        show_custom_actions_setup_page()
    elif st.session_state.current_step == 'org_statistics':
        show_org_statistics_page()

def show_landing_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"""
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 20px; color: white; margin: 2rem 0;'>
            <h2>{t('landing_hero')}</h2>
            <p style='font-size: 1.1rem; margin: 1.5rem 0;'>
                {t('landing_desc')}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"### {t('landing_journey')}")
        
        # 여정 단계들
        journey_steps = [
            ("1", t('journey_1_title'), t('journey_1_desc'), "#667eea"),
            ("2", t('journey_2_title'), t('journey_2_desc'), "#4ECDC4"),  
            ("3", t('journey_3_title'), t('journey_3_desc'), "#FFD700"),
            ("4", t('journey_4_title'), t('journey_4_desc'), "#FF69B4")
        ]
        
        for step, title, desc, color in journey_steps:
            st.markdown(f"""
            <div class='journey-step' style='background: linear-gradient(135deg, {color}, {color}dd); margin: 0.5rem 0;'>
                <div style='display: flex; align-items: center;'>
                    <div style='background: rgba(255,255,255,0.3); width: 2rem; height: 2rem; border-radius: 50%; 
                                display: flex; align-items: center; justify-content: center; margin-right: 1rem;
                                font-weight: bold;'>{step}</div>
                    <div>
                        <div style='font-weight: bold; margin-bottom: 0.2rem;'>{title}</div>
                        <div style='font-size: 0.8rem; opacity: 0.9;'>{desc}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button(t('landing_start'), type="primary"):
            st.session_state.current_step = 'test'
            st.rerun()
        
        st.info(t('landing_stats'))
        
        # 전문가 시스템 소개
        st.markdown("---")
        st.markdown(f"""
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%); 
                    border-radius: 20px; color: white; margin: 2rem 0;'>
            <h2>🎭 전문가와 함께하는 춤마루</h2>
            <p style='font-size: 1.1rem; margin: 1.5rem 0;'>
                8가지 DNA 타입별로 전문가들의 영상을 만나보고,<br>
                피드백을 주고받으며 디지털 평판을 쌓아가세요
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("전문가 갤러리 보기", type="primary", use_container_width=True):
                st.session_state.current_step = 'expert_gallery'
                st.rerun()
        with col2:
            if st.button("전문가 랭킹 보기", type="primary", use_container_width=True):
                st.session_state.current_step = 'expert_ranking'
                st.rerun()

def show_test_page():
    # 현재 언어에 맞는 질문 가져오기
    questions = get_questions(st.session_state.language)
    
    if st.session_state.current_question >= len(questions):
        # 결과 분석
        st.session_state.dna_result = analyze_dna(st.session_state.answers)
        st.session_state.current_step = 'result'
        st.rerun()
        return
    
    progress = (st.session_state.current_question + 1) / len(questions)
    st.progress(progress, text=f"{t('progress')}: {int(progress*100)}% ({st.session_state.current_question + 1}/10)")
    
    # 이전 버튼
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button(t('btn_prev')):
            if st.session_state.current_question > 0:
                st.session_state.current_question -= 1
                st.session_state.answers.pop()
                st.rerun()
            else:
                st.session_state.current_step = 'landing'
                st.rerun()
    
    # 질문 표시
    question = questions[st.session_state.current_question]
    
    st.markdown(f"### {t('question')} {question['id']}/10")
    st.markdown(f"**{question['text']}**")
    
    # 선택지
    selected_option = st.radio(
        t('select_answer'),
        options=list(question['options'].keys()),
        format_func=lambda x: question['options'][x],
        key=f"q_{question['id']}"
    )
    
    if st.button(t('btn_next'), type="primary"):
        st.session_state.answers.append(selected_option)
        st.session_state.current_question += 1
        st.rerun()
    
    # 진행 상황 표시
    if st.session_state.current_question >= 4:
        st.success(t('dna_forming'))

def show_result_page():
    if not st.session_state.dna_result:
        st.error("DNA 분석 결과가 없습니다.")
        return
    
    # 현재 언어에 맞는 DNA 타입 데이터 가져오기
    lang = st.session_state.language
    dna_types = get_dna_types(lang)
    dna_type_name = get_dna_type_name(st.session_state.dna_result, lang)
    dna_data = dna_types[dna_type_name]
    
    # 뒤로가기 버튼
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button(t('btn_prev')):
            st.session_state.current_step = 'test'
            st.session_state.current_question = len(questions) - 1
            st.rerun()
    with col3:
        if st.button(t('btn_home')):
            st.session_state.current_step = 'landing'
            st.rerun()
    
    # 결과 카드
    st.markdown(f"""
    <div class='dna-card' style='background: linear-gradient(135deg, {dna_data['color']}, {dna_data['color']}dd);'>
        <div style='font-size: 4rem; margin-bottom: 1rem;'>{dna_data['emoji']}</div>
        <h1>{t('your_dna')}</h1>
        <h2 style='background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 20px; margin: 1rem 0;'>
            {dna_type_name}
        </h2>
        <h3>{dna_data['title']}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 설명
    st.markdown(f"**{dna_data['description']}**")
    
    # 특징 태그
    st.markdown(f"### {t('your_traits')}")
    cols = st.columns(len(dna_data['characteristics']))
    for i, char in enumerate(dna_data['characteristics']):
        with cols[i]:
            st.markdown(f"<div style='background: {dna_data['color']}20; color: {dna_data['color']}; "
                       f"padding: 0.5rem; border-radius: 10px; text-align: center; font-weight: bold;'>"
                       f"{char}</div>", unsafe_allow_html=True)
    
    # 전문가 영상
    st.markdown(f"### {t('expert_video')}")
    
    # 기본 영상 파일이 있다면 표시
    video_path = f"videos/{dna_data['video_file']}"
    try:
        st.video(video_path)
    except:
        st.info(f"{st.session_state.dna_result} 타입 기본 시연 영상")
    
    # DNA 타입별 전문가 업로드 영상
    videos = get_videos()
    dna_videos = [v for v in videos.values() if v.get('dna_type') == dna_type_name]
    
    if dna_videos:
        st.markdown("---")
        st.markdown(f"### 🎭 {dna_type_name} 전문가 영상 ({len(dna_videos)}개)")
        cols = st.columns(min(3, len(dna_videos)))
        for i, video in enumerate(sorted(dna_videos, key=lambda x: x.get('created_at', ''), reverse=True)[:3]):
            with cols[i % 3]:
                try:
                    st.video(video.get('video_path'))
                except:
                    st.info("영상 로드 중...")
                st.markdown(f"**{video.get('title', '')}**")
                expert = get_experts().get(video.get('expert_id', ''), {})
                st.markdown(f"👤 {expert.get('name', '전문가')}")
                if st.button(f"보기", key=f"result_{video['id']}"):
                    st.session_state.viewing_video_id = video['id']
                    st.session_state.current_step = 'video_detail'
                    st.rerun()
        
        if len(dna_videos) > 3:
            if st.button(f"{dna_type_name} 전문가 영상 더 보기"):
                st.session_state.current_step = 'dna_type_gallery'
                st.rerun()
    else:
        st.info(f"{dna_type_name} 타입의 전문가 영상이 아직 없습니다. 전문가가 되어 첫 영상을 업로드해보세요!")
    
    # 다른 DNA 타입도 보기
    st.markdown("---")
    with st.expander(t('other_dna_types')):
        st.markdown(t('dna_gallery_subtitle'))
        
        # 현재 DNA 타입을 제외한 나머지 7개 타입 표시
        other_types = [name for name in dna_types.keys() if name != dna_type_name]
        
        # 2개씩 컬럼으로 표시
        for i in range(0, len(other_types), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j < len(other_types):
                    other_name = other_types[i + j]
                    other_data = dna_types[other_name]
                    
                    with col:
                        st.markdown(f"""
                        <div style='background: linear-gradient(135deg, {other_data['color']}, {other_data['color']}dd);
                                    padding: 1rem; border-radius: 10px; color: white; text-align: center;
                                    margin-bottom: 0.5rem;'>
                            <div style='font-size: 2rem;'>{other_data['emoji']}</div>
                            <h4 style='margin: 0.3rem 0;'>{other_name}</h4>
                            <p style='font-size: 0.8rem; margin: 0;'>{other_data['title']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(f"*{other_data['description'][:80]}...*")
                        st.markdown("")
        
        # 전체 갤러리 보기 버튼
        if st.button(t('view_all_gallery'), type="secondary", use_container_width=True):
            st.session_state.current_step = 'dna_gallery'
            st.rerun()
    
    # 액션 버튼
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t('start_movement'), type="primary"):
            st.session_state.current_step = 'action_select'
            st.rerun()
    
    with col2:
        if st.button(t('share_result')):
            st.session_state.current_step = 'meme'
            st.rerun()

def show_action_select_page():
    # 뒤로가기 버튼
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button(t('btn_prev')):
            st.session_state.current_step = 'result'
            st.rerun()
    with col3:
        if st.button(t('btn_home')):
            st.session_state.current_step = 'landing'
            st.rerun()
    
    st.markdown(f"## {t('movement_journey')}")
    st.markdown(t('movement_subtitle'))
    
    # 기본 동작 선택
    with st.container():
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 15px; color: white; margin: 1rem 0;'>
            <h3>{t('basic_actions')} (12)</h3>
            <p>{t('basic_actions_desc')}</p>
            <small>✓ {t('ai_support')} • {t('special_meme')}</small>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(t('start_basic'), type="primary"):
            st.session_state.current_step = 'action'
            st.rerun()
    
    # 확장 동작 선택
    with st.container():
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%); 
                    padding: 2rem; border-radius: 15px; color: white; margin: 1rem 0;'>
            <h3>{t('expanded_actions')} (6)</h3>
            <p>{t('expanded_actions_desc')}</p>
            <small>✓ {t('expert_video')} • {t('ai_coming')}</small>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(t('try_expanded'), key="expanded_btn"):
            st.session_state.current_step = 'expanded_action'
            st.rerun()

    # 창작 동작 선택
    with st.container():
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%); 
                    padding: 2rem; border-radius: 15px; color: white; margin: 1rem 0;'>
            <h3>{t('creative_actions')} (8)</h3>
            <p>{t('creative_actions_desc')}</p>
            <small>✓ {t('expert_video')} • {t('ai_coming')}</small>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(t('try_creative'), key="creative_btn"):
            st.session_state.current_step = 'creative_action'
            st.rerun()
            
    # 스토리 보기 버튼
    if st.button(t('see_story')):
        st.session_state.current_step = 'story'
        st.rerun()

def show_action_page():
    """
    기본 동작 배우기 페이지 (WebRTC 기반)
    - 전문가 영상: st.video()로 재생 (스켈레톤은 미리 처리된 영상 사용)
    - 사용자 카메라: WebRTC로 브라우저 카메라 접근 (Streamlit Cloud 호환)
    - 자세 비교: 미리 추출된 전문가 랜드마크와 비교
    """
    # 현재 언어에 맞는 기본 동작 가져오기
    basic_actions = get_basic_actions(st.session_state.language)

    if st.session_state.current_action >= len(basic_actions):
        st.session_state.current_step = 'meme'
        st.rerun()
        return

    action = basic_actions[st.session_state.current_action]
    progress = (st.session_state.current_action + 1) / len(basic_actions)

    # 헤더
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button(t('btn_prev')):
            if st.session_state.current_action > 0:
                st.session_state.current_action -= 1
            else:
                st.session_state.current_step = 'action_select'
            st.rerun()

    with col2:
        st.markdown(f"### {action['name']} ({st.session_state.current_action + 1}/12)")
        st.progress(progress, text=f"{t('progress')}: {int(progress*100)}%")

    with col3:
        if st.button(t('btn_home')):
            st.session_state.current_step = 'landing'
            st.rerun()

    # 동작 설명
    st.markdown(f"""
    <div class='action-card'>
        <h3>{action['description']}</h3>
        <p style='font-style: italic; margin: 1rem 0;'>"{action['story_card']}"</p>
        <small>💡 {action['historical_note']}</small>
    </div>
    """, unsafe_allow_html=True)

    # 세션 상태 초기화
    if 'action_webcam_running' not in st.session_state:
        st.session_state.action_webcam_running = False
    if 'comparison_score' not in st.session_state:
        st.session_state.comparison_score = 0
    if 'comparison_feedback' not in st.session_state:
        st.session_state.comparison_feedback = []
    if 'joint_coverage_percent' not in st.session_state:
        st.session_state.joint_coverage_percent = 0

    # 영상 파일 경로
    video_path = f"videos/{action['video_file']}"
    video_filename = action['video_file']
    video_name = os.path.splitext(os.path.basename(video_filename))[0]

    # 전문가 랜드마크 JSON 경로
    landmarks_json_path = f"data/expert_landmarks/{video_name}_landmarks.json"
    processed_video_path = f"videos/processed/skeleton_{video_filename}"

    # 전문가 랜드마크 로드 (미리 처리된 경우)
    expert_reference_landmarks = None
    if os.path.exists(landmarks_json_path):
        expert_reference_landmarks = load_expert_landmarks(landmarks_json_path)
        if expert_reference_landmarks:
            st.success(f"✅ 전문가 자세 데이터 로드 완료 - 실시간 비교 가능")

    # 2열 레이아웃: 전문가 | 사용자
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"#### {t('expert_demo')}")
        # 전문가 영상 표시 (스켈레톤 처리된 영상 또는 원본)
        if os.path.exists(processed_video_path):
            st.video(processed_video_path, loop=True, autoplay=True, muted=True)
        elif os.path.exists(video_path):
            st.video(video_path, loop=True, autoplay=True, muted=True)
        else:
            st.info(f"{action['name']} 시범 영상 - 업로드 예정")

        # 피드백 표시 영역
        feedback_placeholder = st.empty()

    with col2:
        st.markdown(f"#### {t('your_movement')}")

        # 캐시된 MediaPipe 사용
        user_pose_landmarker = get_pose_landmarker(0.5, 0.5)
        user_hand_landmarker = get_hand_landmarker(0.5, 0.5)

        # WebRTC 비디오 프레임 콜백 함수
        def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="rgb24")
            img = cv2.flip(img, 1)

            try:
                import time
                timestamp_ms = int(time.time() * 1000)

                user_mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img)
                user_result = user_pose_landmarker.detect_for_video(user_mp_image, timestamp_ms)

                if user_result.pose_landmarks:
                    img = draw_landmarks_on_image(img, user_result)

                    if expert_reference_landmarks:
                        try:
                            comparison_result = compare_poses(user_result.pose_landmarks[0], expert_reference_landmarks)
                            score = comparison_result['overall_score']
                            color = (0, 255, 0) if score >= 80 else (255, 165, 0) if score >= 60 else (255, 0, 0)
                            cv2.putText(img, f'Score: {score}%', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                            update_webrtc_state('action_page', {
                                'feedback_score': score,
                                'feedback_messages': comparison_result['feedback'],
                                'joint_coverage': comparison_result.get('joint_coverage_percent', 100),
                                'pose_detected': True,
                                                            })
                        except Exception as e:
                            print(f"[compare_poses error] {e}")
                            update_webrtc_state('action_page', {'pose_detected': True, })
                    else:
                        cv2.putText(img, 'Pose OK (no expert)', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        update_webrtc_state('action_page', {'pose_detected': True, })
                else:
                    cv2.putText(img, 'No pose detected', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
                    update_webrtc_state('action_page', {'pose_detected': False, 'feedback_score': 0, })

                hand_result = user_hand_landmarker.detect_for_video(user_mp_image, timestamp_ms)
                if hand_result.hand_landmarks:
                    img = draw_hands_on_image(img, hand_result)

            except Exception as e:
                import traceback
                traceback.print_exc()
                cv2.putText(img, f'Error: {str(e)[:40]}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            return av.VideoFrame.from_ndarray(img, format="rgb24")

        # WebRTC 스트리머 설정
        webrtc_ctx = webrtc_streamer(
            key="user_camera_action",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}),
            video_frame_callback=video_frame_callback,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

    # 피드백 업데이트
    if webrtc_ctx.state.playing:
        st.session_state.action_webcam_running = True
        st_autorefresh(interval=1000, key="feedback_refresh")

        state = get_webrtc_state('action_page')
        score = state.get('feedback_score', 0)
        feedback_messages = state.get('feedback_messages', [])
        coverage = state.get('joint_coverage', 0)

        if expert_reference_landmarks and score > 0:
            score_color = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
            feedback_text = f"**{score_color} {score:.0f}점, 관절 감지: {coverage}%**\n\n"
            if feedback_messages:
                for fb in feedback_messages[:3]:
                    feedback_text += f"{fb}\n\n"
            feedback_placeholder.markdown(feedback_text)
            st.session_state.comparison_score = score
        elif state.get('pose_detected', False):
            feedback_placeholder.success("✅ 자세 감지 중...")
        else:
            feedback_placeholder.warning("⏳ 카메라 앞에 서주세요")
    else:
        st.session_state.action_webcam_running = False
        reset_webrtc_state('action_page')

    # 전문가 영상 처리 버튼 (JSON이 없는 경우만 표시)
    if not os.path.exists(landmarks_json_path) and os.path.exists(video_path):
        st.markdown("---")
        st.warning("⚠️ 전문가 자세 데이터가 없습니다. 자세 비교 기능을 사용하려면 영상을 처리해주세요.")
        if st.button("🔄 전문가 영상 처리 (스켈레톤 + 랜드마크 추출)", key="process_expert"):
            with st.spinner("전문가 영상 처리 중... (1-2분 소요)"):
                processed_path, landmarks_path = process_expert_video_with_skeleton(video_path)
                if processed_path and landmarks_path:
                    st.success("✅ 처리 완료! 페이지를 새로고침하세요.")
                    st.rerun()
                else:
                    st.error("❌ 처리 실패. 콘솔 로그를 확인하세요.")

    # 완료 조건 체크 (점수 80점 이상)
    if st.session_state.comparison_score >= 80:
        if st.session_state.current_action not in st.session_state.completed_actions:
            st.session_state.completed_actions.append(st.session_state.current_action)
            st.success(f"✅ {action['name']} 동작을 완료했습니다!")
            st.balloons()

    # 세부 영상 표시
    if 'detail_videos' in action:
        render_detail_videos(action['detail_videos'], video_path)

    # 다음 동작으로 이동 버튼
    st.markdown("---")
    if st.button(t('action_complete_manual'), help=t('ai_judgement')):
        if st.session_state.current_action not in st.session_state.completed_actions:
            st.session_state.completed_actions.append(st.session_state.current_action)

        st.session_state.current_action += 1
        st.session_state.action_webcam_running = False
        if st.session_state.current_action >= len(basic_actions):
            st.session_state.current_step = 'meme'
        st.rerun()

    # 배지 체크
    completed_count = len(st.session_state.completed_actions)
    badge_system = get_badge_system(st.session_state.language)
    if completed_count in badge_system and completed_count not in st.session_state.badges:
        badge = badge_system[completed_count]
        st.session_state.badges.append(completed_count)
        st.success(f"{badge['emoji']} {badge['name']} {t('badge_earned')} {badge['message']}")

def show_expanded_action_page():
    # 현재 언어에 맞는 확장 동작 가져오기
    expanded_actions = get_expanded_actions(st.session_state.language)
    
    if st.session_state.current_expanded_action >= len(expanded_actions):
        st.success(t('all_complete'))
        if st.button(t('back_to_select'), type="primary"):
            st.session_state.current_step = 'action_select'
            st.rerun()
        return
    
    action = expanded_actions[st.session_state.current_expanded_action]
    progress = (st.session_state.current_expanded_action + 1) / len(expanded_actions)
    
    # 헤더
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button(t('btn_prev')):
            if st.session_state.current_expanded_action > 0:
                st.session_state.current_expanded_action -= 1
            else:
                st.session_state.current_step = 'action_select'
            st.rerun()
    
    with col2:
        st.markdown(f"### {action['name']} ({st.session_state.current_expanded_action + 1}/6)")
        st.progress(progress, text=f"{t('progress')}: {int(progress*100)}%")
    
    with col3:
        if st.button(t('btn_home')):
            st.session_state.current_step = 'landing'
            st.rerun()
    
    # 동작 설명
    st.markdown(f"""
    <div class='action-card'>
        <h3>{action['description']}</h3>
        <p style='font-style: italic; margin: 1rem 0;'>"{action['story_card']}"</p>
        <small>💡 {action['historical_note']}</small>
    </div>
    """, unsafe_allow_html=True)
    
    # 영상과 웹캠
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"#### {t('expert_demo')}")
        video_path = f"videos/{action['video_file']}"
        try:
            st.video(video_path)
        except:
            st.info(f"{action['name']} 시범 영상 - 업로드 예정")
            st.image("https://via.placeholder.com/320x240/4ECDC4/ffffff?text=시범+영상", 
                    caption=f"{action['name']} 전문가 시연")
    
    with col2:
        st.markdown(f"#### {t('your_movement')}")
        
        # 웹캠 입력
        camera_input = st.camera_input(t('webcam_guide'))
        
        if camera_input is not None:
            # 이미지 처리
            image = Image.open(camera_input)
            image_np = np.array(image)
            
            # MediaPipe로 동작 분석
            pose, mp_pose = init_mediapipe()
            
            # RGB 변환
            rgb_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)

            # 좌우 반전 (거울 효과)
            rgb_image = cv2.flip(rgb_image, 1)

            results = pose.process(rgb_image)
            
            if results.pose_landmarks:
                # 동작 분석
                analysis_result = analyze_movement(results.pose_landmarks, action['name'])
                
                if analysis_result['success']:
                    st.success(f"✅ {analysis_result['message']}")
                    st.balloons()
                    
                    # 다음 동작으로
                    time.sleep(2)
                    st.session_state.current_expanded_action += 1
                    st.rerun()
                else:
                    st.warning(f"⚠️ {analysis_result['message']}")
            else:
                st.info("자세를 인식할 수 없습니다. 전신이 보이도록 해주세요.")
    
    # 세부 영상 표시
    if 'detail_videos' in action:
        render_detail_videos(action['detail_videos'], video_path)
    
    # 수동 진행 버튼 (테스트용)
    if st.button(t('action_complete_manual'), help=t('ai_judgement')):
        st.session_state.current_expanded_action += 1
        st.rerun()

def show_creative_action_page():
    # 현재 언어에 맞는 창작 동작 가져오기
    creative_actions = get_creative_actions(st.session_state.language)
    
    if st.session_state.current_creative_action >= len(creative_actions):
        st.success(t('all_complete'))
        if st.button(t('back_to_select'), type="primary"):
            st.session_state.current_step = 'action_select'
            st.rerun()
        return
    
    action = creative_actions[st.session_state.current_creative_action]
    progress = (st.session_state.current_creative_action + 1) / len(creative_actions)
    
    # 헤더
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button(t('btn_prev')):
            if st.session_state.current_creative_action > 0:
                st.session_state.current_creative_action -= 1
            else:
                st.session_state.current_step = 'action_select'
            st.rerun()
    
    with col2:
        st.markdown(f"### {action['name']} ({st.session_state.current_creative_action + 1}/8)")
        st.progress(progress, text=f"{t('progress')}: {int(progress*100)}%")
    
    with col3:
        if st.button(t('btn_home')):
            st.session_state.current_step = 'landing'
            st.rerun()
    
    # 동작 설명
    st.markdown(f"""
    <div class='action-card'>
        <h3>{action['description']}</h3>
        <p style='font-style: italic; margin: 1rem 0;'>"{action['story_card']}"</p>
        <small>💡 {action['historical_note']}</small>
    </div>
    """, unsafe_allow_html=True)
    
    # 영상과 웹캠
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 전문가 시범")
        video_path = f"videos/{action['video_file']}"
        try:
            st.video(video_path)
        except:
            st.info(f"{action['name']} 시범 영상 - 업로드 예정")
            st.image("https://via.placeholder.com/320x240/FF6B35/ffffff?text=시범+영상", 
                    caption=f"{action['name']} 창작 시연")
    
    with col2:
        st.markdown(f"#### {t('your_movement')}")
        
        # 웹캠 입력
        camera_input = st.camera_input(t('webcam_guide'))
        
        if camera_input is not None:
            # 이미지 처리
            image = Image.open(camera_input)
            image_np = np.array(image)
            
            # MediaPipe로 동작 분석
            pose, mp_pose = init_mediapipe()
            
            # RGB 변환
            rgb_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)

            # 좌우 반전 (거울 효과)
            rgb_image = cv2.flip(rgb_image, 1)

            results = pose.process(rgb_image)
            
            if results.pose_landmarks:
                # 동작 분석
                analysis_result = analyze_movement(results.pose_landmarks, action['name'])
                
                if analysis_result['success']:
                    st.success(f"✅ {analysis_result['message']}")
                    st.balloons()
                    
                    # 다음 동작으로
                    time.sleep(2)
                    st.session_state.current_creative_action += 1
                    st.rerun()
                else:
                    st.warning(f"⚠️ {analysis_result['message']}")
            else:
                st.info("자세를 인식할 수 없습니다. 전신이 보이도록 해주세요.")
    
    # 세부 영상 표시
    if 'detail_videos' in action:
        render_detail_videos(action['detail_videos'], video_path)
    
    # 수동 진행 버튼 (테스트용)
    if st.button(t('action_complete_manual'), help=t('ai_judgement')):
        st.session_state.current_creative_action += 1
        st.rerun()

def show_dna_gallery_page():
    """DNA 갤러리 페이지 - 8가지 DNA 타입을 모두 보여줌"""
    # 뒤로가기 버튼
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button(t('btn_prev')):
            # 이전 페이지 추적 (result나 landing으로 돌아가기)
            if st.session_state.dna_result:
                st.session_state.current_step = 'result'
            else:
                st.session_state.current_step = 'landing'
            st.rerun()
    with col3:
        if st.button(t('btn_home')):
            st.session_state.current_step = 'landing'
            st.rerun()
    
    # 페이지 헤더
    st.markdown(f"## {t('dna_gallery_title')}")
    st.markdown(t('dna_gallery_subtitle'))
    st.markdown("---")
    
    # 현재 언어에 맞는 DNA 타입 데이터 가져오기
    lang = st.session_state.language
    dna_types = get_dna_types(lang)
    
    # 8가지 DNA 타입을 2개씩 3행으로 배치 (마지막 행은 4개)
    dna_type_names = list(dna_types.keys())
    
    # 첫 번째 행 (2개)
    cols = st.columns(2)
    for i in range(2):
        if i < len(dna_type_names):
            dna_name = dna_type_names[i]
            dna_data = dna_types[dna_name]
            
            with cols[i]:
                # DNA 타입 카드
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, {dna_data['color']}, {dna_data['color']}dd);
                            padding: 1.5rem; border-radius: 15px; color: white; text-align: center;
                            margin-bottom: 1rem; min-height: 150px;'>
                    <div style='font-size: 3rem; margin-bottom: 0.5rem;'>{dna_data['emoji']}</div>
                    <h3 style='margin: 0.5rem 0;'>{dna_name}</h3>
                    <p style='font-size: 0.9rem; margin: 0;'>{dna_data['title']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 특징 표시
                st.markdown(f"**{t('your_traits')}**")
                for char in dna_data['characteristics']:
                    st.markdown(f"- {char}")
                
                # 설명
                with st.expander(t('view_detail')):
                    st.markdown(dna_data['description'])
                
                # 영상
                video_path = f"videos/{dna_data['video_file']}"
                try:
                    st.video(video_path)
                except:
                    st.info(f"{t('expert_video')} - {t('coming_soon')}")
                
                st.markdown("---")
    
    # 두 번째 행 (2개)
    cols = st.columns(2)
    for i in range(2, 4):
        if i < len(dna_type_names):
            dna_name = dna_type_names[i]
            dna_data = dna_types[dna_name]
            
            with cols[i-2]:
                # DNA 타입 카드
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, {dna_data['color']}, {dna_data['color']}dd);
                            padding: 1.5rem; border-radius: 15px; color: white; text-align: center;
                            margin-bottom: 1rem; min-height: 150px;'>
                    <div style='font-size: 3rem; margin-bottom: 0.5rem;'>{dna_data['emoji']}</div>
                    <h3 style='margin: 0.5rem 0;'>{dna_name}</h3>
                    <p style='font-size: 0.9rem; margin: 0;'>{dna_data['title']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 특징 표시
                st.markdown(f"**{t('your_traits')}**")
                for char in dna_data['characteristics']:
                    st.markdown(f"- {char}")
                
                # 설명
                with st.expander(t('view_detail')):
                    st.markdown(dna_data['description'])
                
                # 영상
                video_path = f"videos/{dna_data['video_file']}"
                try:
                    st.video(video_path)
                except:
                    st.info(f"{t('expert_video')} - {t('coming_soon')}")
                
                st.markdown("---")
    
    # 세 번째 행 (2개)
    cols = st.columns(2)
    for i in range(4, 6):
        if i < len(dna_type_names):
            dna_name = dna_type_names[i]
            dna_data = dna_types[dna_name]
            
            with cols[i-4]:
                # DNA 타입 카드
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, {dna_data['color']}, {dna_data['color']}dd);
                            padding: 1.5rem; border-radius: 15px; color: white; text-align: center;
                            margin-bottom: 1rem; min-height: 150px;'>
                    <div style='font-size: 3rem; margin-bottom: 0.5rem;'>{dna_data['emoji']}</div>
                    <h3 style='margin: 0.5rem 0;'>{dna_name}</h3>
                    <p style='font-size: 0.9rem; margin: 0;'>{dna_data['title']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 특징 표시
                st.markdown(f"**{t('your_traits')}**")
                for char in dna_data['characteristics']:
                    st.markdown(f"- {char}")
                
                # 설명
                with st.expander(t('view_detail')):
                    st.markdown(dna_data['description'])
                
                # 영상
                video_path = f"videos/{dna_data['video_file']}"
                try:
                    st.video(video_path)
                except:
                    st.info(f"{t('expert_video')} - {t('coming_soon')}")
                
                st.markdown("---")
    
    # 네 번째 행 (2개)
    cols = st.columns(2)
    for i in range(6, 8):
        if i < len(dna_type_names):
            dna_name = dna_type_names[i]
            dna_data = dna_types[dna_name]
            
            with cols[i-6]:
                # DNA 타입 카드
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, {dna_data['color']}, {dna_data['color']}dd);
                            padding: 1.5rem; border-radius: 15px; color: white; text-align: center;
                            margin-bottom: 1rem; min-height: 150px;'>
                    <div style='font-size: 3rem; margin-bottom: 0.5rem;'>{dna_data['emoji']}</div>
                    <h3 style='margin: 0.5rem 0;'>{dna_name}</h3>
                    <p style='font-size: 0.9rem; margin: 0;'>{dna_data['title']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 특징 표시
                st.markdown(f"**{t('your_traits')}**")
                for char in dna_data['characteristics']:
                    st.markdown(f"- {char}")
                
                # 설명
                with st.expander(t('view_detail')):
                    st.markdown(dna_data['description'])
                
                # 영상
                video_path = f"videos/{dna_data['video_file']}"
                try:
                    st.video(video_path)
                except:
                    st.info(f"{t('expert_video')} - {t('coming_soon')}")
                
                st.markdown("---")
    
    # 하단 액션 버튼
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t('landing_start'), type="primary", use_container_width=True):
            st.session_state.current_step = 'test'
            st.rerun()
    with col2:
        if st.button(t('see_story'), use_container_width=True):
            st.session_state.current_step = 'story'
            st.rerun()

def show_story_page():
    # 현재 언어에 맞는 스토리 가져오기
    story_contents = get_story_contents(st.session_state.language)
    
    # 뒤로가기 버튼
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button(t('btn_prev')):
            st.session_state.current_step = 'action_select'
            st.rerun()
    with col3:
        if st.button(t('btn_home')):
            st.session_state.current_step = 'landing'
            st.rerun()
    
    st.markdown(f"## {t('story_title')}")
    st.markdown(t('story_subtitle'))
    
    # 스토리 목록
    for index, story in enumerate(story_contents):
        with st.expander(f"{story['avatar']} {story['title']}", expanded=False):
            st.markdown(story['content'])
            
            if story.get('historical_note'):
                st.info(f"**{t('historical_background')}**: {story['historical_note']}")
            
            if st.button(t('view_detail'), key=f"story_{index}"):
                st.session_state.current_story = index
                st.session_state.current_step = 'story_detail'
                st.rerun()
    
    # 전통무용 아카이브 섹션
    st.markdown("---")
    st.markdown(f"## {t('traditional_archive_title')}")
    st.markdown(t('traditional_archive_subtitle'))
    
    # Placeholder 안내
    st.info(f"""
    💡 **{t('coming_soon')}**
    
    {t('archive_desc')}
    
    이 섹션은 다음과 같은 콘텐츠로 채워질 예정입니다:
    - 🏰 궁중의 비밀 - 왕실이 춤춘 이유
    - 🎭 민초의 신명 - 억압 속에서 피어난 춤
    - 🙏 신을 부르는 몸짓 - 종교와 춤의 만남
    - ⚔️ 금지된 춤의 부활 - 잊혀질 뻔한 동작들
    - 👘 한복과 춤의 공생 - 옷이 만든 움직임
    - 🎤 K-pop이 훔쳐간 동작 - 전통이 살아있는 현장
    
    각 섹션에는 관련 전통무용 영상과 스토리가 함께 제공됩니다.
    """)
    
    # 샘플 구조 (향후 콘텐츠로 대체 예정)
    with st.expander("📺 영상 섹션 구조 미리보기 (개발용)", expanded=False):
        st.markdown("""
        ### 구조 예시
        
        각 테마별로 다음과 같은 구조를 가집니다:
        
        1. **테마 제목** (예: 🏰 궁중의 비밀)
        2. **짧은 스토리** (100-200자)
        3. **관련 동작 영상** (basic-actions, expanded-actions, creative-actions 폴더)
        4. **현대 연결고리** (K-pop, 현대 문화와의 연결)
        5. **역사적 배경** (심화 학습)
        
        ### 영상 탑재 방식
        - videos/basic-actions/ (12개 영상)
        - videos/expanded-actions/ (6개 영상)
        - videos/creative-actions/ (8개 영상)
        
        이 영상들을 테마에 맞게 재배치하여 스토리텔링과 함께 제공합니다.
        """)
    
    st.markdown("---")
    
    # 체험하기 버튼
    if st.button(t('try_now'), type="primary"):
        st.session_state.current_step = 'action_select'
        st.rerun()

def show_story_detail_page():
    # 현재 언어에 맞는 스토리 가져오기
    story_contents = get_story_contents(st.session_state.language)
    story = story_contents[st.session_state.current_story]
    
    # 뒤로가기 버튼
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← 목록으로"):
            st.session_state.current_step = 'story'
            st.rerun()
    with col3:
        if st.button(t('btn_home')):
            st.session_state.current_step = 'landing'
            st.rerun()
    
    # 스토리 헤더
    st.markdown(f"# {story['avatar']} {story['title']}")
    
    # 내용
    st.markdown(story['content'])
    
    # 역사적 배경
    if story.get('historical_note'):
        st.markdown(f"### {t('historical_background')}")
        st.info(story['historical_note'])
    
    # 네비게이션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.current_story > 0:
            if st.button("← 이전 이야기"):
                st.session_state.current_story -= 1
                st.rerun()
    
    with col2:
        st.write(f"{st.session_state.current_story + 1} / {len(story_contents)}")
    
    with col3:
        if st.session_state.current_story < len(story_contents) - 1:
            if st.button("다음 이야기 →"):
                st.session_state.current_story += 1
                st.rerun()
    
    # 체험하기 버튼
    st.markdown("---")
    if st.button(t('try_now'), type="primary"):
        st.session_state.current_step = 'action_select'
        st.rerun()

def show_meme_page():
    if not st.session_state.dna_result:
        st.error("DNA 결과가 없습니다.")
        return
    
    # 현재 언어에 맞는 DNA 타입 데이터 가져오기
    lang = st.session_state.language
    dna_types = get_dna_types(lang)
    dna_type_name = get_dna_type_name(st.session_state.dna_result, lang)
    dna_data = dna_types[dna_type_name]
    badge_system = get_badge_system(lang)
    
    completed_count = len(st.session_state.completed_actions)
    is_full_complete = completed_count == len(basic_actions)
    
    # 네비게이션
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button(t('btn_home')):
            st.session_state.current_step = 'landing'
            st.rerun()
    with col2:
        if st.button(t('view_dna_result')):
            st.session_state.current_step = 'result'
            st.rerun()
    with col3:
        if st.button(t('practice_movement')):
            st.session_state.current_step = 'action_select'
            st.rerun()
    
    # 완성 축하
    st.markdown(f"""
    <div class='dna-card' style='background: linear-gradient(135deg, {dna_data['color']}, {dna_data['color']}dd);'>
        <div style='font-size: 3rem; margin-bottom: 1rem;'>🎉</div>
        <h1>{t('dna_awakened') if is_full_complete else f'{completed_count}{t("actions_completed")}'}</h1>
        <p>{t('awakened_msg') if is_full_complete else t('share_journey')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 밈 카드 유형 선택
    st.markdown(f"### {t('meme_type')}")
    
    meme_type = st.radio(
        t('meme_format'),
        [t('static_image'), t('animated_gif')],
        horizontal=True,
        help="정적 이미지는 빠르고 용량이 작으며, GIF는 움직여서 더 눈에 띕니다"
    )
    
    # 스타일 선택
    if meme_type == t('static_image'):
        style_option = st.selectbox(
            t('select_style'),
            [
                t('style_a'),
                t('style_b'),
                t('style_c'),
                t('style_d')
            ],
            index=0,
            help="각 스타일마다 다른 시각적 효과가 적용됩니다"
        )
        
        # 스타일에 따라 다른 밈 카드 생성
        if style_option == t('style_a'):
            meme_card = create_meme_card_gradient_box(dna_type_name, dna_data)
        elif style_option == t('style_b'):
            meme_card = create_meme_card_neon(dna_type_name, dna_data)
        elif style_option == t('style_c'):
            meme_card = create_meme_card_dualtone(dna_type_name, dna_data)
        elif style_option == t('style_d'):
            meme_card = create_meme_card_minimal(dna_type_name, dna_data)
        else:
            meme_card = create_meme_card(dna_type_name, dna_data)
        
        # 밈 카드 표시
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(meme_card, caption=f"{dna_type_name} {t('static_image')}")
    
    else:  # GIF 모드
        # GIF 설정
        col1, col2 = st.columns(2)
        with col1:
            gif_duration = st.slider(t('gif_length'), 2, 5, 3, help="GIF 영상의 길이를 설정합니다")
        with col2:
            style_options = [t('style_gradient'), t('style_neon'), t('style_dualtone'), t('style_minimal')]
            gif_style = st.selectbox(
                t('gif_style'),
                style_options,
                help="GIF에 적용할 스타일을 선택합니다"
            )
        
        # 스타일 매핑 (한국어와 영어 모두 지원)
        style_map = {
            t('style_gradient'): "gradient",
            t('style_neon'): "neon",
            t('style_dualtone'): "dualtone",
            t('style_minimal'): "minimal"
        }
        
        # GIF 생성 버튼
        if st.button(t('generate_gif'), type="primary"):
            with st.spinner(f"멋진 {gif_duration}초 GIF를 생성 중입니다... 잠시만 기다려주세요!"):
                gif_buffer = create_meme_gif(
                    dna_type_name, 
                    dna_data, 
                    duration=gif_duration,
                    fps=10,
                    style=style_map[gif_style]
                )
                
                if gif_buffer:
                    st.session_state.generated_gif = gif_buffer
                    st.success("✨ GIF가 생성되었습니다!")
                else:
                    st.error("GIF 생성에 실패했습니다. 다시 시도해주세요.")
        
        # 생성된 GIF 표시
        if 'generated_gif' in st.session_state and st.session_state.generated_gif:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(st.session_state.generated_gif, caption=f"{st.session_state.dna_result} GIF 밈")
                st.info("💡 GIF는 자동으로 반복 재생됩니다")
    
    # 공유 버튼들
    st.markdown(f"### {t('share_result')}")
    
    col1, col2 = st.columns(2)
    with col1:
        if meme_type == t('static_image'):
            # 이미지를 바이트로 변환
            buf = io.BytesIO()
            meme_card.save(buf, format='PNG', quality=95)
            byte_im = buf.getvalue()
            
            st.download_button(
                label=t('download_png'),
                data=byte_im,
                file_name=f"choomaru_{dna_type_name.replace(' ', '_')}.png",
                mime="image/png",
                type="primary",
                help="밈 카드를 PNG 파일로 다운로드합니다"
            )
        else:  # GIF 모드
            if 'generated_gif' in st.session_state and st.session_state.generated_gif:
                st.download_button(
                    label=t('download_gif'),
                    data=st.session_state.generated_gif.getvalue(),
                    file_name=f"choomaru_{dna_type_name.replace(' ', '_')}.gif",
                    mime="image/gif",
                    type="primary",
                    help="움직이는 밈 카드를 GIF 파일로 다운로드합니다"
                )
            else:
                st.info(t('press_button_first'))
    
    with col2:
        if st.button(t('share_guide')):
            if meme_type == "정적 이미지 (PNG)":
                st.info("💡 다운로드한 이미지를 인스타그램, 페이스북, 트위터 등에 자유롭게 공유하세요!\n\n추천 해시태그: #춤마루 #K_DNA각성 #한국무용")
            else:
                st.info("💡 GIF는 인스타그램 스토리, 페이스북, 트위터에서 자동으로 재생됩니다!\n\n추천 플랫폼: 인스타그램 스토리, 트위터, 텔레그램\n\n추천 해시태그: #춤마루 #K_DNA각성 #한국무용")
    
    # 배지 표시
    if st.session_state.badges:
        st.markdown(f"### {t('earned_badges')}")
        badge_cols = st.columns(len(st.session_state.badges))
        for i, badge_count in enumerate(st.session_state.badges):
            badge = badge_system[badge_count]
            with badge_cols[i]:
                st.markdown(f"""
                <div style='text-align: center; padding: 1rem; background: {badge['color']}20; 
                           border-radius: 10px; color: {badge['color']};'>
                    <div style='font-size: 2rem;'>{badge['emoji']}</div>
                    <div style='font-weight: bold;'>{badge['name']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # 재시작 및 추가 액션
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(t('new_dna')):
            # 세션 초기화
            for key in ['current_step', 'answers', 'current_question', 'dna_result', 
                       'completed_actions', 'current_action', 'badges', 'consecutive_success']:
                if key in st.session_state:
                    if key == 'current_step':
                        st.session_state[key] = 'landing'
                    elif key in ['answers', 'completed_actions', 'badges']:
                        st.session_state[key] = []
                    else:
                        st.session_state[key] = 0
            st.rerun()
    
    with col2:
        if not is_full_complete:
            if st.button(t('continue_actions')):
                st.session_state.current_step = 'action'
                st.rerun()
    
    with col3:
        if st.button(t('see_stories')):
            st.session_state.current_step = 'story'
            st.rerun()
    
    # 성취 메시지
    success_message = (
        t('success_full')
        if is_full_complete else
        t('success_partial').format(count=completed_count)
    )
    
    st.success(success_message)

# ==================== 전문가 시스템 페이지 ====================

def show_expert_login_page():
    """전문가 로그인 페이지"""
    st.markdown(f"## {t('expert_login')}")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        email = st.text_input(t('expert_email'))
        password = st.text_input(t('expert_password'), type="password")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button(t('expert_login'), type="primary", use_container_width=True):
                experts = get_experts()
                for expert_id, expert_data in experts.items():
                    if expert_data.get('email') == email and expert_data.get('password') == password:
                        st.session_state.expert_logged_in = True
                        st.session_state.expert_id = expert_id
                        st.session_state.current_step = 'expert_profile'
                        st.success("로그인 성공!")
                        st.rerun()
                        return
                st.error("이메일 또는 비밀번호가 올바르지 않습니다.")
        
        with col_btn2:
            if st.button("뒤로가기", use_container_width=True):
                st.session_state.current_step = 'landing'
                st.rerun()
        
        st.markdown("---")
        st.markdown(f"아직 계정이 없으신가요? [{t('expert_signup')}](javascript:void(0))")
        if st.button(t('expert_signup'), key="signup_from_login"):
            st.session_state.current_step = 'expert_signup'
            st.rerun()

def show_expert_signup_page():
    """전문가 가입 페이지"""
    st.markdown(f"## {t('expert_signup')}")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name = st.text_input(t('expert_name'))
        email = st.text_input(t('expert_email'))
        password = st.text_input(t('expert_password'), type="password")
        bio = st.text_area(t('expert_bio'))
        specialty = st.text_input(t('expert_specialty'))
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("가입하기", type="primary", use_container_width=True):
                if name and email and password:
                    experts = get_experts()
                    # 이메일 중복 확인
                    if any(e.get('email') == email for e in experts.values()):
                        st.error("이미 등록된 이메일입니다.")
                    else:
                        expert_id = f"expert_{int(time.time())}"
                        expert_data = {
                            'id': expert_id,
                            'name': name,
                            'email': email,
                            'password': password,  # 실제로는 해시화 필요
                            'bio': bio,
                            'specialty': specialty,
                            'created_at': datetime.now().isoformat()
                        }
                        save_expert(expert_id, expert_data)
                        st.session_state.expert_logged_in = True
                        st.session_state.expert_id = expert_id
                        st.session_state.current_step = 'expert_profile'
                        st.success("가입 완료!")
                        st.rerun()
                else:
                    st.error("필수 항목을 모두 입력해주세요.")
        
        with col_btn2:
            if st.button("뒤로가기", use_container_width=True):
                st.session_state.current_step = 'landing'
                st.rerun()

def show_expert_upload_page():
    """전문가 영상 업로드 페이지"""
    if not st.session_state.expert_logged_in:
        st.warning("로그인이 필요합니다.")
        st.session_state.current_step = 'expert_login'
        st.rerun()
        return
    
    st.markdown(f"## {t('expert_upload_video')}")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        dna_types = get_dna_types(st.session_state.language)
        dna_type_names = list(dna_types.keys())
        
        title = st.text_input(t('video_title'))
        description = st.text_area(t('video_description'))
        selected_dna_type = st.selectbox(t('video_dna_type'), dna_type_names)
        tags = st.text_input(t('video_tags'))
        video_file = st.file_uploader("영상 파일 업로드", type=['mp4', 'mov', 'avi'])
        
        if st.button("업로드", type="primary", use_container_width=True):
            if title and video_file:
                # 영상 저장
                video_id = f"video_{int(time.time())}"
                video_filename = f"{video_id}_{video_file.name}"
                video_path = EXPERT_VIDEOS_DIR / video_filename
                
                with open(video_path, "wb") as f:
                    f.write(video_file.getbuffer())
                
                # 영상 데이터 저장
                video_data = {
                    'id': video_id,
                    'expert_id': st.session_state.expert_id,
                    'title': title,
                    'description': description,
                    'dna_type': selected_dna_type,
                    'tags': [tag.strip() for tag in tags.split(',')] if tags else [],
                    'video_path': str(video_path),
                    'created_at': datetime.now().isoformat(),
                    'likes': 0,
                    'comments': 0,
                    'views': 0
                }
                save_video(video_id, video_data)
                st.success(t('upload_success'))
                st.session_state.current_step = 'expert_profile'
                st.rerun()
            else:
                st.error("제목과 영상 파일을 모두 입력해주세요.")
        
        if st.button("뒤로가기", use_container_width=True):
            st.session_state.current_step = 'expert_profile'
            st.rerun()

def show_expert_profile_page():
    """전문가 프로필 페이지"""
    if not st.session_state.expert_logged_in:
        st.warning("로그인이 필요합니다.")
        st.session_state.current_step = 'expert_login'
        st.rerun()
        return
    
    expert = get_experts().get(st.session_state.expert_id, {})
    videos = get_videos()
    expert_videos = [v for v in videos.values() if v.get('expert_id') == st.session_state.expert_id]
    reputation_score = calculate_reputation_score(st.session_state.expert_id)
    reputation_level = get_reputation_level(reputation_score)
    
    st.markdown(f"## {expert.get('name', '전문가')} {t('expert_my_profile')}")
    
    # 프로필 정보
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 15px; color: white; text-align: center;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>{reputation_level['emoji']}</div>
            <h3>{reputation_level['level']}</h3>
            <p style='font-size: 1.5rem; font-weight: bold;'>{reputation_score}점</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"**{t('expert_name')}:** {expert.get('name', '')}")
        st.markdown(f"**{t('expert_bio')}:** {expert.get('bio', '')}")
        st.markdown(f"**{t('expert_specialty')}:** {expert.get('specialty', '')}")
        st.markdown(f"**{t('total_videos')}:** {len(expert_videos)}개")
    
    # 내 영상 목록
    st.markdown("---")
    st.markdown(f"### {t('expert_my_videos')}")
    
    if expert_videos:
        for video in sorted(expert_videos, key=lambda x: x.get('created_at', ''), reverse=True):
            with st.container():
                col1, col2 = st.columns([1, 2])
                with col1:
                    try:
                        st.video(video.get('video_path'))
                    except:
                        st.info("영상 로드 중...")
                with col2:
                    st.markdown(f"### {video.get('title', '')}")
                    st.markdown(f"**DNA 타입:** {video.get('dna_type', '')}")
                    st.markdown(f"**설명:** {video.get('description', '')}")
                    st.markdown(f"**좋아요:** {video.get('likes', 0)} | **댓글:** {video.get('comments', 0)}")
                    if st.button(f"영상 보기", key=f"view_{video['id']}"):
                        st.session_state.viewing_video_id = video['id']
                        st.session_state.current_step = 'video_detail'
                        st.rerun()
                st.markdown("---")
    else:
        st.info(t('no_videos'))
    
    if st.button(t('expert_upload_video')):
        st.session_state.current_step = 'expert_upload'
        st.rerun()

def show_expert_gallery_page():
    """전문가 갤러리 페이지"""
    st.markdown(f"## {t('expert_gallery')}")
    
    videos = get_videos()
    dna_types = get_dna_types(st.session_state.language)
    
    # DNA 타입별 필터
    dna_type_names = ["전체"] + list(dna_types.keys())
    selected_filter = st.selectbox("DNA 타입 필터", dna_type_names)
    
    filtered_videos = videos.values()
    if selected_filter != "전체":
        filtered_videos = [v for v in filtered_videos if v.get('dna_type') == selected_filter]
    
    if filtered_videos:
        # 그리드 레이아웃으로 영상 표시
        cols = st.columns(3)
        for i, video in enumerate(sorted(filtered_videos, key=lambda x: x.get('created_at', ''), reverse=True)):
            with cols[i % 3]:
                with st.container():
                    try:
                        st.video(video.get('video_path'))
                    except:
                        st.info("영상 로드 중...")
                    st.markdown(f"**{video.get('title', '')}**")
                    expert = get_experts().get(video.get('expert_id', ''), {})
                    st.markdown(f"👤 {expert.get('name', '전문가')}")
                    st.markdown(f"🎭 {video.get('dna_type', '')}")
                    if st.button(f"보기", key=f"gallery_{video['id']}"):
                        st.session_state.viewing_video_id = video['id']
                        st.session_state.current_step = 'video_detail'
                        st.rerun()
    else:
        st.info(t('no_videos'))

def show_expert_ranking_page():
    """전문가 랭킹 페이지"""
    st.markdown(f"## {t('expert_ranking')}")
    
    experts = get_experts()
    expert_scores = []
    
    for expert_id, expert_data in experts.items():
        score = calculate_reputation_score(expert_id)
        expert_scores.append({
            'expert_id': expert_id,
            'expert_data': expert_data,
            'score': score
        })
    
    expert_scores.sort(key=lambda x: x['score'], reverse=True)
    
    if expert_scores:
        for rank, item in enumerate(expert_scores, 1):
            expert = item['expert_data']
            score = item['score']
            level = get_reputation_level(score)
            
            videos = get_videos()
            expert_videos = [v for v in videos.values() if v.get('expert_id') == item['expert_id']]
            feedbacks = get_feedback()
            video_ids = [v['id'] for v in expert_videos]
            expert_feedbacks = [f for f in feedbacks.values() if f.get('video_id') in video_ids]
            total_likes = sum(1 for f in expert_feedbacks if f.get('type') == 'like')
            total_comments = sum(1 for f in expert_feedbacks if f.get('type') == 'comment')
            
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 2])
                with col1:
                    st.markdown(f"""
                    <div style='text-align: center; padding: 1rem; background: {level['color']}20; 
                               border-radius: 10px;'>
                        <div style='font-size: 2rem;'>{level['emoji']}</div>
                        <div style='font-weight: bold; font-size: 1.5rem;'>#{rank}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"### {expert.get('name', '전문가')}")
                    st.markdown(f"**{t('expert_specialty')}:** {expert.get('specialty', '')}")
                    st.markdown(f"**{t('expert_bio')}:** {expert.get('bio', '')}")
                with col3:
                    st.markdown(f"**{t('reputation_score')}:** {score}점")
                    st.markdown(f"**{t('reputation_level')}:** {level['level']}")
                    st.markdown(f"**{t('total_videos')}:** {len(expert_videos)}개")
                    st.markdown(f"**{t('total_likes')}:** {total_likes}개")
                    st.markdown(f"**{t('total_comments')}:** {total_comments}개")
                    if st.button(f"{t('view_profile')}", key=f"rank_{item['expert_id']}"):
                        st.session_state.viewing_expert_id = item['expert_id']
                        st.session_state.current_step = 'expert_profile'
                        st.rerun()
                st.markdown("---")
    else:
        st.info(t('no_experts'))

def show_dna_type_gallery_page():
    """DNA 타입별 갤러리 페이지"""
    st.markdown(f"## {t('dna_type_gallery')}")
    
    dna_types = get_dna_types(st.session_state.language)
    dna_type_names = list(dna_types.keys())
    
    # 결과 페이지에서 온 경우 해당 DNA 타입 선택
    if st.session_state.dna_result:
        default_index = 0
        try:
            dna_type_name = get_dna_type_name(st.session_state.dna_result, st.session_state.language)
            if dna_type_name in dna_type_names:
                default_index = dna_type_names.index(dna_type_name)
        except:
            pass
        selected_dna_type = st.selectbox("DNA 타입 선택", dna_type_names, index=default_index)
    else:
        selected_dna_type = st.selectbox("DNA 타입 선택", dna_type_names)
    
    videos = get_videos()
    dna_videos = [v for v in videos.values() if v.get('dna_type') == selected_dna_type]
    
    if dna_videos:
        st.markdown(f"### {selected_dna_type} 영상 ({len(dna_videos)}개)")
        cols = st.columns(3)
        for i, video in enumerate(sorted(dna_videos, key=lambda x: x.get('created_at', ''), reverse=True)):
            with cols[i % 3]:
                with st.container():
                    try:
                        st.video(video.get('video_path'))
                    except:
                        st.info("영상 로드 중...")
                    st.markdown(f"**{video.get('title', '')}**")
                    expert = get_experts().get(video.get('expert_id', ''), {})
                    st.markdown(f"👤 {expert.get('name', '전문가')}")
                    if st.button(f"보기", key=f"dna_{video['id']}"):
                        st.session_state.viewing_video_id = video['id']
                        st.session_state.current_step = 'video_detail'
                        st.rerun()
    else:
        st.info(f"{selected_dna_type} 타입의 영상이 아직 없습니다.")

def show_video_detail_page():
    """영상 상세 페이지"""
    if not st.session_state.viewing_video_id:
        st.warning("영상을 찾을 수 없습니다.")
        st.session_state.current_step = 'expert_gallery'
        st.rerun()
        return
    
    videos = get_videos()
    video = videos.get(st.session_state.viewing_video_id)
    
    if not video:
        st.warning("영상을 찾을 수 없습니다.")
        st.session_state.current_step = 'expert_gallery'
        st.rerun()
        return
    
    expert = get_experts().get(video.get('expert_id', ''), {})
    feedbacks = get_feedback()
    video_feedbacks = [f for f in feedbacks.values() if f.get('video_id') == st.session_state.viewing_video_id]
    comments = [f for f in video_feedbacks if f.get('type') == 'comment']
    likes = [f for f in video_feedbacks if f.get('type') == 'like']
    
    st.markdown(f"## {video.get('title', '')}")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        try:
            st.video(video.get('video_path'))
        except:
            st.info("영상 로드 중...")
    
    with col2:
        st.markdown(f"**👤 전문가:** {expert.get('name', '')}")
        st.markdown(f"**🎭 DNA 타입:** {video.get('dna_type', '')}")
        st.markdown(f"**📅 업로드:** {video.get('created_at', '')[:10]}")
        st.markdown(f"**❤️ 좋아요:** {len(likes)}")
        st.markdown(f"**💬 댓글:** {len(comments)}")
        
        # 좋아요 버튼
        like_key = f"like_{st.session_state.viewing_video_id}"
        if st.button(f"❤️ {t('like')}", key=like_key, use_container_width=True):
            feedback_id = f"feedback_{int(time.time())}"
            feedback_data = {
                'id': feedback_id,
                'video_id': st.session_state.viewing_video_id,
                'type': 'like',
                'created_at': datetime.now().isoformat()
            }
            save_feedback(feedback_id, feedback_data)
            st.success("좋아요를 눌렀습니다!")
            st.rerun()
        
        # 평점
        rating = st.slider(t('rating'), 1, 5, 3)
        if st.button("평점 등록", use_container_width=True):
            feedback_id = f"feedback_{int(time.time())}"
            feedback_data = {
                'id': feedback_id,
                'video_id': st.session_state.viewing_video_id,
                'type': 'rating',
                'rating': rating,
                'created_at': datetime.now().isoformat()
            }
            save_feedback(feedback_id, feedback_data)
            st.success(f"{rating}점을 등록했습니다!")
            st.rerun()
    
    st.markdown("---")
    st.markdown(f"### {t('video_description')}")
    st.markdown(video.get('description', ''))
    
    if video.get('tags'):
        st.markdown("**태그:** " + ", ".join([f"#{tag}" for tag in video.get('tags', [])]))
    
    st.markdown("---")
    st.markdown(f"### {t('comment')} ({len(comments)}개)")
    
    # 댓글 작성
    new_comment = st.text_area(t('write_comment'))
    if st.button(t('submit_comment')):
        if new_comment:
            feedback_id = f"feedback_{int(time.time())}"
            feedback_data = {
                'id': feedback_id,
                'video_id': st.session_state.viewing_video_id,
                'type': 'comment',
                'content': new_comment,
                'created_at': datetime.now().isoformat()
            }
            save_feedback(feedback_id, feedback_data)
            st.success("댓글이 등록되었습니다!")
            st.rerun()
    
    # 댓글 목록
    for comment in sorted(comments, key=lambda x: x.get('created_at', ''), reverse=True):
        st.markdown(f"""
        <div style='background: #f0f0f0; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;'>
            <p>{comment.get('content', '')}</p>
            <small>{comment.get('created_at', '')[:16]}</small>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("뒤로가기"):
        st.session_state.viewing_video_id = None
        st.session_state.current_step = 'expert_gallery'
        st.rerun()

# ==================== B2B 시스템 페이지 ====================

def show_org_login_page():
    """단체 로그인 페이지"""
    st.markdown(f"## {t('org_login')}")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        email = st.text_input(t('org_email'))
        password = st.text_input(t('org_password'), type="password")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button(t('org_login'), type="primary", use_container_width=True):
                orgs = get_organizations()
                for org_id, org_data in orgs.items():
                    if org_data.get('email') == email and org_data.get('password') == password:
                        st.session_state.org_logged_in = True
                        st.session_state.org_id = org_id
                        st.session_state.user_role = 'admin'
                        st.session_state.current_step = 'org_dashboard'
                        st.success("로그인 성공!")
                        st.rerun()
                        return
                st.error("이메일 또는 비밀번호가 올바르지 않습니다.")
        
        with col_btn2:
            if st.button("뒤로가기", use_container_width=True):
                st.session_state.current_step = 'landing'
                st.rerun()
        
        st.markdown("---")
        if st.button(t('org_signup'), key="signup_from_login"):
            st.session_state.current_step = 'org_signup'
            st.rerun()

def show_org_signup_page():
    """단체 가입 페이지"""
    st.markdown(f"## {t('org_signup')}")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name = st.text_input(t('org_name'))
        org_type = st.selectbox(t('org_type'), ["학원", "단체", "기타"])
        email = st.text_input(t('org_email'))
        password = st.text_input(t('org_password'), type="password")
        manager = st.text_input(t('org_manager'))
        address = st.text_input(t('org_address'))
        phone = st.text_input(t('org_phone'))
        
        # 구독 플랜 선택
        st.markdown("### 구독 플랜 선택")
        plan_options = list(SUBSCRIPTION_PLANS.keys())
        selected_plan = st.selectbox("플랜 선택", plan_options, format_func=lambda x: f"{SUBSCRIPTION_PLANS[x]['name']} - 월 {SUBSCRIPTION_PLANS[x]['price']:,}원")
        
        # 플랜 정보 표시
        plan_info = SUBSCRIPTION_PLANS[selected_plan]
        st.info(f"**{plan_info['name']} 플랜**: {', '.join(plan_info['features'])}")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("가입하기", type="primary", use_container_width=True):
                if name and email and password:
                    orgs = get_organizations()
                    if any(o.get('email') == email for o in orgs.values()):
                        st.error("이미 등록된 이메일입니다.")
                    else:
                        org_id = f"org_{int(time.time())}"
                        org_data = {
                            'id': org_id,
                            'name': name,
                            'type': org_type,
                            'email': email,
                            'password': password,
                            'manager': manager,
                            'address': address,
                            'phone': phone,
                            'created_at': datetime.now().isoformat()
                        }
                        save_organization(org_id, org_data)
                        
                        # 구독 생성
                        sub_id = f"sub_{int(time.time())}"
                        sub_data = {
                            'id': sub_id,
                            'org_id': org_id,
                            'plan': selected_plan,
                            'start_date': datetime.now().isoformat(),
                            'status': 'active'
                        }
                        save_subscription(sub_id, sub_data)
                        
                        st.session_state.org_logged_in = True
                        st.session_state.org_id = org_id
                        st.session_state.user_role = 'admin'
                        st.session_state.current_step = 'org_dashboard'
                        st.success("가입 완료!")
                        st.rerun()
                else:
                    st.error("필수 항목을 모두 입력해주세요.")
        
        with col_btn2:
            if st.button("뒤로가기", use_container_width=True):
                st.session_state.current_step = 'landing'
                st.rerun()

def show_org_dashboard_page():
    """단체 대시보드 페이지"""
    if not st.session_state.org_logged_in:
        st.warning("로그인이 필요합니다.")
        st.session_state.current_step = 'org_login'
        st.rerun()
        return
    
    org = get_organizations().get(st.session_state.org_id, {})
    subscriptions = get_subscriptions()
    org_sub = next((s for s in subscriptions.values() if s.get('org_id') == st.session_state.org_id), None)
    plan = SUBSCRIPTION_PLANS.get(org_sub.get('plan', 'basic'), SUBSCRIPTION_PLANS['basic']) if org_sub else SUBSCRIPTION_PLANS['basic']
    
    instructors = get_instructors()
    org_instructors = [i for i in instructors.values() if i.get('org_id') == st.session_state.org_id]
    
    students = get_students()
    org_students = [s for s in students.values() if s.get('org_id') == st.session_state.org_id]
    
    st.markdown(f"## {org.get('name', '단체')} {t('org_dashboard')}")
    
    # 통계 카드
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(t('current_plan'), plan['name'])
    with col2:
        st.metric(t('total_instructors'), len(org_instructors))
    with col3:
        st.metric(t('total_students'), len(org_students))
    with col4:
        progress_data = get_progress()
        org_progress = [p for p in progress_data.values() if p.get('org_id') == st.session_state.org_id]
        if org_progress:
            completed = sum(1 for p in org_progress if p.get('completed', False))
            total = len(org_progress)
            completion_rate = (completed / total * 100) if total > 0 else 0
            st.metric(t('completion_rate'), f"{completion_rate:.1f}%")
        else:
            st.metric(t('completion_rate'), "0%")
    
    # 빠른 액션
    st.markdown("---")
    st.markdown("### 빠른 액션")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button(t('subscription_management'), use_container_width=True):
            st.session_state.current_step = 'subscription_management'
            st.rerun()
    with col2:
        if st.button(t('instructor_management'), use_container_width=True):
            st.session_state.current_step = 'instructor_management'
            st.rerun()
    with col3:
        if st.button(t('student_management'), use_container_width=True):
            st.session_state.current_step = 'student_management'
            st.rerun()
    with col4:
        if st.button(t('custom_actions'), use_container_width=True):
            st.session_state.current_step = 'custom_actions_setup'
            st.rerun()
    
    # 최근 활동
    st.markdown("---")
    st.markdown("### 최근 활동")
    if org_students:
        st.dataframe(pd.DataFrame([{
            '학생명': s.get('name', ''),
            '강사': next((i.get('name', '') for i in org_instructors if i.get('id') == s.get('instructor_id')), ''),
            '상태': '활성'
        } for s in org_students[:10]]), use_container_width=True)
    else:
        st.info("등록된 학생이 없습니다.")

def show_subscription_management_page():
    """구독 관리 페이지"""
    if not st.session_state.org_logged_in:
        st.warning("로그인이 필요합니다.")
        st.session_state.current_step = 'org_login'
        st.rerun()
        return
    
    subscriptions = get_subscriptions()
    org_sub = next((s for s in subscriptions.values() if s.get('org_id') == st.session_state.org_id), None)
    current_plan = org_sub.get('plan', 'basic') if org_sub else 'basic'
    current_plan_info = SUBSCRIPTION_PLANS[current_plan]
    
    st.markdown(f"## {t('subscription_management')}")
    
    # 현재 플랜 정보
    st.markdown(f"### {t('current_plan')}: {current_plan_info['name']}")
    st.markdown(f"**월 구독료:** {current_plan_info['price']:,}원")
    st.markdown(f"**기능:** {', '.join(current_plan_info['features'])}")
    
    # 플랜 비교 및 업그레이드
    st.markdown("---")
    st.markdown("### 플랜 변경")
    
    plan_options = list(SUBSCRIPTION_PLANS.keys())
    current_index = plan_options.index(current_plan) if current_plan in plan_options else 0
    
    new_plan = st.selectbox("새 플랜 선택", plan_options, index=current_index, format_func=lambda x: f"{SUBSCRIPTION_PLANS[x]['name']} - 월 {SUBSCRIPTION_PLANS[x]['price']:,}원")
    
    if new_plan != current_plan:
        new_plan_info = SUBSCRIPTION_PLANS[new_plan]
        st.info(f"**{new_plan_info['name']} 플랜**: {', '.join(new_plan_info['features'])}")
        
        if st.button("플랜 변경", type="primary"):
            if org_sub:
                org_sub['plan'] = new_plan
                org_sub['updated_at'] = datetime.now().isoformat()
                save_subscription(org_sub['id'], org_sub)
                st.success(f"{new_plan_info['name']} 플랜으로 변경되었습니다!")
                st.rerun()
    
    if st.button("뒤로가기"):
        st.session_state.current_step = 'org_dashboard'
        st.rerun()

def show_instructor_management_page():
    """강사 관리 페이지"""
    if not st.session_state.org_logged_in:
        st.warning("로그인이 필요합니다.")
        st.session_state.current_step = 'org_login'
        st.rerun()
        return
    
    org = get_organizations().get(st.session_state.org_id, {})
    subscriptions = get_subscriptions()
    org_sub = next((s for s in subscriptions.values() if s.get('org_id') == st.session_state.org_id), None)
    plan = SUBSCRIPTION_PLANS.get(org_sub.get('plan', 'basic'), SUBSCRIPTION_PLANS['basic']) if org_sub else SUBSCRIPTION_PLANS['basic']
    
    instructors = get_instructors()
    org_instructors = [i for i in instructors.values() if i.get('org_id') == st.session_state.org_id]
    max_instructors = plan['max_instructors']
    
    st.markdown(f"## {t('instructor_management')}")
    st.markdown(f"**{t('max_instructors')}:** {max_instructors if max_instructors > 0 else '무제한'} | **현재:** {len(org_instructors)}명")
    
    # 강사 추가
    st.markdown("---")
    st.markdown(f"### {t('add_instructor')}")
    with st.form("add_instructor_form"):
        instructor_name = st.text_input(t('instructor_name'))
        instructor_email = st.text_input(t('instructor_email'))
        instructor_phone = st.text_input("전화번호")
        
        if st.form_submit_button("강사 추가", type="primary"):
            if instructor_name and instructor_email:
                if max_instructors > 0 and len(org_instructors) >= max_instructors:
                    st.error(f"최대 강사 수({max_instructors}명)에 도달했습니다. 플랜을 업그레이드하세요.")
                else:
                    instructor_id = f"instructor_{int(time.time())}"
                    instructor_data = {
                        'id': instructor_id,
                        'org_id': st.session_state.org_id,
                        'name': instructor_name,
                        'email': instructor_email,
                        'phone': instructor_phone,
                        'created_at': datetime.now().isoformat()
                    }
                    save_instructor(instructor_id, instructor_data)
                    st.success("강사가 추가되었습니다!")
                    st.rerun()
            else:
                st.error("필수 항목을 모두 입력해주세요.")
    
    # 강사 목록
    st.markdown("---")
    st.markdown("### 강사 목록")
    if org_instructors:
        for instructor in org_instructors:
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.markdown(f"**{instructor.get('name', '')}**")
                    st.markdown(f"이메일: {instructor.get('email', '')}")
                with col2:
                    students = get_students()
                    instructor_students = [s for s in students.values() if s.get('instructor_id') == instructor['id']]
                    st.markdown(f"담당 학생: {len(instructor_students)}명")
                with col3:
                    if st.button("삭제", key=f"del_{instructor['id']}"):
                        # 강사 삭제 시 학생들의 instructor_id도 제거
                        for student in instructor_students:
                            student['instructor_id'] = None
                            save_student(student['id'], student)
                        del instructors[instructor['id']]
                        save_json(INSTRUCTORS_FILE, instructors)
                        st.success("강사가 삭제되었습니다!")
                        st.rerun()
                st.markdown("---")
    else:
        st.info("등록된 강사가 없습니다.")
    
    if st.button("뒤로가기"):
        st.session_state.current_step = 'org_dashboard'
        st.rerun()

def show_student_management_page():
    """학생 관리 페이지"""
    if not st.session_state.org_logged_in:
        st.warning("로그인이 필요합니다.")
        st.session_state.current_step = 'org_login'
        st.rerun()
        return
    
    org = get_organizations().get(st.session_state.org_id, {})
    subscriptions = get_subscriptions()
    org_sub = next((s for s in subscriptions.values() if s.get('org_id') == st.session_state.org_id), None)
    plan = SUBSCRIPTION_PLANS.get(org_sub.get('plan', 'basic'), SUBSCRIPTION_PLANS['basic']) if org_sub else SUBSCRIPTION_PLANS['basic']
    
    students = get_students()
    org_students = [s for s in students.values() if s.get('org_id') == st.session_state.org_id]
    instructors = get_instructors()
    org_instructors = [i for i in instructors.values() if i.get('org_id') == st.session_state.org_id]
    max_students = plan['max_students']
    
    st.markdown(f"## {t('student_management')}")
    st.markdown(f"**{t('max_students')}:** {max_students if max_students > 0 else '무제한'} | **현재:** {len(org_students)}명")
    
    # 학생 추가
    st.markdown("---")
    st.markdown(f"### {t('add_student')}")
    with st.form("add_student_form"):
        student_name = st.text_input(t('student_name'))
        student_email = st.text_input(t('student_email'))
        instructor_options = ["없음"] + [f"{i['name']} ({i['email']})" for i in org_instructors]
        selected_instructor = st.selectbox("담당 강사", instructor_options)
        
        if st.form_submit_button("학생 추가", type="primary"):
            if student_name and student_email:
                if max_students > 0 and len(org_students) >= max_students:
                    st.error(f"최대 학생 수({max_students}명)에 도달했습니다. 플랜을 업그레이드하세요.")
                else:
                    student_id = f"student_{int(time.time())}"
                    instructor_id = None
                    if selected_instructor != "없음":
                        instructor_name_email = selected_instructor.split(" (")[0]
                        instructor = next((i for i in org_instructors if i['name'] == instructor_name_email), None)
                        if instructor:
                            instructor_id = instructor['id']
                    
                    student_data = {
                        'id': student_id,
                        'org_id': st.session_state.org_id,
                        'instructor_id': instructor_id,
                        'name': student_name,
                        'email': student_email,
                        'created_at': datetime.now().isoformat()
                    }
                    save_student(student_id, student_data)
                    st.success("학생이 추가되었습니다!")
                    st.rerun()
            else:
                st.error("필수 항목을 모두 입력해주세요.")
    
    # 학생 목록
    st.markdown("---")
    st.markdown("### 학생 목록")
    if org_students:
        for student in org_students:
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.markdown(f"**{student.get('name', '')}**")
                    st.markdown(f"이메일: {student.get('email', '')}")
                with col2:
                    instructor = next((i for i in org_instructors if i.get('id') == student.get('instructor_id')), None)
                    st.markdown(f"담당 강사: {instructor.get('name', '없음') if instructor else '없음'}")
                with col3:
                    if st.button("삭제", key=f"del_{student['id']}"):
                        del students[student['id']]
                        save_json(STUDENTS_FILE, students)
                        st.success("학생이 삭제되었습니다!")
                        st.rerun()
                st.markdown("---")
    else:
        st.info("등록된 학생이 없습니다.")
    
    if st.button("뒤로가기"):
        st.session_state.current_step = 'org_dashboard'
        st.rerun()

def show_custom_actions_setup_page():
    """커스텀 동작 세트 설정 페이지"""
    if not st.session_state.org_logged_in:
        st.warning("로그인이 필요합니다.")
        st.session_state.current_step = 'org_login'
        st.rerun()
        return
    
    subscriptions = get_subscriptions()
    org_sub = next((s for s in subscriptions.values() if s.get('org_id') == st.session_state.org_id), None)
    plan = SUBSCRIPTION_PLANS.get(org_sub.get('plan', 'basic'), SUBSCRIPTION_PLANS['basic']) if org_sub else SUBSCRIPTION_PLANS['basic']
    
    st.markdown(f"## {t('custom_actions')}")
    st.markdown(f"**현재 플랜:** {plan['name']}")
    
    # 플랜별 사용 가능한 동작 수
    max_basic = plan['basic_actions']
    max_expanded = plan['expanded_actions']
    max_creative = plan['creative_actions']
    
    # 전체 동작 가져오기
    lang = st.session_state.language
    basic_actions = get_basic_actions(lang)
    expanded_actions = get_expanded_actions(lang)
    creative_actions = get_creative_actions(lang)
    
    # 저장된 설정 가져오기
    org = get_organizations().get(st.session_state.org_id, {})
    selected_basic = org.get('selected_basic_actions', [])
    selected_expanded = org.get('selected_expanded_actions', [])
    selected_creative = org.get('selected_creative_actions', [])
    
    # 기본 동작 선택
    if max_basic > 0:
        st.markdown(f"### 기본 동작 선택 (최대 {max_basic}개)")
        basic_options = [f"{i+1}. {a['name']}" for i, a in enumerate(basic_actions)]
        selected_basic_indices = st.multiselect(
            "기본 동작 선택",
            basic_options,
            default=[basic_options[i] for i in selected_basic if i < len(basic_options)],
            max_selections=max_basic
        )
        selected_basic = [basic_options.index(opt) for opt in selected_basic_indices if opt in basic_options]
    
    # 확장 동작 선택
    if max_expanded > 0:
        st.markdown(f"### 확장 동작 선택 (최대 {max_expanded}개)")
        expanded_options = [f"{i+1}. {a['name']}" for i, a in enumerate(expanded_actions)]
        selected_expanded_indices = st.multiselect(
            "확장 동작 선택",
            expanded_options,
            default=[expanded_options[i] for i in selected_expanded if i < len(expanded_options)],
            max_selections=max_expanded
        )
        selected_expanded = [expanded_options.index(opt) for opt in selected_expanded_indices if opt in expanded_options]
    
    # 창작 동작 선택
    if max_creative > 0:
        st.markdown(f"### 창작 동작 선택 (최대 {max_creative}개)")
        creative_options = [f"{i+1}. {a['name']}" for i, a in enumerate(creative_actions)]
        selected_creative_indices = st.multiselect(
            "창작 동작 선택",
            creative_options,
            default=[creative_options[i] for i in selected_creative if i < len(creative_options)],
            max_selections=max_creative
        )
        selected_creative = [creative_options.index(opt) for opt in selected_creative_indices if opt in creative_options]
    
    if st.button(t('save_settings'), type="primary"):
        org['selected_basic_actions'] = selected_basic
        org['selected_expanded_actions'] = selected_expanded
        org['selected_creative_actions'] = selected_creative
        save_organization(st.session_state.org_id, org)
        st.success("설정이 저장되었습니다!")
        st.rerun()
    
    if st.button("뒤로가기"):
        st.session_state.current_step = 'org_dashboard'
        st.rerun()

def show_org_statistics_page():
    """단체 통계 페이지"""
    if not st.session_state.org_logged_in:
        st.warning("로그인이 필요합니다.")
        st.session_state.current_step = 'org_login'
        st.rerun()
        return
    
    st.markdown(f"## {t('statistics')}")
    
    students = get_students()
    org_students = [s for s in students.values() if s.get('org_id') == st.session_state.org_id]
    progress_data = get_progress()
    org_progress = [p for p in progress_data.values() if p.get('org_id') == st.session_state.org_id]
    
    # 통계 표시
    col1, col2 = st.columns(2)
    with col1:
        st.metric("전체 학생", len(org_students))
        st.metric("완료된 동작", sum(1 for p in org_progress if p.get('completed', False)))
    with col2:
        if org_progress:
            completed = sum(1 for p in org_progress if p.get('completed', False))
            completion_rate = (completed / len(org_progress) * 100) if org_progress else 0
            st.metric("완료율", f"{completion_rate:.1f}%")
    
    if st.button("뒤로가기"):
        st.session_state.current_step = 'org_dashboard'
        st.rerun()

# ==================== 동작 테스트 페이지 ====================

# MediaPipe 랜드마크 그리기 헬퍼 함수
def draw_landmarks_on_image(rgb_image, detection_result):
    """MediaPipe Pose 랜드마크를 이미지에 그리기"""
    pose_landmarks_list = detection_result.pose_landmarks
    annotated_image = np.copy(rgb_image)

    if not pose_landmarks_list:
        return annotated_image

    height, width, _ = annotated_image.shape

    # Pose 연결선 정의 (MediaPipe Pose 33개 랜드마크 기준)
    POSE_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
        (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
        (17, 19), (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
        (11, 23), (12, 24), (23, 24), (23, 25), (25, 27), (27, 29), (27, 31),
        (29, 31), (24, 26), (26, 28), (28, 30), (28, 32), (30, 32)
    ]

    # 각 사람의 포즈 랜드마크를 순회
    for pose_landmarks in pose_landmarks_list:
        # 연결선 그리기
        for connection in POSE_CONNECTIONS:
            start_idx, end_idx = connection
            if start_idx < len(pose_landmarks) and end_idx < len(pose_landmarks):
                start_landmark = pose_landmarks[start_idx]
                end_landmark = pose_landmarks[end_idx]

                # 가시성이 충분한 경우에만 그리기
                if start_landmark.visibility > 0.5 and end_landmark.visibility > 0.5:
                    start_point = (int(start_landmark.x * width), int(start_landmark.y * height))
                    end_point = (int(end_landmark.x * width), int(end_landmark.y * height))
                    cv2.line(annotated_image, start_point, end_point, (0, 255, 0), 2)

        # 랜드마크 점 그리기
        for landmark in pose_landmarks:
            if landmark.visibility > 0.5:
                x = int(landmark.x * width)
                y = int(landmark.y * height)
                cv2.circle(annotated_image, (x, y), 5, (255, 0, 0), -1)
                cv2.circle(annotated_image, (x, y), 5, (0, 255, 255), 2)

    return annotated_image

def draw_hands_on_image(rgb_image, detection_result):
    """MediaPipe Hands 랜드마크를 이미지에 그리기"""
    hand_landmarks_list = detection_result.hand_landmarks
    annotated_image = np.copy(rgb_image)

    if not hand_landmarks_list:
        return annotated_image

    height, width, _ = annotated_image.shape

    # Hand 연결선 정의 (MediaPipe Hands 21개 랜드마크 기준)
    HAND_CONNECTIONS = [
        # 손바닥
        (0, 1), (1, 2), (2, 3), (3, 4),      # 엄지
        (0, 5), (5, 6), (6, 7), (7, 8),      # 검지
        (0, 9), (9, 10), (10, 11), (11, 12), # 중지
        (0, 13), (13, 14), (14, 15), (15, 16), # 약지
        (0, 17), (17, 18), (18, 19), (19, 20), # 새끼
        (5, 9), (9, 13), (13, 17)            # 손바닥 연결
    ]

    # 각 손의 랜드마크를 순회
    for hand_landmarks in hand_landmarks_list:
        # 연결선 그리기
        for connection in HAND_CONNECTIONS:
            start_idx, end_idx = connection
            if start_idx < len(hand_landmarks) and end_idx < len(hand_landmarks):
                start_landmark = hand_landmarks[start_idx]
                end_landmark = hand_landmarks[end_idx]

                start_point = (int(start_landmark.x * width), int(start_landmark.y * height))
                end_point = (int(end_landmark.x * width), int(end_landmark.y * height))
                cv2.line(annotated_image, start_point, end_point, (255, 0, 255), 2)  # 마젠타색

        # 랜드마크 점 그리기
        for landmark in hand_landmarks:
            x = int(landmark.x * width)
            y = int(landmark.y * height)
            cv2.circle(annotated_image, (x, y), 4, (0, 0, 255), -1)  # 빨간색
            cv2.circle(annotated_image, (x, y), 4, (255, 255, 0), 1)  # 노란색 테두리

    return annotated_image

# =============================================================================
# 전문가 영상 사전 처리 함수 (스켈레톤 그리기 + 랜드마크 JSON 저장)
# WebRTC 환경에서는 while loop를 사용할 수 없으므로 미리 처리
# =============================================================================
def process_expert_video_with_skeleton(expert_video_path):
    """
    전문가 영상에 skeleton을 그려서 새 영상 생성 + 랜드마크를 JSON으로 저장

    Returns:
        tuple: (skeleton 영상 경로, landmarks JSON 경로) 또는 (None, None)
    """
    if not os.path.exists(expert_video_path):
        return None, None

    try:
        # 출력 파일 경로
        output_dir = "videos/processed"
        landmarks_dir = "data/expert_landmarks"
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(landmarks_dir, exist_ok=True)

        video_filename = os.path.basename(expert_video_path)
        video_name = os.path.splitext(video_filename)[0]
        output_video_path = os.path.join(output_dir, f"skeleton_{video_filename}")
        output_landmarks_path = os.path.join(landmarks_dir, f"{video_name}_landmarks.json")

        # 이미 처리된 파일이 있으면 반환
        if os.path.exists(output_video_path) and os.path.exists(output_landmarks_path):
            return output_video_path, output_landmarks_path

        print(f"전문가 영상 처리 중: {video_filename}...")

        # MediaPipe 초기화
        pose_model_path = os.path.join(os.path.dirname(__file__), "models", "pose_landmarker_lite.task")
        pose_base_options = python.BaseOptions(model_asset_path=pose_model_path)
        pose_options = vision.PoseLandmarkerOptions(
            base_options=pose_base_options,
            running_mode=vision.RunningMode.VIDEO
        )
        pose_landmarker = vision.PoseLandmarker.create_from_options(pose_options)

        hand_model_path = os.path.join(os.path.dirname(__file__), "models", "hand_landmarker.task")
        hand_base_options = python.BaseOptions(model_asset_path=hand_model_path)
        hand_options = vision.HandLandmarkerOptions(
            base_options=hand_base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2
        )
        hand_landmarker = vision.HandLandmarker.create_from_options(hand_options)

        # 영상 읽기
        cap = cv2.VideoCapture(expert_video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # 비디오 writer 설정
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

        # 랜드마크 저장용 리스트
        all_landmarks = []

        frame_timestamp_ms = 0
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # BGR → RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

            # Pose 감지
            pose_result = pose_landmarker.detect_for_video(mp_image, frame_timestamp_ms)

            # 랜드마크 데이터 저장
            frame_data = {
                'frame': frame_count,
                'timestamp_ms': frame_timestamp_ms,
                'pose_landmarks': None,
                'hand_landmarks': None
            }

            # Pose 랜드마크 그리기 및 저장
            if pose_result.pose_landmarks:
                frame_rgb = draw_landmarks_on_image(frame_rgb, pose_result)
                # 랜드마크를 직렬화 가능한 형태로 변환
                landmarks = pose_result.pose_landmarks[0]
                frame_data['pose_landmarks'] = [
                    {'x': lm.x, 'y': lm.y, 'z': lm.z, 'visibility': lm.visibility}
                    for lm in landmarks
                ]

            # Hand 감지 및 그리기
            hand_result = hand_landmarker.detect_for_video(mp_image, frame_timestamp_ms)
            if hand_result.hand_landmarks:
                frame_rgb = draw_hands_on_image(frame_rgb, hand_result)
                frame_data['hand_landmarks'] = [
                    [{'x': lm.x, 'y': lm.y, 'z': lm.z} for lm in hand]
                    for hand in hand_result.hand_landmarks
                ]

            all_landmarks.append(frame_data)

            # RGB → BGR로 변환하여 저장
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            out.write(frame_bgr)

            frame_timestamp_ms += int(1000 / fps)
            frame_count += 1

        # 정리
        cap.release()
        out.release()
        pose_landmarker.close()
        hand_landmarker.close()

        # 랜드마크 JSON 저장
        landmarks_data = {
            'video_file': video_filename,
            'fps': fps,
            'total_frames': frame_count,
            'frames': all_landmarks
        }

        with open(output_landmarks_path, 'w', encoding='utf-8') as f:
            json.dump(landmarks_data, f, ensure_ascii=False, indent=2)

        print(f"처리 완료: {output_video_path}, {output_landmarks_path}")
        return output_video_path, output_landmarks_path

    except Exception as e:
        print(f"전문가 영상 처리 실패: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def load_expert_landmarks(landmarks_json_path):
    """
    전문가 랜드마크 JSON 파일에서 대표 프레임 랜드마크 로드

    Returns:
        list: 대표 프레임의 pose_landmarks (33개 랜드마크) 또는 None
    """
    if not os.path.exists(landmarks_json_path):
        return None

    try:
        with open(landmarks_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 중간 프레임 선택 (대표 자세)
        total_frames = data['total_frames']
        mid_frame_idx = total_frames // 2
        mid_frame_data = data['frames'][mid_frame_idx]

        if mid_frame_data['pose_landmarks']:
            return mid_frame_data['pose_landmarks']

        # 중간 프레임에 랜드마크가 없으면 다른 프레임에서 찾기
        for frame_data in data['frames']:
            if frame_data['pose_landmarks']:
                return frame_data['pose_landmarks']

        return None

    except Exception as e:
        print(f"랜드마크 로드 실패: {e}")
        return None


def show_pose_test_page():
    """
    MediaPipe를 활용한 실시간 자세 감지 페이지 (WebRTC 기반)
    - Streamlit Cloud 배포 호환
    - 전문가 자세와 비교 기능 추가
    """
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <h2>🎯 실시간 자세 감지 테스트</h2>
        <p style='color: #666;'>MediaPipe Pose를 활용하여 웹캠에서 실시간으로 자세 랜드마크를 감지합니다</p>
    </div>
    """, unsafe_allow_html=True)

    # 세션 상태 초기화
    if 'pose_landmarks_data' not in st.session_state:
        st.session_state.pose_landmarks_data = []
    if 'hand_landmarks_data' not in st.session_state:
        st.session_state.hand_landmarks_data = []
    if 'frame_count' not in st.session_state:
        st.session_state.frame_count = 0

    # 메인 컨텐츠
    col1, col2 = st.columns([2, 1])

    # col2(설정)를 먼저 렌더링하여 변수들을 정의
    with col2:
        st.markdown("### ⚙️ 설정")

        # 감지 설정
        st.markdown("#### 감지 설정")
        min_detection_confidence = st.slider(
            "감지 신뢰도",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="자세를 처음 감지할 때의 최소 신뢰도"
        )

        min_tracking_confidence = st.slider(
            "추적 신뢰도",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="이미 감지된 자세를 추적할 때의 최소 신뢰도"
        )

        show_landmarks = st.checkbox(
            "랜드마크 표시",
            value=True,
            help="웹캠 화면에 자세 랜드마크를 표시"
        )

        # MediaPipe Hands 활성화
        enable_hands = st.checkbox(
            "✋ MediaPipe Hands 활성화",
            value=False,
            help="손 랜드마크 감지 및 표시 (21개 랜드마크/손)"
        )

        st.markdown("---")

        # 전문가 자세 비교 설정
        st.markdown("#### 🎯 전문가 자세 비교")

        # 사용 가능한 전문가 랜드마크 파일 목록
        expert_landmarks_dir = "data/expert_landmarks"
        expert_files = []
        if os.path.exists(expert_landmarks_dir):
            expert_files = [f.replace("_landmarks.json", "") for f in os.listdir(expert_landmarks_dir) if f.endswith("_landmarks.json")]

        if expert_files:
            enable_comparison = st.checkbox(
                "전문가 자세 비교 활성화",
                value=False,
                help="선택한 전문가 자세와 실시간 비교"
            )

            if enable_comparison:
                selected_expert = st.selectbox(
                    "비교할 동작 선택",
                    options=expert_files,
                    format_func=lambda x: x.replace("-", " ").title()
                )
            else:
                selected_expert = None
        else:
            enable_comparison = False
            selected_expert = None
            st.info("📂 전문가 자세 데이터가 없습니다")

        st.markdown("---")
        st.markdown("### 📊 감지 정보")

        # 피드백 표시 영역
        feedback_container = st.container()

        # MediaPipe Pose 랜드마크 정보
        with st.expander("🎯 MediaPipe Pose 랜드마크 (33개)", expanded=False):
            st.markdown("""
            **얼굴/머리 (8개)**
            - 0: 코, 1-4: 눈, 5-8: 입

            **상체 (14개)**
            - 11-12: 어깨
            - 13-14: 팔꿈치
            - 15-16: 손목
            - 17-22: 손 (엄지, 검지, 새끼손가락)

            **하체 (11개)**
            - 23-24: 엉덩이
            - 25-26: 무릎
            - 27-28: 발목
            - 29-32: 발 (뒤꿈치, 발끝)
            """)

        # 사용 가이드
        with st.expander("📖 사용 가이드", expanded=False):
            st.markdown("""
            **사용 방법:**
            1. 'START' 버튼을 클릭하여 카메라 시작
            2. 브라우저에서 카메라 권한 허용
            3. 카메라 앞에서 몸 전체가 나오도록 서세요
            4. 랜드마크가 자동으로 감지되어 표시됩니다

            **전문가 자세 비교:**
            - 우측 패널에서 '전문가 자세 비교 활성화' 체크
            - 비교할 동작 선택
            - 실시간으로 자세 유사도 점수 표시

            **팁:**
            - 조명이 밝은 곳에서 사용하세요
            - 배경이 단순할수록 감지 정확도가 높아집니다
            - 카메라와 2-3m 거리를 유지하세요
            """)

    # col1(웹캠)
    with col1:
        st.markdown("### 📹 웹캠 영상")

        # 캐시된 MediaPipe 사용
        pose_landmarker = get_pose_landmarker(min_detection_confidence, min_tracking_confidence)
        hand_landmarker = get_hand_landmarker(min_detection_confidence, min_tracking_confidence) if enable_hands else None

        # 전문가 랜드마크 로드
        expert_reference_landmarks = None
        if enable_comparison and selected_expert:
            expert_json_path = f"{expert_landmarks_dir}/{selected_expert}_landmarks.json"
            if os.path.exists(expert_json_path):
                expert_reference_landmarks = load_expert_landmarks(expert_json_path)

        # WebRTC 비디오 프레임 콜백
        def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="rgb24")
            img = cv2.flip(img, 1)

            try:
                import time
                timestamp_ms = int(time.time() * 1000)

                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img)
                pose_result = pose_landmarker.detect_for_video(mp_image, timestamp_ms)

                if show_landmarks and pose_result.pose_landmarks:
                    img = draw_landmarks_on_image(img, pose_result)

                    if expert_reference_landmarks:
                        try:
                            comparison_result = compare_poses(pose_result.pose_landmarks[0], expert_reference_landmarks)
                            score = comparison_result['overall_score']
                            color = (0, 255, 0) if score >= 80 else (255, 165, 0) if score >= 60 else (255, 0, 0)
                            cv2.putText(img, f'Score: {score}%', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                            update_webrtc_state('pose_test_page', {
                                'feedback_score': score,
                                'feedback_messages': comparison_result['feedback'],
                                'joint_coverage': comparison_result.get('joint_coverage_percent', 100),
                                'pose_detected': True,
                                                            })
                        except Exception as e:
                            update_webrtc_state('pose_test_page', {'pose_detected': True, })
                    else:
                        cv2.putText(img, 'Pose: OK', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        update_webrtc_state('pose_test_page', {'pose_detected': True, })
                else:
                    update_webrtc_state('pose_test_page', {'pose_detected': False, 'feedback_score': 0, })

                if enable_hands and hand_landmarker:
                    hand_result = hand_landmarker.detect_for_video(mp_image, timestamp_ms)
                    if hand_result.hand_landmarks:
                        img = draw_hands_on_image(img, hand_result)
                        update_webrtc_state('pose_test_page', {'hands_detected': len(hand_result.hand_landmarks)})
                    else:
                        update_webrtc_state('pose_test_page', {'hands_detected': 0})

            except Exception as e:
                import traceback
                traceback.print_exc()

            return av.VideoFrame.from_ndarray(img, format="rgb24")

        # WebRTC 스트리머
        webrtc_ctx = webrtc_streamer(
            key="pose_test_camera",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}),
            video_frame_callback=video_frame_callback,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

        # 피드백 업데이트
        if webrtc_ctx.state.playing:
            st_autorefresh(interval=1000, key="pose_test_feedback_refresh")

            state = get_webrtc_state('pose_test_page')

            with feedback_container:
                if enable_comparison and expert_reference_landmarks:
                    score = state.get('feedback_score', 0)
                    messages = state.get('feedback_messages', [])
                    joint_coverage = state.get('joint_coverage', 0)

                    if score >= 80:
                        st.success(f"🎯 유사도: {score}%")
                    elif score >= 60:
                        st.warning(f"🎯 유사도: {score}%")
                    elif score > 0:
                        st.error(f"🎯 유사도: {score}%")
                    else:
                        st.info("📊 자세 분석 중...")

                    if joint_coverage > 0:
                        st.progress(joint_coverage / 100, text=f"관절 감지율: {joint_coverage}%")

                    if messages:
                        for msg in messages[:3]:
                            st.caption(msg)
                else:
                    if state.get('pose_detected', False):
                        st.success("✅ 자세 감지 중")
                    else:
                        st.info("📊 자세 분석 중...")

                    if enable_hands and state.get('hands_detected', 0) > 0:
                        st.info(f"✋ 손 감지: {state['hands_detected']}개")
        else:
            reset_webrtc_state('pose_test_page')

    # 뒤로가기 버튼
    st.markdown("---")
    if st.button("🏠 홈으로 돌아가기", use_container_width=True):
        reset_webrtc_state('pose_test_page')
        st.session_state.current_step = 'landing'
        st.rerun()


def convert_landmarks_to_csv(pose_landmarks_data, hand_landmarks_data):
    """Pose 및 Hands 랜드마크 데이터를 CSV 형식으로 변환"""
    if not pose_landmarks_data and not hand_landmarks_data:
        return ""

    # CSV 헤더 생성
    headers = ['frame', 'timestamp']

    # Pose 랜드마크 헤더 (33개)
    for i in range(33):
        headers.extend([f'pose_{i}_x', f'pose_{i}_y', f'pose_{i}_z', f'pose_{i}_visibility'])

    # Hands 랜드마크 헤더 (최대 2개 손, 각 21개 랜드마크)
    for hand_idx in range(2):
        for i in range(21):
            headers.extend([
                f'hand{hand_idx}_lm{i}_x',
                f'hand{hand_idx}_lm{i}_y',
                f'hand{hand_idx}_lm{i}_z'
            ])
        headers.append(f'hand{hand_idx}_handedness')  # Left or Right

    csv_data = ','.join(headers) + '\n'

    # 프레임 데이터를 매칭하여 병합
    max_frames = max(
        len(pose_landmarks_data) if pose_landmarks_data else 0,
        len(hand_landmarks_data) if hand_landmarks_data else 0
    )

    for frame_idx in range(max_frames):
        row = []

        # Pose 데이터 가져오기
        if frame_idx < len(pose_landmarks_data):
            pose_frame = pose_landmarks_data[frame_idx]
            row.extend([str(pose_frame['frame']), str(pose_frame['timestamp'])])

            # Pose 랜드마크
            landmarks = pose_frame.get('landmarks', [])
            for i in range(33):
                if i < len(landmarks):
                    lm = landmarks[i]
                    row.extend([str(lm['x']), str(lm['y']), str(lm['z']), str(lm['visibility'])])
                else:
                    row.extend(['', '', '', ''])
        else:
            row.extend(['', ''])  # frame, timestamp
            for i in range(33):
                row.extend(['', '', '', ''])

        # Hands 데이터 가져오기
        hands_dict = {}
        if frame_idx < len(hand_landmarks_data):
            hand_frame = hand_landmarks_data[frame_idx]
            for hand_data in hand_frame.get('hands', []):
                hand_idx = hand_data.get('hand_index', 0)
                hands_dict[hand_idx] = hand_data

        # 최대 2개 손에 대한 데이터
        for hand_idx in range(2):
            if hand_idx in hands_dict:
                hand_data = hands_dict[hand_idx]
                landmarks = hand_data.get('landmarks', [])
                for i in range(21):
                    if i < len(landmarks):
                        lm = landmarks[i]
                        row.extend([str(lm['x']), str(lm['y']), str(lm['z'])])
                    else:
                        row.extend(['', '', ''])
                row.append(hand_data.get('handedness', ''))
            else:
                for i in range(21):
                    row.extend(['', '', ''])
                row.append('')

        csv_data += ','.join(row) + '\n'

    return csv_data

if __name__ == "__main__":
    main()

# 실행방법:
# pip install streamlit opencv-python mediapipe pillow numpy pandas
# streamlit run app_v13.py
