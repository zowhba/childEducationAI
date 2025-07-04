import streamlit as st
import requests
from urllib.parse import urljoin
from dotenv import load_dotenv
import os
import sqlite3
from datetime import datetime
import re
from collections import Counter
import json

# 환경변수 로드
load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")
DB_PATH = "./child_edu_ai.db"

# DB 유틸 함수
@st.cache_resource
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY,
            name TEXT,
            pw TEXT,
            age INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id TEXT,
            lesson_id TEXT,
            date TEXT,
            title TEXT,
            content TEXT,
            materials_text TEXT,
            feedback TEXT,
            PRIMARY KEY (id, lesson_id)
        )
    """)
    conn.commit()
init_db()

# DB 연동 함수
def add_account(id, name, pw, age):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO accounts (id, name, pw, age) VALUES (?, ?, ?, ?)", (id, name, pw, age))
    conn.commit()

def get_account(id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, name, pw, age FROM accounts WHERE id=?", (id,))
    row = c.fetchone()
    if row:
        return {"id": row[0], "name": row[1], "pw": row[2], "age": row[3]}
    return None

def add_history(id, lesson_id, date, title, content, materials_text, feedback=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO history (id, lesson_id, date, title, content, materials_text, feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (id, lesson_id, date, title, content, materials_text, feedback))
    conn.commit()

def get_history(id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT lesson_id, date, title, content, materials_text, feedback FROM history WHERE id=? ORDER BY date DESC", (id,))
    rows = c.fetchall()
    return [
        {"lesson_id": r[0], "date": r[1], "title": r[2], "content": r[3], "materials_text": r[4], "feedback": r[5]}
        for r in rows
    ]

def update_feedback(id, lesson_id, feedback):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE history SET feedback=? WHERE id=? AND lesson_id=?", (feedback, id, lesson_id))
    conn.commit()

def render_child_friendly_materials(materials_text):
    lines = materials_text.split('\n')
    output = []
    q_num = 1
    in_choices = False
    for line in lines:
        # 문제 번호 감지
        m = re.match(r'【문제 (\d+)】', line)
        if m:
            num = int(m.group(1))
            emoji = ['🎈', '🐻', '🦄', '🦊', '🐧'][min(num-1, 4)]
            output.append(f"\n---\n\n#### {emoji} 문제 {num}\n")
            q_num = num
            in_choices = False
            continue
        # 객관식 보기는 ①~④
        m = re.match(r'\s*([①②③④])', line)
        if m:
            color_emoji = {'①': '🔵', '②': '🟢', '③': '🟡', '④': '🟣'}
            emoji = color_emoji.get(m.group(1), '⚪')
            output.append(f"{emoji} {line.strip()}\n")
            in_choices = True
            continue
        # 정답 입력란
        if '답안:' in line or '정답:' in line:
            if in_choices:
                output.append("\n✏️ **정답:** (     )\n")
            elif '단답형' in materials_text or q_num == 4:
                output.append("\n✏️ **정답:** _______________\n")
            elif '서술형' in materials_text or q_num == 5:
                output.append("\n✏️ **정답:**\n____________________________\n____________________________\n____________________________\n")
            in_choices = False
            continue
        # 일반 텍스트(문제 설명 등)
        if line.strip():
            output.append(f"{line.strip()}\n")
    output.append("\n---\n")
    return ''.join(output)

def remove_markdown_links(text):
    # [텍스트](링크) → 텍스트
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # [텍스트] → 텍스트
    text = re.sub(r'\[([^\]]+)\]', r'\1', text)
    return text

def get_unused_categories(user_interests):
    CATEGORIES = {
        "과학": ["과학", "천체", "물리", "화학", "생물", "마찰력", "표면장력", "천체물리학", "우주", "실험"],
        "예술": ["예술", "미술", "음악", "그림", "공예", "연주", "작곡"],
        "스포츠": ["스포츠", "축구", "야구", "농구", "운동", "달리기"],
        "동물": ["동물", "강아지", "고양이", "토끼", "오징어", "포켓몬스터"],
        "모험": ["모험", "탐험", "여행", "탐사", "모험이야기"],
    }
    used_cats = set()
    for interest in user_interests:
        for cat, keywords in CATEGORIES.items():
            if any(k in interest for k in keywords):
                used_cats.add(cat)
    unused = [cat for cat in CATEGORIES if cat not in used_cats]
    return unused

def get_history_for_feedback(history):
    result = []
    for item in history:
        # title에서 관심사 추출
        m = re.findall(r'\((.*?)\)', item['title'])
        interests = m[0] if m else ""
        # content에서 주제 추출
        topic = item['content'].split('\n')[0][:30] if item['content'] else ""
        feedback = item.get('feedback', '') or ""  # None/null을 빈 문자열로 보정
        result.append({
            "interests": interests,
            "topic": topic,
            "feedback": feedback
        })
    return result

def render_overall_feedback(history):
    # 관심사, 학습 주제, 피드백 요약 추출
    interests = []
    topics = []
    feedbacks = []
    for item in history:
        # 관심사 추출 (title이 (관심사1, 관심사2) 형식)
        m = re.findall(r'\((.*?)\)', item['title'])
        if m:
            for s in m[0].split(','):
                s = s.strip()
                if s:
                    interests.append(s)
        # 학습 주제(lesson content의 첫 줄)
        if item['content']:
            topic_line = item['content'].split('\n')[0][:30]
            topics.append(remove_markdown_links(topic_line))
        # 피드백
        if item.get('feedback'):
            feedbacks.append(remove_markdown_links(item['feedback']))
    interest_cnt = Counter(interests)
    topic_cnt = Counter(topics)
    # 피드백 요약(가장 많이 등장하는 단어)
    feedback_text = ' '.join(feedbacks)
    words = [w for w in re.findall(r'\w+', feedback_text) if len(w) > 1]
    word_cnt = Counter(words)
    common_words = ', '.join([w for w, _ in word_cnt.most_common(3)])
    # 추천 관심사 카테고리
    unused_cats = get_unused_categories(interests)
    if unused_cats:
        recommend_str = f"- 새로운 관심사(예: {', '.join(unused_cats)})로도 교재를 생성해보세요!\n"
    else:
        recommend_str = "- 다양한 관심사로 교재를 생성해보세요!\n"
    # 마크다운 종합 피드백 (대괄호 없이)
    md = [
        "# 📊 나의 학습 분석\n",
        f"- **관심사:** " + ', '.join([f"{k}({v}회)" for k, v in interest_cnt.most_common()]) if interest_cnt else "- **관심사:** 없음",
        f"- **학습 주제:** " + ', '.join([f"{k}({v}회)" for k, v in topic_cnt.most_common()]) if topic_cnt else "- **학습 주제:** 없음",
        f"- **AI 피드백 요약:** {common_words if common_words else '아직 피드백이 충분하지 않아요!'}\n",
        "## 📝 앞으로 이런 학습을 추천해요!",
        "- 서술형 문제에서 예시를 더 많이 써보세요.",
        recommend_str
    ]
    return '\n'.join(md)

# 세션 상태 최소화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "child_id" not in st.session_state:
    st.session_state.child_id = None
if "child_name" not in st.session_state:
    st.session_state.child_name = None
if "child_pw" not in st.session_state:
    st.session_state.child_pw = None
if "child_age" not in st.session_state:
    st.session_state.child_age = None
if "selected_lesson" not in st.session_state:
    st.session_state.selected_lesson = None
if "show_login" not in st.session_state:
    st.session_state.show_login = False
if "show_register" not in st.session_state:
    st.session_state.show_register = False
if "feedback" not in st.session_state:
    st.session_state.feedback = None

# 쿼리 파라미터로 동작 제어
action = st.query_params.get("action", "")

if action == "login":
    st.session_state.show_login = True
    st.session_state.show_register = False
elif action == "register":
    st.session_state.show_register = True
    st.session_state.show_login = False
elif action == "logout":
    st.session_state.logged_in = False
    st.session_state.child_id = None
    st.session_state.child_name = None
    st.session_state.child_pw = None
    st.session_state.child_age = None
    st.session_state.selected_lesson = None
    st.rerun()

# 앱 타이틀 및 버튼 한 줄 배치
st.set_page_config(page_title="어린이 맞춤형 교재 생성기", layout="wide")
col_title, col1, col2, col3, col4 = st.columns([8, 1, 1, 1, 1])
with col_title:
    st.markdown("### 어린이 맞춤형 교재 생성기")
with col1:
    if not st.session_state.logged_in:
        st.markdown('<div style="background-color:#ffe4e1; padding:4px; border-radius:8px;">', unsafe_allow_html=True)
        if st.button("🔑 Login", key="top_login_btn"):
            st.session_state.show_login = True
            st.session_state.show_register = False
        st.markdown('</div>', unsafe_allow_html=True)
with col2:
    if not st.session_state.logged_in:
        st.markdown('<div style="background-color:#e0ffe1; padding:4px; border-radius:8px;">', unsafe_allow_html=True)
        if st.button("🧒 Regist", key="top_register_btn"):
            st.session_state.show_register = True
            st.session_state.show_login = False
        st.markdown('</div>', unsafe_allow_html=True)
with col3:
    if st.session_state.logged_in:
        st.markdown('<div style="background-color:#e1e7ff; padding:4px; border-radius:8px;">', unsafe_allow_html=True)
        if st.button("🚪 Logout", key="top_logout_btn"):
            st.session_state.logged_in = False
            st.session_state.child_id = None
            st.session_state.child_name = None
            st.session_state.child_pw = None
            st.session_state.child_age = None
            st.session_state.selected_lesson = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# 아동 프로필 생성 입력 폼 (모달 대체)
if st.session_state.show_register:
    st.markdown("### 아동 프로필 생성")
    reg_id = st.text_input("ID", key="reg_id")
    reg_name = st.text_input("이름", key="reg_name")
    reg_pw = st.text_input("PW", type="password", key="reg_pw")
    reg_age = st.number_input("나이", min_value=3, max_value=18, step=1, key="reg_age")
    if st.button("등록", key="register_btn"):
        if reg_id and reg_name and reg_pw and reg_age:
            if get_account(reg_id):
                st.warning("이미 존재하는 ID입니다. 다른 ID를 입력하세요.")
            else:
                add_account(reg_id, reg_name, reg_pw, reg_age)
                st.session_state.child_id = reg_id
                st.session_state.child_name = reg_name
                st.session_state.child_pw = reg_pw
                st.session_state.child_age = reg_age
                st.session_state.logged_in = True
                st.session_state.show_register = False
        else:
            st.warning("모든 정보를 입력하세요.")
    if st.button("닫기", key="close_register"):
        st.session_state.show_register = False
    st.stop()

# 로그인 입력 폼 (모달 대체)
if st.session_state.show_login:
    st.markdown("### 로그인")
    login_id = st.text_input("ID", key="login_id")
    login_pw = st.text_input("PW", type="password", key="login_pw")
    if st.button("로그인", key="login_btn"):
        if login_id and login_pw:
            acc = get_account(login_id)
            if acc and acc["pw"] == login_pw:
                st.session_state.child_id = login_id
                st.session_state.child_name = acc["name"]
                st.session_state.child_pw = login_pw
                st.session_state.child_age = acc["age"]
                st.session_state.logged_in = True
                st.session_state.show_login = False
                st.rerun()
            else:
                st.warning("ID 또는 PW가 일치하지 않습니다.")
        else:
            st.warning("ID, PW를 입력하세요.")
    if st.button("닫기", key="close_login"):
        st.session_state.show_login = False
    st.stop()

# 로그인 전 메인
if not st.session_state.logged_in:
    st.markdown("""
    # 어린이 맞춤형 AI 학습 서비스
    아동의 흥미와 수준에 맞는 교재와 피드백을 제공합니다.\n
    1. 우측 상단에서 아동 프로필을 생성하거나 로그인하세요.\n
    2. 로그인 후 학습 이력, 새 교재 생성, 문제 풀이 및 피드백을 경험할 수 있습니다.
    """)
else:
    acc = get_account(st.session_state.child_id)
    with st.sidebar:
        st.markdown("#### 새 교재 생성")
        interests = st.text_input("관심사 입력", key="interest_input")
        if st.button("교재 생성", key="create_lesson_btn"):
            interests_list = [s.strip() for s in interests.split(',') if s.strip()]
            interests_str = ', '.join(interests_list)
            payload = {
                "child_id": acc["id"],
                "name": acc["name"],
                "age": int(acc["age"]),
                "interests": interests_list
            }
            resp = requests.post(urljoin(API_URL, "/init_profile"), json=payload)
            if resp.status_code == 200:
                data = resp.json()
                lesson_item = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "title": f"({interests_str})",
                    "lesson_id": data["lesson_id"],
                    "content": data["lesson"],
                    "materials_text": data["materials_text"],
                    "feedback": None
                }
                add_history(acc["id"], lesson_item["lesson_id"], lesson_item["date"], lesson_item["title"], lesson_item["content"], lesson_item["materials_text"])
                st.session_state.selected_lesson = lesson_item
                st.session_state.feedback = None
                st.success("✅ 교재가 생성되었습니다! 메인 화면에서 확인하세요.")
            else:
                st.error(f"오류 발생: {resp.text}")
        st.markdown("---")
        st.markdown(f"### {acc['name']}님의 학습 이력")
        history = get_history(acc["id"])
        if history:
            for idx, item in enumerate(history):
                if st.button(f"{item['date']} {item['title']}", key=f"lesson_{idx}"):
                    st.session_state.selected_lesson = item

    # 메인: 학습 상세/진행
    if st.session_state.selected_lesson:
        lesson = st.session_state.selected_lesson
        st.markdown(f"### {lesson['title']}")
        st.write(lesson['content'])
        st.markdown("#### 문제지 🎉")
        st.markdown(render_child_friendly_materials(lesson['materials_text']), unsafe_allow_html=True)
        st.markdown("#### 문제 답변 입력")
        answer_inputs = []
        for i in range(5):
            answer = st.text_input(f"{i+1}번 문제 정답", key=f"answer_{i+1}", placeholder=f"{i+1}번 문제 정답 :")
            answer_inputs.append(answer)
        if st.button("문제 제출", key="submit_assessment_btn"):
            responses_text = "\n".join(answer_inputs)
            payload = {
                "child_id": acc["id"],
                "lesson_id": lesson["lesson_id"],
                "responses_text": responses_text,
                "materials_text": lesson["materials_text"]
            }
            try:
                print(json.dumps(payload, ensure_ascii=False))
                resp = requests.post(urljoin(API_URL, "/submit_assessment"), json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.feedback = data["feedback"]
                    update_feedback(acc["id"], lesson["lesson_id"], data["feedback"])
                    st.success("✅ 평가가 제출되었습니다! 피드백을 확인하세요.")
                else:
                    st.error(f"오류 발생: {resp.text}")
            except Exception as e:
                st.error(f"요청 중 오류 발생: {e}")
        # 피드백은 문제 제출 후에만 노출
        if (lesson.get("feedback") or st.session_state.feedback) and any(ans.strip() for ans in answer_inputs):
            st.markdown("#### 피드백 결과")
            st.write(st.session_state.feedback or lesson.get("feedback"))
    else:
        if history:
            history_for_feedback = get_history_for_feedback(history)
            payload = {
                "name": acc["name"],
                "age": acc["age"],
                "history": history_for_feedback
            }
            st.spinner("AI 종합 피드백을 작성중입니다. 잠시만 기다려주세요...")
            resp = requests.post(urljoin(API_URL, "/overall_feedback"), json=payload)
            if resp.status_code == 200:
                overall_feedback = resp.json().get("feedback", "")
                st.markdown("---")
                st.markdown("## 📊 AI 종합 피드백")
                st.markdown(overall_feedback, unsafe_allow_html=True)
            else:
                st.error("AI 종합 피드백 생성에 실패했습니다.")
        else:
            st.markdown("""
            # 👋 처음 오셨군요!

            1. 우측 상단 [Regist] 버튼으로 아이 프로필을 등록하세요.
            2. 좌측에서 관심사를 입력하고 [교재 생성]을 눌러 첫 학습을 시작하세요.
            3. 문제를 풀고 [문제 제출]을 누르면 AI가 피드백을 드려요!

            🎈 다양한 관심사로 여러 번 교재를 생성해보세요!
            """)

