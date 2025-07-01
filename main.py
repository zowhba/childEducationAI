from fastapi import FastAPI
from app.models.schemas import ChildProfileInput, LearningResponse, AssessmentInput, FeedbackResponse, EducationWorkflowState
from app.workflow.graph import create_init_profile_graph, create_assessment_graph
from dotenv import load_dotenv
import os

# 환경변수 로드
load_dotenv()

app = FastAPI(title="어린이 맞춤형 교재 생성기 API")

# LangGraph 워크플로우 초기화
init_profile_workflow = create_init_profile_graph()
assessment_workflow = create_assessment_graph()

@app.post("/init_profile", response_model=LearningResponse)
async def init_profile(profile: ChildProfileInput):
    """
    1) 아동 프로필 입력 받음
    2) 초기 학습 커리큘럼 생성
    3) 교재 및 문제 생성 후 반환
    """
    # LangGraph 워크플로우 실행
    initial_state = EducationWorkflowState(child_profile=profile)
    final_state = init_profile_workflow.invoke(initial_state)
    
    if final_state.get("learning_response"):
        return final_state["learning_response"]
    else:
        raise Exception("교재 생성에 실패했습니다.")

@app.post("/submit_assessment", response_model=FeedbackResponse)
async def submit_assessment(assessment: AssessmentInput):
    """
    1) 평가 응답 저장
    2) 피드백 생성
    3) 다음 교재 생성
    """
    # LangGraph 워크플로우 실행
    initial_state = EducationWorkflowState(assessment_input=assessment)
    final_state = assessment_workflow.invoke(initial_state)
    
    if final_state.get("feedback_response"):
        return final_state["feedback_response"]
    else:
        raise Exception("피드백 생성에 실패했습니다.")
