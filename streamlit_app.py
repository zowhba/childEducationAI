import streamlit as st
import requests
from urllib.parse import urljoin
from dotenv import load_dotenv
import os

# 환경변수 로드
load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="어린이 맞춤형 교재 생성기", layout="centered")
st.title("🎓 어린이 맞춤형 교재 생성기")

# 탭 설정
tab1, tab2 = st.tabs(["프로필 등록 & 교재 생성", "평가 응답 & 피드백"])

with tab1:
    st.header("1. 아동 프로필 입력 및 교재 생성")
    child_id = st.text_input("아동 ID", key="id")
    name = st.text_input("이름", key="name")
    age = st.number_input("나이", min_value=3, max_value=18, step=1, key="age")
    interests = st.text_area("관심사 (쉼표로 구분)", key="interests")

    if st.button("교재 생성 요청", key="init_btn"):
        if not child_id or not name or not interests:
            st.error("모든 필드를 입력해주세요.")
        else:
            payload = {
                "child_id": child_id,
                "name": name,
                "age": int(age),
                "interests": [s.strip() for s in interests.split(',')]
            }
            resp = requests.post(urljoin(API_URL, "/init_profile"), json=payload)
            if resp.status_code == 200:
                data = resp.json()
                st.success("✅ 교재가 생성되었습니다! 2번 탭에서 확인하세요.")
                # 세션에 저장
                st.session_state.lesson_id = data["lesson_id"]
                st.session_state.child_id = child_id
                st.session_state.materials_text = data["materials_text"]
                st.session_state.lesson = data["lesson"]
            else:
                st.error(f"오류 발생: {resp.text}")

with tab2:
    st.header("2. 평가 문제 응답 및 피드백")
    if "materials_text" not in st.session_state or "lesson" not in st.session_state:
        st.info("먼저 1번 탭에서 교재 생성 후 진행하세요.")
    else:
        st.subheader("문제 및 답변 입력")
        st.write(st.session_state.lesson)
        st.write(st.session_state.materials_text)

        answer_inputs = []
        for i in range(5):
            answer = st.text_input(f"{i+1}번 문제 정답", key=f"answer_{i+1}", placeholder=f"{i+1}번 문제 정답 :")
            answer_inputs.append(answer)

        if st.button("평가 제출"):
            responses_text = "\n".join(answer_inputs)
            payload = {
                "child_id": st.session_state.child_id,
                "lesson_id": st.session_state.lesson_id,
                "responses_text": responses_text,
                "materials_text": st.session_state.materials_text
            }
            try:
                resp = requests.post(urljoin(API_URL, "/submit_assessment"), json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    st.success("✅ 평가가 제출되었습니다!")
                    st.subheader("피드백")
                    st.write(data["feedback"])
                    if data.get("next_lesson"):
                        st.subheader("다음 교재")
                        st.write(data["next_lesson"])
                else:
                    st.error(f"오류 발생: {resp.text}")
            except Exception as e:
                st.error(f"요청 중 오류 발생: {e}")
