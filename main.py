from fastapi import FastAPI
from app.models.schemas import ChildProfileInput, LearningResponse, AssessmentInput, FeedbackResponse
from app.services.azure_openai_service import AzureOpenAIService
from app.services.vector_db_service import VectorDBService
from dotenv import load_dotenv
import os

# 환경변수 로드
load_dotenv()

app = FastAPI(title="어린이 맞춤형 교재 생성기 API")

# Azure OpenAI 및 ChromaDB 서비스 초기화
azure_service = AzureOpenAIService(
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    key=os.getenv("AZURE_OPENAI_KEY"),
    dep_curriculum=os.getenv("AZURE_OPENAI_DEPLOY_CURRICULUM"),
    dep_embed=os.getenv("AZURE_OPENAI_DEPLOY_EMBED"),
)
vector_service = VectorDBService(
    persist_directory=os.getenv("CHROMA_DB_PATH", "./chroma_db")
)

@app.post("/init_profile", response_model=LearningResponse)
async def init_profile(profile: ChildProfileInput):
    """
    1) 아동 프로필 입력 받음
    2) 초기 학습 커리큘럼 생성
    3) 교재 및 문제 생성 후 반환
    """
    # 1) 초기 커리큘럼 프롬프트 생성
    curriculum_text = azure_service.get_initial_curriculum(profile)
    # 2) 커리큘럼 텍스트 임베딩
    embedding = azure_service.get_embedding(curriculum_text)
    # 3) 임베딩 기반 유사 자료 검색
    docs = vector_service.query_similar(embedding)
    # 4) 교재와 평가 문제 생성
    lesson, materials = azure_service.generate_materials(curriculum_text, docs)
    # 5) 학습 세션 저장 및 ID 생성
    lesson_id = azure_service.save_lesson(profile.child_id, lesson, docs)
    return LearningResponse(
        lesson=lesson,
        materials=materials,
        lesson_id=lesson_id
    )

@app.post("/submit_assessment", response_model=FeedbackResponse)
async def submit_assessment(assessment: AssessmentInput):
    """
    1) 평가 응답 저장
    2) 피드백 생성
    3) 다음 교재 생성
    """
    # 1) 평가 응답 ChromaDB에 저장
    vector_service.add_assessment(
        student_id=assessment.child_id,
        lesson_id=assessment.lesson_id,
        responses=assessment.responses,
        azure_service=azure_service
    )
    # 2) 피드백 생성
    feedback = azure_service.create_feedback(assessment.responses)
    # 3) 다음 교재 생성
    next_lesson = azure_service.generate_next_material(assessment.child_id, assessment.lesson_id)
    print("피드백:", feedback)
    print("다음 교재:", next_lesson)
    return FeedbackResponse(
        feedback=feedback,
        next_lesson=next_lesson
    )
