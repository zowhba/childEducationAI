import uuid
import os
from app.services.azure_openai_service import AzureOpenAIService
from app.services.vector_db_service import VectorDBService

token azure_service = AzureOpenAIService(
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    key=os.getenv("AZURE_OPENAI_KEY"),
    dep_curriculum=os.getenv("AZURE_OPENAI_DEPLOY_CURRICULUM"),
    dep_embed=os.getenv("AZURE_OPENAI_DEPLOY_EMBED"),
)
vector_service = VectorDBService(persist_directory=os.getenv("CHROMA_DB_PATH", "./chroma_db"))

def profile_node(state):
    # 아동 프로필 기반 초기 커리큘럼 생성
    curriculum = azure_service.get_initial_curriculum(state)
    return {**state, "curriculum": curriculum}

def fetch_course_node(state):
    # 커리큘럼 임베딩 및 유사 자료 조회
    embedding = azure_service.get_embedding(state["curriculum"])
    docs = vector_service.query_similar(embedding)
    return {**state, "related_docs": docs}

def generate_node(state):
    # 맞춤 교재 및 평가 문제 생성
    lesson, materials = azure_service.generate_materials(state["curriculum"], state["related_docs"])
    lesson_id = str(uuid.uuid4())
    return {**state, "lesson": lesson, "materials": materials, "lesson_id": lesson_id}

def assess_node(state):
    # 이해도 평가 결과 저장
    vector_service.add_assessment(
        student_id=state.child_id,
        lesson_id=state["lesson_id"],
        responses=state.get("responses", [])
    )
    return state

def feedback_node(state):
    # 피드백 및 다음 교재 생성
    feedback = azure_service.create_feedback(state["responses"])
    next_lesson = azure_service.generate_next_material(state["child_id"], state["lesson_id"])
    return {**state, "feedback": feedback, "next_lesson": next_lesson}
