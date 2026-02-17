from pydantic import BaseModel, Field
from typing import Optional

class AnswerRequest(BaseModel):
    text_answer: str = Field(..., min_length=350, max_length=5000)
    answer_type: str = Field(default="text")

class UserProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    age: Optional[int] = Field(None, ge=1, le=120)
    gender: Optional[str] = Field(None, max_length=20)

class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=100)
    name: Optional[str] = Field(None, max_length=100)

class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1)

class QuestionResponse(BaseModel):
    id: int
    text: str
    order_number: int
    type: str
    allow_voice: bool
    max_length: int

class ProgressResponse(BaseModel):
    current: int
    total: int
    answered: int

class UserStatusResponse(BaseModel):
    is_paid: bool
    test_completed: bool

class CurrentQuestionResponse(BaseModel):
    question: QuestionResponse
    progress: ProgressResponse
    user: UserStatusResponse

class NextQuestionResponse(BaseModel):
    status: str
    next_question: Optional[QuestionResponse] = None
    progress: Optional[ProgressResponse] = None
    message: Optional[str] = None
    is_paid: Optional[bool] = None  # для status=test_completed — куда редиректить

class UserProgressResponse(BaseModel):
    user: dict
    progress: dict
    answers: list

class UserProfileResponse(BaseModel):
    status: str
    user: dict
    payment_status: Optional[str] = None
