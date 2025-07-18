import streamlit as st
from openai import OpenAI

# 클라이언트 설정
client = OpenAI(
    base_url="https://guest-api.sktax.chat/v1",
    api_key="sktax-XyeKFrq67ZjS4EpsDlrHHXV8it"
)

st.title("에이닷 엑스 4.0 UI (trained by SKT, using Quen2.5 Engine)")

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "generating" not in st.session_state:
    st.session_state["generating"] = False

# 1. 대화 내역 먼저 출력
for q, a, file_info in st.session_state["messages"]:
    st.markdown(f"**질문:** {q}")
    st.markdown(f"**AI 답변:** {a}")
    if file_info:
        st.markdown(f"**첨부파일:** {file_info}")

# 2. 입력 폼을 코드의 마지막에 배치 (최하단)
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("질문을 입력하세요:", key="user_input")
    uploaded_file = st.file_uploader("첨부파일 선택 (선택)", type=None)
    submit_btn = st.form_submit_button(
        "질문하기",
        disabled=st.session_state["generating"]
    )

if submit_btn and user_input and not st.session_state["generating"]:
    st.session_state["generating"] = True
    with st.spinner("AI가 답변을 생성 중입니다..."):
        clean_input = user_input.encode("utf-8", "surrogatepass").decode("utf-8", "ignore")
        file_info = None
        if uploaded_file is not None:
            file_info = f"{uploaded_file.name} ({uploaded_file.size} bytes)"
            # 텍스트 파일이면 내용을 AI에 추가
            try:
                file_content = uploaded_file.read().decode('utf-8', errors='ignore')
                clean_input += f"\n[첨부파일: {uploaded_file.name} 내용]\n{file_content}"
            except Exception:
                # 텍스트 파일이 아니면 이름만 전달
                clean_input += f"\n[첨부파일: {uploaded_file.name} (텍스트 아님)]"
        try:
            completion = client.chat.completions.create(
                model="ax4",
                messages=[{"role": "user", "content": clean_input}]
            )
            answer = completion.choices[0].message.content
            st.session_state["messages"].append((user_input, answer, file_info))
        except Exception as e:
            answer = f"에러 발생: {e}"
            st.session_state["messages"].append((user_input, answer, file_info))
    st.session_state["generating"] = False
    st.rerun()
