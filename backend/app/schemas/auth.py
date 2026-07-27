import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.schemas.student import StudentProfileRead


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    full_name: str = Field(..., min_length=2, max_length=255)
    roll_number: str = Field(..., min_length=3, max_length=100, description="Unique GITAM Roll Number")
    phone_number: Optional[str] = Field(None, max_length=20)
    branch_id: str = Field(..., description="ID of the selected Branch")
    target_role_id: str = Field(..., description="ID of the selected Target Role")
    current_year: int = Field(..., description="Current year of study (1, 2, 3, or 4)")
    semester: int = Field(..., description="Current semester (1-8)")
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    leetcode_url: Optional[str] = None
    hackerrank_url: Optional[str] = None

    @field_validator("current_year")
    @classmethod
    def validate_current_year(cls, v: int) -> int:
        if v not in [1, 2, 3, 4]:
            raise ValueError("Current year must be 1, 2, 3, or 4")
        return v

    @field_validator("semester")
    @classmethod
    def validate_semester(cls, v: int) -> int:
        if v < 1 or v > 8:
            raise ValueError("Semester must be between 1 and 8")
        return v

    @field_validator("github_url")
    @classmethod
    def validate_github_url(cls, v: Optional[str]) -> Optional[str]:
        if v and v.strip():
            url = v.strip()
            github_pattern = r"^https?:\/\/(www\.)?github\.com\/[A-Za-z0-9_.-]+\/?$"
            if not re.match(github_pattern, url, re.IGNORECASE):
                raise ValueError("Invalid GitHub profile URL format (must be https://github.com/username)")
            return url
        return None

    @field_validator("linkedin_url")
    @classmethod
    def validate_linkedin_url(cls, v: Optional[str]) -> Optional[str]:
        if v and v.strip():
            url = v.strip()
            linkedin_pattern = r"^https?:\/\/(www\.)?linkedin\.com\/in\/[A-Za-z0-9_-]+\/?$"
            if not re.match(linkedin_pattern, url, re.IGNORECASE):
                raise ValueError("Invalid LinkedIn profile URL format (must be https://linkedin.com/in/username)")
            return url
        return None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    is_superuser: bool
    student_profile: Optional[StudentProfileRead] = None
    created_at: datetime
    updated_at: datetime
