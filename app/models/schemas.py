from pydantic import BaseModel, Field
from typing import List, Optional

class ChildProfileInput(BaseModel):
    child_id: str = Field(..., description="아동 식별자")
    name: str     = Field(..., description="아동 이름")
    age: int      = Field(..., description="아동 나이")
    interests: List[str] = Field(..., description="관심사 리스트")

class LearningResponse(BaseModel):
    lesson: str             = Field(..., description="생성된 교재 내용")
    materials: List[str]    = Field(..., description="평가 문제 리스트")
    lesson_id: str          = Field(..., description="교재 세션 식별자")

class AssessmentInput(BaseModel):
    child_id: str   = Field(..., description="아동 식별자")
    lesson_id: str  = Field(..., description="교재 세션 식별자")
    responses: List[str] = Field(..., description="아동의 평가 응답 리스트")

class FeedbackResponse(BaseModel):
    feedback: str           = Field(..., description="이해도 평가 기반 피드백")
    next_lesson: Optional[str] = Field(None, description="다음 교재 내용(옵션)")
