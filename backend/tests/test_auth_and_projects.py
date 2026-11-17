"""Comprehensive integration tests for User Auth and Project Ownership."""
import pytest
from httpx import ASGITransport, AsyncClient
from researchpilot.main import app


@pytest.mark.asyncio
async def test_auth_registration_and_login():
    """Verify registration, duplicate email rejection, and successful login."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register new user
        reg_payload = {
            "name": "Alice Researcher",
            "email": "alice@university.edu",
            "password": "StrongPassword123!",
        }
        res = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res.status_code == 201
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data

        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # 2. Duplicate registration rejected with 409
        res_dup = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res_dup.status_code == 409

        # 3. Fetch profile with Bearer token
        res_me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert res_me.status_code == 200
        assert res_me.json()["email"] == "alice@university.edu"

        # 4. Token refresh rotation
        res_ref = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert res_ref.status_code == 200
        new_refresh = res_ref.json()["refresh_token"]

        # 5. Old refresh token should now be revoked
        res_old = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert res_old.status_code == 401

        # 6. Logout
        res_out = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": new_refresh},
        )
        assert res_out.status_code == 200


@pytest.mark.asyncio
async def test_project_ownership_isolation():
    """Verify that projects created by User A cannot be accessed or modified by User B."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register User A
        res_a = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "Dr. Alice",
                "email": "alice.owner@test.edu",
                "password": "SuperSecretPass1!",
            },
        )
        token_a = res_a.json()["access_token"]

        # Register User B
        res_b = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "Bob Observer",
                "email": "bob.observer@test.edu",
                "password": "SuperSecretPass2!",
            },
        )
        token_b = res_b.json()["access_token"]

        # User A creates a research project
        create_res = await client.post(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "title": "Quantum Computing Literature Review",
                "description": "Analysis of NISQ error mitigation papers",
            },
        )
        assert create_res.status_code == 201
        project_id = create_res.json()["id"]

        # User A can get the project
        get_a = await client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert get_a.status_code == 200
        assert get_a.json()["title"] == "Quantum Computing Literature Review"

        # User B attempts to access User A's project -> returns 404 (does not leak existence)
        get_b = await client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert get_b.status_code == 404

        # User B attempts to delete User A's project -> returns 404
        del_b = await client.delete(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert del_b.status_code == 404

        # User A updates the project
        patch_a = await client.patch(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"title": "Updated Quantum Review"},
        )
        assert patch_a.status_code == 200
        assert patch_a.json()["title"] == "Updated Quantum Review"

        # Unauthenticated request returns 401
        unauth = await client.get(f"/api/v1/projects/{project_id}")
        assert unauth.status_code == 401
