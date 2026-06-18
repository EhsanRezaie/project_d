from typing import Optional
from pydantic import BaseModel
from uuid import UUID


class PromptResponse(BaseModel):
    id: UUID
    question: str
    category: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class PromptCreateRequest(BaseModel):
    question: str
    category: Optional[str] = None


class UserPromptResponse(BaseModel):
    id: UUID
    prompt_id: UUID
    question: str
    answer: str

    class Config:
        from_attributes = True


class UserPromptCreateRequest(BaseModel):
    prompt_id: UUID
    answer: str