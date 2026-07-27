import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class BranchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    description: Optional[str] = None


class TargetRoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: Optional[str] = None


class StudentProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    full_name: str
    email: EmailStr
    roll_number: str
    phone_number: Optional[str] = None
    branch_id: str
    target_role_id: str
    branch: Optional[BranchRead] = None
    target_role: Optional[TargetRoleRead] = None
    current_year: int
    semester: int
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    leetcode_url: Optional[str] = None
    hackerrank_url: Optional[str] = None
    profile_photo: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class StudentProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    branch_id: Optional[str] = None
    target_role_id: Optional[str] = None
    current_year: Optional[int] = Field(None, description="Year of study: 1, 2, 3, or 4")
    semester: Optional[int] = Field(None, description="Semester: 1 to 8")

    @field_validator("current_year")
    @classmethod
    def validate_current_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in [1, 2, 3, 4]:
            raise ValueError("Current year must be 1, 2, 3, or 4")
        return v

    @field_validator("semester")
    @classmethod
    def validate_semester(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 8):
            raise ValueError("Semester must be an integer between 1 and 8")
        return v


class StudentSocialLinksUpdate(BaseModel):
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    leetcode_url: Optional[str] = None
    hackerrank_url: Optional[str] = None

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
