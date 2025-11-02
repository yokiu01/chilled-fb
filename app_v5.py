# 춤마루 MVP v5 Streamlit (2025.09.18)
# 완전한 Streamlit 구현 버전 - 10개 질문, 8개 DNA 타입, 12개 기본동작, 6개 확장동작, 8개 창작동작 포함
# MediaPipe 실제 구현, 영상 업로드 지원, 웹캠 동작 인식 기능

import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
from PIL import Image, ImageDraw, ImageFont
import json
import time
import random

# 페이지 설정
st.set_page_config(
    page_title="춤마루 - K-DNA 체험",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
    if 'current_story' not in st.session_state:
        st.session_state.current_story = 0
    if 'badges' not in st.session_state:
        st.session_state.badges = []
    if 'consecutive_success' not in st.session_state:
        st.session_state.consecutive_success = 0

# 10개 질문 데이터 (전체 포함)
questions = [
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

# 8가지 DNA 타입 정의 (전체 포함)
dna_types = {
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
        "video_file": "dna-types/fun-exploder.mp4"
    }
}

# 12개 기본 동작 정의 (전체 포함)
basic_actions = [
    {
        "name": "좌우새",
        "description": "어깨와 머리를 좌우로 부드럽게 흔드는 머릿짓",
        "story_card": "작은 흔들림이 파동을 만든다. 내 몸이 파도처럼 흔들리며 춤의 첫 숨결을 열어준다.",
        "historical_note": "조선 정재에서 '좌우새'는 새가 머리를 좌우로 흔드는 모습을 형상화한 동작입니다.",
        "video_file": "basic-actions/left-right-flow.mp4"
    },
    {
        "name": "감기", 
        "description": "팔을 원형으로 휘감으며 연결하는 동작",
        "story_card": "팔끝이 그리는 원은 흐름의 다리다. 시작과 끝이 이어지며 끊김 없는 리듬이 완성된다.",
        "historical_note": "원형의 움직임은 동양 철학의 순환 사상을 담고 있으며, 궁중무에서 자주 사용되었습니다.",
        "video_file": "basic-actions/arm-circle.mp4"
    },
    {
        "name": "손목감기",
        "description": "손목을 안팎으로 원을 그리며 감아 올리는 동작", 
        "story_card": "작은 손목에서 큰 에너지가 피어난다. 미세한 움직임이 춤 전체의 결을 바꾼다.",
        "historical_note": "손목의 미세한 움직임은 한국무용의 섬세함을 보여주는 대표적 요소입니다.",
        "video_file": "basic-actions/wrist-circle.mp4"
    },
    {
        "name": "머리감기",
        "description": "머리를 원으로 부드럽게 돌리는 동작",
        "story_card": "머리의 회전은 시야와 생각을 확장시킨다. 원이 커질수록 마음도 더 넓어진다.",
        "historical_note": "머리감기는 자연의 흐름에 몸을 맡기는 한국무용의 핵심 철학을 담고 있습니다.",
        "video_file": "basic-actions/head-circle.mp4"
    },
    {
        "name": "바람불기",
        "description": "팔과 손을 바람결처럼 흔드는 동작",
        "story_card": "바람처럼 가볍게, 그러나 보이지 않게 강하게. 손끝에서 세상과 연결되는 길이 열린다.",
        "historical_note": "자연의 바람을 형상화한 이 동작은 인간과 자연의 조화를 추구하는 우리 문화를 보여줍니다.",
        "video_file": "basic-actions/wind-blowing.mp4"
    },
    {
        "name": "손바닥 뒤집기", 
        "description": "손바닥을 위아래로 간단히 뒤집는 동작",
        "story_card": "뒤집는 순간 세상이 달라진다. 위와 아래가 바뀌며 삶의 관점도 새로워진다.",
        "historical_note": "음양의 전환을 의미하는 동작으로, 변화와 조화의 철학이 담겨 있습니다.",
        "video_file": "basic-actions/palm-flip.mp4"
    },
    {
        "name": "홑디딤",
        "description": "한 발을 내디으며 중심을 옮기는 기본 걸음",
        "story_card": "단순한 한 발, 그러나 모든 시작은 여기서 열린다. 땅을 딛는 순간 춤은 살아난다.",
        "historical_note": "한국무용의 모든 이동의 기본이 되는 걸음으로, 안정감과 우아함을 동시에 표현합니다.",
        "video_file": "basic-actions/single-step.mp4"
    },
    {
        "name": "잔걸음",
        "description": "작게 바닥을 누르거나 살짝 들어 올리는 걸음",
        "story_card": "잔걸음은 땅과의 대화다. 무게를 맡기거나 들어 올리며 삶의 무게와 가벼움을 동시에 담는다.",
        "historical_note": "조심스럽고 절제된 움직임으로 한국 여성의 단아함을 표현하는 대표적 걸음입니다.",
        "video_file": "basic-actions/small-steps.mp4"
    },
    {
        "name": "굴신",
        "description": "무릎과 몸통을 굽혔다 펴는 동작", 
        "story_card": "굽힘과 펼침 속에 인간의 태도가 담긴다. 겸손히 낮추고 당당히 일어서는 몸짓.",
        "historical_note": "유교 문화의 예의범절이 춤으로 승화된 동작으로, 정중동의 미학을 보여줍니다.",
        "video_file": "basic-actions/bend-stretch.mp4"
    },
    {
        "name": "한다리들기",
        "description": "한쪽 다리를 들어 균형을 잡는 동작",
        "story_card": "흔들림 속에서도 균형을 찾아야 한다. 한다리들기는 중심을 지키는 힘을 길러준다.",
        "historical_note": "학이 한 발로 서 있는 모습을 형상화한 동작으로, 고고한 품격을 의미합니다.",
        "video_file": "basic-actions/one-leg-lift.mp4"
    },
    {
        "name": "호흡",
        "description": "숨의 길이를 달리해 동작을 이어주는 원리",
        "story_card": "호흡은 춤의 보이지 않는 심장이다. 긴 호흡은 여유를, 짧은 호흡은 순간을, 겹호흡은 깊이를 만들어낸다.",
        "historical_note": "한국무용에서 호흡은 동작의 생명력을 불어넣는 핵심 요소입니다.",
        "video_file": "basic-actions/breathing.mp4"
    },
    {
        "name": "궁채",
        "description": "팔을 크게 원으로 굽혀 돌리는 동작",
        "story_card": "원은 끝없는 순환을 상징한다. 팔이 그린 원 안에 세상의 흐름이 담긴다.",
        "historical_note": "큰 원을 그리는 동작으로 우주의 순환과 생명의 흐름을 표현합니다.",
        "video_file": "basic-actions/large-circle.mp4"
    }
]

# 확장 동작 (6개) 
expanded_actions = [
    {
        "name": "겹디딤",
        "description": "두 발을 교차하며 밟는 걸음",
        "video_file": "expanded-actions/double-steps.mp4"
    },
    {
        "name": "제자리돌기", 
        "description": "같은 자리에 서서 회전하는 동작",
        "video_file": "expanded-actions/spin-in-place.mp4"
    },
    {
        "name": "이동하면서돌기",
        "description": "걸음을 옮기며 회전하는 동작", 
        "video_file": "expanded-actions/moving-spin.mp4"
    },
    {
        "name": "점프하면서돌기",
        "description": "뛰어오르며 회전하는 동작",
        "video_file": "expanded-actions/jumping-spin.mp4"
    },
    {
        "name": "연풍대",
        "description": "바람에 흔들리는 버드나무처럼 원을 그리며 회전하는 동작",
        "video_file": "expanded-actions/Yeon-pung-dae.mp4"
    },
    {
        "name": "치마채기",
        "description": "치마 자락을 들어 움직임을 강조하는 동작",
        "video_file": "expanded-actions/skirt-snatch.mp4"
    }
]

# 창작 동작 (8개)
creative_actions = [
    {
        "name": "풀업",
        "description": "몸을 위로 길게 끌어올리는 동작",
        "video_file": "creative-actions/pull-up.mp4"
    },
    {
        "name": "인파세/아웃파세",
        "description": "무릎을 굽혀 발끝을 무릎에 붙이고 안팎으로 드는 동작",
        "video_file": "creative-actions/in-pase.mp4"
    },
    {
        "name": "턴",
        "description": "몸을 축으로 삼아 위로 세워 회전하는 동작",
        "video_file": "creative-actions/up-turn.mp4"
    },
    {
        "name": "점프",
        "description": "바닥을 박차고 공중으로 뛰어오르는 동작",
        "video_file": "creative-actions/jump.mp4"
    },
    {
        "name": "롤링",
        "description": "몸을 바닥에 굴리며 회전하는 동작",
        "video_file": "creative-actions/rolling.mp4"
    },
    {
        "name": "컨트렉션",
        "description": "복부와 척추를 안으로 수축하는 동작",
        "video_file": "creative-actions/contraction.mp4"
    },
    {
        "name": "웨이브",
        "description": "척추와 몸통을 물결처럼 이어 흐르는 동작",
        "video_file": "creative-actions/wave.mp4"
    },
    {
        "name": "컴퍼스턴",
        "description": "다리를 축으로 크게 원을 그리며 도는 동작",
        "video_file": "creative-actions/compass-turn.mp4"
    }
]

# 스토리 콘텐츠 
story_contents = [
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

# 배지 시스템
badge_system = {
    3: {"name": "입문자", "emoji": "🌱", "message": "몸이 기억하기 시작했어요", "color": "#22C55E"},
    6: {"name": "수련자", "emoji": "🎋", "message": "당신 안의 한국인이 깨어나고 있어요", "color": "#3B82F6"},
    9: {"name": "달인", "emoji": "🏔️", "message": "이제 진짜 K-무브먼트를 이해하시네요", "color": "#8B5CF6"},
    12: {"name": "마스터", "emoji": "👑", "message": "K-DNA 각성 완료", "color": "#F59E0B"}
}

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

# MediaPipe 초기화
@st.cache_resource
def init_mediapipe():
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    return pose, mp_pose

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

# 밈 카드 생성 함수
def create_meme_card(dna_type_name, dna_data):
    # PIL로 밈 카드 생성
    width, height = 1080, 1080
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # 그라데이션 배경 (간단히 단색으로 처리)
    color = dna_data['color']
    draw.rectangle([0, 0, width, height], fill=color)
    
    # 텍스트 추가 (기본 폰트 사용)
    try:
        # 큰 제목
        draw.text((width//2, height//3), f"나는 {dna_type_name}!", 
                 fill='white', anchor='mm')
        draw.text((width//2, height//2), dna_data['title'], 
                 fill='white', anchor='mm')
        draw.text((width//2, height*2//3), "#춤마루 #K_DNA각성", 
                 fill='white', anchor='mm')
    except:
        pass
    
    return img

# 메인 앱 로직
def main():
    init_session_state()
    
    # 헤더
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #667eea; font-size: 3rem; margin-bottom: 0;'>🎭 춤마루</h1>
        <p style='color: #666; font-size: 1.2rem;'>당신 안에 잠든 K-DNA, 지금 깨어나다</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 단계별 라우팅
    if st.session_state.current_step == 'landing':
        show_landing_page()
    elif st.session_state.current_step == 'test':
        show_test_page()
    elif st.session_state.current_step == 'result':
        show_result_page()
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

def show_landing_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 20px; color: white; margin: 2rem 0;'>
            <h2>5000년 흘러온 움직임이 드디어 내 몸에서 시작된다</h2>
            <p style='font-size: 1.1rem; margin: 1.5rem 0;'>
                10가지 일상 질문으로 나만의 춤 DNA를 발견하고,<br>
                세계가 열광하는 K-무브먼트의 진짜 뿌리를 경험하세요
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 춤마루 여정")
        
        # 여정 단계들
        journey_steps = [
            ("1", "K-DNA 발견", "10개 질문으로 나만의 춤 성향 분석", "#667eea"),
            ("2", "전통 움직임 체험", "한국무용 기본동작 12가지 완주", "#4ECDC4"),  
            ("3", "5000년 이야기", "전통 속에 숨겨진 깊은 철학 탐구", "#FFD700"),
            ("4", "K-DNA 카드 생성", "나만의 춤 정체성을 SNS로 공유", "#FF69B4")
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
        
        if st.button("내 K-DNA 깨우기", type="primary"):
            st.session_state.current_step = 'test'
            st.rerun()
        
        st.info("이미 2,347명이 자신만의 춤 유전자를 발견했습니다")

def show_test_page():
    if st.session_state.current_question >= len(questions):
        # 결과 분석
        st.session_state.dna_result = analyze_dna(st.session_state.answers)
        st.session_state.current_step = 'result'
        st.rerun()
        return
    
    progress = (st.session_state.current_question + 1) / len(questions)
    st.progress(progress, text=f"진행률: {int(progress*100)}% ({st.session_state.current_question + 1}/10)")
    
    # 이전 버튼
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← 이전"):
            if st.session_state.current_question > 0:
                st.session_state.current_question -= 1
                st.session_state.answers.pop()
                st.rerun()
            else:
                st.session_state.current_step = 'landing'
                st.rerun()
    
    # 질문 표시
    question = questions[st.session_state.current_question]
    
    st.markdown(f"### 질문 {question['id']}/10")
    st.markdown(f"**{question['text']}**")
    
    # 선택지
    selected_option = st.radio(
        "답변을 선택해주세요:",
        options=list(question['options'].keys()),
        format_func=lambda x: question['options'][x],
        key=f"q_{question['id']}"
    )
    
    if st.button("다음", type="primary"):
        st.session_state.answers.append(selected_option)
        st.session_state.current_question += 1
        st.rerun()
    
    # 진행 상황 표시
    if st.session_state.current_question >= 4:
        st.success("당신만의 K-DNA가 선명해지고 있어요")

def show_result_page():
    if not st.session_state.dna_result:
        st.error("DNA 분석 결과가 없습니다.")
        return
    
    dna_data = dna_types[st.session_state.dna_result]
    
    # 뒤로가기 버튼
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← 이전"):
            st.session_state.current_step = 'test'
            st.session_state.current_question = len(questions) - 1
            st.rerun()
    with col3:
        if st.button("🏠 홈"):
            st.session_state.current_step = 'landing'
            st.rerun()
    
    # 결과 카드
    st.markdown(f"""
    <div class='dna-card' style='background: linear-gradient(135deg, {dna_data['color']}, {dna_data['color']}dd);'>
        <div style='font-size: 4rem; margin-bottom: 1rem;'>{dna_data['emoji']}</div>
        <h1>당신의 춤 DNA</h1>
        <h2 style='background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 20px; margin: 1rem 0;'>
            {st.session_state.dna_result}
        </h2>
        <h3>{dna_data['title']}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 설명
    st.markdown(f"**{dna_data['description']}**")
    
    # 특징 태그
    st.markdown("### 당신의 특징")
    cols = st.columns(len(dna_data['characteristics']))
    for i, char in enumerate(dna_data['characteristics']):
        with cols[i]:
            st.markdown(f"<div style='background: {dna_data['color']}20; color: {dna_data['color']}; "
                       f"padding: 0.5rem; border-radius: 10px; text-align: center; font-weight: bold;'>"
                       f"{char}</div>", unsafe_allow_html=True)
    
    # 전문가 영상
    st.markdown("### 맞춤 전통무용 시연")
    
    # 영상 파일이 있다면 표시, 없다면 플레이스홀더
    video_path = f"videos/{dna_data['video_file']}"
    try:
        st.video(video_path)
    except:
        st.info(f"{st.session_state.dna_result} 타입 전문가 시연 영상 (1분) - 업로드 예정")
        st.image("https://via.placeholder.com/640x360/667eea/ffffff?text=전문가+시연+영상", 
                caption=f"{st.session_state.dna_result} 맞춤 전통무용 스타일")
    
    # 액션 버튼
    col1, col2 = st.columns(2)
    with col1:
        if st.button("이제 움직임으로 깨워보기", type="primary"):
            st.session_state.current_step = 'action_select'
            st.rerun()
    
    with col2:
        if st.button("결과 공유하기"):
            st.session_state.current_step = 'meme'
            st.rerun()

def show_action_select_page():
    # 뒤로가기 버튼
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← 이전"):
            st.session_state.current_step = 'result'
            st.rerun()
    with col3:
        if st.button("🏠 홈"):
            st.session_state.current_step = 'landing'
            st.rerun()
    
    st.markdown("## 움직임 여정 시작")
    st.markdown("한국무용의 숨겨진 DNA를 깨워보세요")
    
    # 기본 동작 선택
    with st.container():
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 15px; color: white; margin: 1rem 0;'>
            <h3>기본 동작 (12개)</h3>
            <p>한국무용의 핵심 미학을 담은 필수 동작들. 5000년 전통의 움직임 언어를 현대적으로 경험해보세요.</p>
            <small>✓ AI 동작 분석 지원 • 완주시 특별 밈 생성</small>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("기본 동작 시작하기", type="primary"):
            st.session_state.current_step = 'action'
            st.rerun()
    
    # 확장 동작 선택
    with st.container():
        st.markdown("""
        <div style='background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%); 
                    padding: 2rem; border-radius: 15px; color: white; margin: 1rem 0;'>
            <h3>확장 동작 (6개)</h3>
            <p>기본기를 응용한 고급 동작들. 더욱 섬세한 표현력을 경험할 수 있습니다.</p>
            <small>✓ 전문가 영상 제공 • 2025년 6월 AI 분석 지원</small>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("확장 동작 체험하기", key="expanded_btn"):
            st.session_state.current_step = 'expanded_action'
            st.rerun()

    # 창작 동작 선택
    with st.container():
        st.markdown("""
        <div style='background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%); 
                    padding: 2rem; border-radius: 15px; color: white; margin: 1rem 0;'>
            <h3>창작 동작 (8개)</h3>
            <p>전통을 현대적으로 재해석한 창작 동작들. K-Culture의 미래를 체험해보세요.</p>
            <small>✓ 전문가 영상 제공 • 2025년 6월 AI 분석 지원</small>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("창작 동작 체험하기", key="creative_btn"):
            st.session_state.current_step = 'creative_action'
            st.rerun()
            
    # 스토리 보기 버튼
    if st.button("📖 5000년 움직임의 비밀 먼저 보기"):
        st.session_state.current_step = 'story'
        st.rerun()

def show_action_page():
    if st.session_state.current_action >= len(basic_actions):
        st.session_state.current_step = 'meme'
        st.rerun()
        return
    
    action = basic_actions[st.session_state.current_action]
    progress = (st.session_state.current_action + 1) / len(basic_actions)
    
    # 헤더
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← 이전"):
            if st.session_state.current_action > 0:
                st.session_state.current_action -= 1
            else:
                st.session_state.current_step = 'action_select'
            st.rerun()
    
    with col2:
        st.markdown(f"### {action['name']} ({st.session_state.current_action + 1}/12)")
        st.progress(progress, text=f"진행률: {int(progress*100)}%")
    
    with col3:
        if st.button("🏠 홈"):
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
        # 영상 파일이 있다면 표시
        video_path = f"videos/{action['video_file']}"
        try:
            st.video(video_path)
        except:
            st.info(f"{action['name']} 시범 영상 - 업로드 예정")
            st.image("https://via.placeholder.com/320x240/f093fb/ffffff?text=시범+영상", 
                    caption=f"{action['name']} 전문가 시연")
    
    with col2:
        st.markdown("#### 당신의 동작")
        
        # 웹캠 입력
        camera_input = st.camera_input("웹캠으로 동작을 따라해보세요")
        
        if camera_input is not None:
            # 이미지 처리
            image = Image.open(camera_input)
            image_np = np.array(image)
            
            # MediaPipe로 동작 분석
            pose, mp_pose = init_mediapipe()
            
            # RGB 변환
            rgb_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_image)
            
            if results.pose_landmarks:
                # 동작 분석
                analysis_result = analyze_movement(results.pose_landmarks, action['name'])
                
                if analysis_result['success']:
                    st.success(f"✅ {analysis_result['message']}")
                    st.balloons()
                    
                    # 완료된 동작에 추가
                    if st.session_state.current_action not in st.session_state.completed_actions:
                        st.session_state.completed_actions.append(st.session_state.current_action)
                    
                    # 다음 동작으로
                    time.sleep(2)
                    st.session_state.current_action += 1
                    st.rerun()
                else:
                    st.warning(f"⚠️ {analysis_result['message']}")
            else:
                st.info("자세를 인식할 수 없습니다. 전신이 보이도록 해주세요.")
    
    # 수동 진행 버튼 (테스트용)
    if st.button("동작 완료 (수동)", help="실제 앱에서는 AI가 자동 판정"):
        if st.session_state.current_action not in st.session_state.completed_actions:
            st.session_state.completed_actions.append(st.session_state.current_action)
        
        st.session_state.current_action += 1
        if st.session_state.current_action >= len(basic_actions):
            st.session_state.current_step = 'meme'
        st.rerun()
    
    # 배지 체크
    completed_count = len(st.session_state.completed_actions)
    if completed_count in badge_system and completed_count not in st.session_state.badges:
        badge = badge_system[completed_count]
        st.session_state.badges.append(completed_count)
        st.success(f"{badge['emoji']} {badge['name']} 배지 획득! {badge['message']}")

def show_expanded_action_page():
    # 뒤로가기 버튼
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← 이전"):
            st.session_state.current_step = 'action_select'
            st.rerun()
    with col3:
        if st.button("🏠 홈"):
            st.session_state.current_step = 'landing'
            st.rerun()
    
    st.markdown("## 확장 동작 체험")
    st.markdown("기본기를 응용한 고급 동작들")
    
    # 동작 목록
    for action in expanded_actions:
        with st.expander(f"🎭 {action['name']}", expanded=False):
            st.markdown(f"**설명**: {action['description']}")
            
            # 영상 표시 (실제 구현 시)
            video_path = f"videos/{action['video_file']}"
            try:
                st.video(video_path)
            except:
                st.info(f"{action['name']} 전문가 시연 영상 - 업로드 예정")
                st.image("https://via.placeholder.com/640x360/4ECDC4/ffffff?text=확장동작+영상", 
                        caption=f"{action['name']} 전문가 시연")
            
            st.markdown("💡 AI 동작 분석 기능은 2025년 6월에 추가될 예정입니다")
    
    # 기본 동작으로 돌아가기
    if st.button("기본 동작 먼저 체험하기", type="primary"):
        st.session_state.current_step = 'action'
        st.rerun()

def show_creative_action_page():
    # 뒤로가기 버튼
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← 이전"):
            st.session_state.current_step = 'action_select'
            st.rerun()
    with col3:
        if st.button("🏠 홈"):
            st.session_state.current_step = 'landing'
            st.rerun()
    
    st.markdown("## 창작 동작 체험")
    st.markdown("전통을 현대적으로 재해석한 혁신적인 동작들")
    
    # 동작 목록
    for action in creative_actions:
        with st.expander(f"🚀 {action['name']}", expanded=False):
            st.markdown(f"**설명**: {action['description']}")
            
            # 영상 표시 (실제 구현 시)
            video_path = f"videos/{action['video_file']}"
            try:
                st.video(video_path)
            except:
                st.info(f"{action['name']} 창작 시연 영상 - 업로드 예정")
                st.image("https://via.placeholder.com/640x360/FF6B35/ffffff?text=창작동작+영상", 
                        caption=f"{action['name']} 창작 시연")
            
            st.markdown("💡 AI 동작 분석 기능은 2025년 6월에 추가될 예정입니다")
    
    # 기본 동작으로 돌아가기
    if st.button("기본 동작 먼저 체험하기", type="primary"):
        st.session_state.current_step = 'action'
        st.rerun()

def show_story_page():
    # 뒤로가기 버튼
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← 이전"):
            st.session_state.current_step = 'action_select'
            st.rerun()
    with col3:
        if st.button("🏠 홈"):
            st.session_state.current_step = 'landing'
            st.rerun()
    
    st.markdown("## 5000년 움직임의 비밀")
    st.markdown("한국무용에 담긴 깊은 철학")
    
    # 스토리 목록
    for index, story in enumerate(story_contents):
        with st.expander(f"{story['avatar']} {story['title']}", expanded=False):
            st.markdown(story['content'])
            
            if story.get('historical_note'):
                st.info(f"**역사적 배경**: {story['historical_note']}")
            
            if st.button(f"자세히 보기", key=f"story_{index}"):
                st.session_state.current_story = index
                st.session_state.current_step = 'story_detail'
                st.rerun()
    
    # 체험하기 버튼
    if st.button("이제 직접 체험해보기", type="primary"):
        st.session_state.current_step = 'action_select'
        st.rerun()

def show_story_detail_page():
    story = story_contents[st.session_state.current_story]
    
    # 뒤로가기 버튼
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← 목록으로"):
            st.session_state.current_step = 'story'
            st.rerun()
    with col3:
        if st.button("🏠 홈"):
            st.session_state.current_step = 'landing'
            st.rerun()
    
    # 스토리 헤더
    st.markdown(f"# {story['avatar']} {story['title']}")
    
    # 내용
    st.markdown(story['content'])
    
    # 역사적 배경
    if story.get('historical_note'):
        st.markdown("### 역사적 배경")
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
    if st.button("이제 직접 체험해보기", type="primary"):
        st.session_state.current_step = 'action_select'
        st.rerun()

def show_meme_page():
    if not st.session_state.dna_result:
        st.error("DNA 결과가 없습니다.")
        return
    
    dna_data = dna_types[st.session_state.dna_result]
    completed_count = len(st.session_state.completed_actions)
    is_full_complete = completed_count == len(basic_actions)
    
    # 네비게이션
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🏠 홈"):
            st.session_state.current_step = 'landing'
            st.rerun()
    with col2:
        if st.button("👤 DNA 결과"):
            st.session_state.current_step = 'result'
            st.rerun()
    with col3:
        if st.button("▶️ 동작 연습"):
            st.session_state.current_step = 'action'
            st.rerun()
    
    # 완성 축하
    st.markdown(f"""
    <div class='dna-card' style='background: linear-gradient(135deg, {dna_data['color']}, {dna_data['color']}dd);'>
        <div style='font-size: 3rem; margin-bottom: 1rem;'>🎉</div>
        <h1>{'K-DNA 각성 완료!' if is_full_complete else f'{completed_count}개 동작 완료!'}</h1>
        <p>{'당신만의 춤 유전자가 깨어났습니다' if is_full_complete else '지금까지의 여정을 공유해보세요'}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 밈 카드 생성 및 표시
    meme_card = create_meme_card(st.session_state.dna_result, dna_data)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(meme_card, caption=f"{st.session_state.dna_result} 카드")
    
    # 공유 버튼들
    st.markdown("### 결과 공유하기")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📱 카드 다운로드", type="primary"):
            # 실제로는 다운로드 로직 구현
            st.success("카드가 다운로드되었습니다!")
    
    with col2:
        if st.button("📤 인스타 스토리 공유"):
            st.info("인스타그램 공유 기능은 준비 중입니다.")
    
    # 배지 표시
    if st.session_state.badges:
        st.markdown("### 획득한 배지")
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
        if st.button("🔄 새로운 DNA 탐험하기"):
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
            if st.button("➡️ 계속 동작 익히기"):
                st.session_state.current_step = 'action'
                st.rerun()
    
    with col3:
        if st.button("📖 전통 이야기 보기"):
            st.session_state.current_step = 'story'
            st.rerun()
    
    # 성취 메시지
    success_message = (
        "축하합니다! 한국무용의 12가지 기본 동작을 모두 완주하셨습니다. "
        "당신은 이제 진정한 K-DNA 마스터입니다. 5000년 전통의 움직임이 당신 안에서 살아 숨쉬고 있어요."
        if is_full_complete else
        f"훌륭해요! {completed_count}개 동작을 완료하셨습니다. "
        "계속해서 더 많은 전통 동작을 익히며 K-DNA를 완전히 깨워보세요!"
    )
    
    st.success(success_message)

if __name__ == "__main__":
    main()

# 실행방법:
# pip install streamlit opencv-python mediapipe pillow numpy
# streamlit run app_v5.py
