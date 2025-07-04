from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

class ChildProfileInput(BaseModel):
    child_id: str = Field(..., description="아동 식별자")
    name: str     = Field(..., description="아동 이름")
    age: int      = Field(..., description="아동 나이")
    interests: List[str] = Field(..., description="관심사 리스트")

class LearningResponse(BaseModel):
    lesson: str             = Field(..., description="생성된 교재 내용")
    materials_text: str     = Field(..., description="문제 전체 텍스트(줄바꿈 포함)")
    lesson_id: str          = Field(..., description="교재 세션 식별자")

class AssessmentInput(BaseModel):
    child_id: str   = Field(..., description="아동 식별자")
    lesson_id: str  = Field(..., description="교재 세션 식별자")
    responses_text: str = Field(..., description="아동의 평가 응답 전체 텍스트")
    materials_text: str = Field(..., description="문제 전체 텍스트")

class FeedbackResponse(BaseModel):
    feedback: str           = Field(..., description="이해도 평가 기반 피드백")
    next_lesson: Optional[str] = Field(None, description="다음 교재 내용(옵션)")

class OverallFeedbackResponse(BaseModel):
    feedback: str = Field(..., description="학습 이력 기반 종합 피드백")

class FeedbackHistoryItem(BaseModel):
    interests: str
    topic: str
    feedback: str

class OverallFeedbackRequest(BaseModel):
    name: str
    age: int
    history: List[FeedbackHistoryItem]

# LangGraph 워크플로우용 통합 상태
@dataclass
class EducationWorkflowState:
    # 입력 데이터
    child_profile: Optional[ChildProfileInput] = None
    assessment_input: Optional[AssessmentInput] = None
    
    # 워크플로우 상태
    curriculum: Optional[str] = None
    embedding: Optional[List[float]] = None
    related_docs: Optional[List[Any]] = None
    lesson: Optional[str] = None
    materials: Optional[List[str]] = None
    lesson_id: Optional[str] = None
    responses: Optional[List[str]] = None
    feedback: Optional[str] = None
    next_lesson: Optional[str] = None
    
    # 결과
    learning_response: Optional[LearningResponse] = None
    feedback_response: Optional[FeedbackResponse] = None
    overall_feedback_response: Optional[OverallFeedbackResponse] = None
    history: Optional[List[Dict[str, str]]] = None
