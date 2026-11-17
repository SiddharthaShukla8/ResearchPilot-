"""Unit tests for ResearchPilot health and capabilities endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient
from researchpilot.main import app


@pytest.mark.asyncio
async def test_health_live():
    """Verify live probe returns ok status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "researchpilot-api"


@pytest.mark.asyncio
async def test_health_ready():
    """Verify ready probe returns ready status and storage status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "storage" in data


@pytest.mark.asyncio
async def test_system_capabilities():
    """Verify system capabilities are reported safely without leaking secrets."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/system/capabilities")
        assert response.status_code == 200
        data = response.json()
        assert "ai_configured" in data
        assert "chat_model" in data
        assert "embedding_model" in data
        assert "max_upload_mb" in data
        assert "OPENAI_API_KEY" not in str(data)
