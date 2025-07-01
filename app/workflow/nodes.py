import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path)

import uuid
from app.services.azure_openai_service import AzureOpenAIService
from app.services.vector_db_service import VectorDBService
from app.models.schemas import EducationWorkflowState, LearningResponse, FeedbackResponse

key = os.getenv("AZURE_OPENAI_API_KEY")
if not key:
    raise RuntimeError("환경변수 AZURE_OPENAI_API_KEY가 설정되어 있지 않습니다.")
azure_service = AzureOpenAIService(
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    key=key,
    dep_curriculum=os.getenv("AZURE_OPENAI_DEPLOY_CURRICULUM"),
    dep_embed=os.getenv("AZURE_OPENAI_DEPLOY_EMBED"),
)
vector_service = VectorDBService(persist_directory=os.getenv("CHROMA_DB_PATH", "./chroma_db"))

def init_profile_node(state: EducationWorkflowState) -> EducationWorkflowState:
    """아동 프로필 기반 초기 커리큘럼 생성"""
    if state.child_profile:
        curriculum_text = azure_service.get_initial_curriculum(state.child_profile)
        state.curriculum = curriculum_text
    return state

def fetch_course_node(state: EducationWorkflowState) -> EducationWorkflowState:
    """커리큘럼 임베딩 및 유사 자료 조회"""
    if state.curriculum:
        embedding = azure_service.get_embedding(state.curriculum)
        docs = vector_service.query_similar(embedding)
        state.embedding = embedding
        state.related_docs = docs
    return state

def generate_materials_node(state: EducationWorkflowState) -> EducationWorkflowState:
    """맞춤 교재 및 평가 문제 생성"""
    if state.curriculum and state.related_docs and state.child_profile:
        lesson, materials = azure_service.generate_materials(state.curriculum, state.related_docs)
        lesson_id = azure_service.save_lesson(state.child_profile.child_id, lesson, state.related_docs)
        
        state.lesson = lesson
        state.materials = materials
        state.lesson_id = lesson_id
        
        # 문제 텍스트로 합치기
        materials_text = "\n".join(materials)
        state.learning_response = LearningResponse(
            lesson=lesson,
            materials_text=materials_text,
            lesson_id=lesson_id
        )
    return state

def submit_assessment_node(state: EducationWorkflowState) -> EducationWorkflowState:
    """평가 응답 저장"""
    if state.assessment_input:
        vector_service.add_assessment(
            student_id=state.assessment_input.child_id,
            lesson_id=state.assessment_input.lesson_id,
            responses=[state.assessment_input.responses_text],
            materials_text=state.assessment_input.materials_text,
            azure_service=azure_service
        )
        state.responses = state.assessment_input.responses_text
    return state

def create_feedback_node(state: EducationWorkflowState) -> EducationWorkflowState:
    """피드백 및 다음 교재 생성"""
    if state.responses and state.assessment_input:
        feedback = azure_service.create_feedback(
            state.assessment_input.materials_text,
            state.responses
        )
        state.feedback = feedback
        state.feedback_response = FeedbackResponse(
            feedback=feedback
        )
    return state
