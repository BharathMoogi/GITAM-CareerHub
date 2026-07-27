try:
    import pytest
except ImportError:
    class MarkFallback:
        def asyncio(self, func):
            return func
    class PytestFallback:
        mark = MarkFallback()
    pytest = PytestFallback()

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.student_service import StudentService


@pytest.mark.asyncio
async def test_full_student_lifecycle(client: AsyncClient, db_session: AsyncSession):
    # 1. Fetch branches and target roles
    res = await client.get("/api/v1/branches")
    assert res.status_code == 200
    branches = res.json()["data"]
    assert len(branches) >= 4
    branch_id = branches[0]["id"]

    res = await client.get("/api/v1/target-roles")
    assert res.status_code == 200
    roles = res.json()["data"]
    assert len(roles) >= 8
    target_role_id = roles[0]["id"]

    # 2. Register Student
    register_payload = {
        "email": "student1@gitam.edu",
        "password": "Password123!",
        "full_name": "Gitam Student",
        "roll_number": "121910301001",
        "phone_number": "9876543210",
        "branch_id": branch_id,
        "target_role_id": target_role_id,
        "current_year": 3,
        "semester": 5,
        "github_url": "https://github.com/gitamstudent",
        "linkedin_url": "https://linkedin.com/in/gitamstudent",
    }
    reg_res = await client.post("/api/v1/auth/register", json=register_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["success"] is True
    assert "timestamp" in reg_data
    assert reg_data["data"]["email"] == "student1@gitam.edu"
    assert reg_data["data"]["student_profile"]["roll_number"] == "121910301001"

    # 3. Duplicate Email Validation
    dup_email_res = await client.post("/api/v1/auth/register", json={
        **register_payload,
        "roll_number": "121910301002",
    })
    assert dup_email_res.status_code == 400
    assert "already exists" in dup_email_res.json()["error"]["message"]

    # 4. Duplicate Roll Number Validation
    dup_roll_res = await client.post("/api/v1/auth/register", json={
        **register_payload,
        "email": "student2@gitam.edu",
    })
    assert dup_roll_res.status_code == 400
    assert "already exists" in dup_roll_res.json()["error"]["message"]

    # 5. Login
    login_res = await client.post("/api/v1/auth/login", json={
        "email": "student1@gitam.edu",
        "password": "Password123!",
    })
    assert login_res.status_code == 200
    token_data = login_res.json()["data"]
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 6. View Profile
    profile_res = await client.get("/api/v1/students/me", headers=headers)
    assert profile_res.status_code == 200
    prof_data = profile_res.json()["data"]
    assert prof_data["roll_number"] == "121910301001"
    assert prof_data["current_year"] == 3
    assert prof_data["semester"] == 5

    # 7. Update Profile
    update_res = await client.put(
        "/api/v1/students/me",
        headers=headers,
        json={"current_year": 4, "semester": 7, "phone_number": "9999988888"},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()["data"]
    assert updated_data["current_year"] == 4
    assert updated_data["semester"] == 7
    assert updated_data["phone_number"] == "9999988888"

    # 8. Update Social Links (Valid & Invalid)
    invalid_social_res = await client.patch(
        "/api/v1/students/me/social-links",
        headers=headers,
        json={"github_url": "invalid-url-format"},
    )
    assert invalid_social_res.status_code == 422

    valid_social_res = await client.patch(
        "/api/v1/students/me/social-links",
        headers=headers,
        json={
            "github_url": "https://github.com/updatedstudent",
            "linkedin_url": "https://linkedin.com/in/updatedstudent",
            "leetcode_url": "https://leetcode.com/updatedstudent",
        },
    )
    assert valid_social_res.status_code == 200
    social_data = valid_social_res.json()["data"]
    assert social_data["github_url"] == "https://github.com/updatedstudent"

    # 9. Unauthorized Access Verification
    unauth_res = await client.get("/api/v1/students/me")
    assert unauth_res.status_code == 401

    # 10. Logout Endpoint Verification
    logout_res = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    assert logout_res.json()["success"] is True
