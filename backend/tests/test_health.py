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


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "GITAM CareerHub API"
    assert data["status"] == "online"


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] in ["healthy", "degraded"]
    assert "database" in payload["data"]


@pytest.mark.asyncio
async def test_api_v1_health_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] in ["healthy", "degraded"]
