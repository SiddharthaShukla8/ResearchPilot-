"""Integration tests for Research Run lifecycle, Agent Planner, and Orchestration."""
import fitz
import pytest
from httpx import ASGITransport, AsyncClient
from researchpilot.agents.orchestrator import ResearchOrchestrator
from researchpilot.db.models import Document, DocumentChunk, Project, ResearchRun, User
from researchpilot.main import app
from researchpilot.services.ai_provider import MockAIProvider


def make_pdf(text: str) -> bytes:
    doc = fitz.open()
    p = doc.new_page()
    p.insert_text((50, 50), text)
    b = doc.write()
    doc.close()
    return b


@pytest.mark.asyncio
async def test_research_run_creation_and_plan_review(db_session):
    """Verify research question submission, plan generation, and review/edit endpoints."""
    # 1. Setup user, project, and indexed document
    user = User(name="Researcher Maya", email="maya@lab.org", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    proj = Project(owner_id=user.id, title="Brain Tumor DL Review")
    db_session.add(proj)
    await db_session.flush()

    doc = Document(
        project_id=proj.id,
        owner_id=user.id,
        original_filename="cnn_mri.pdf",
        private_storage_key="p1.pdf",
        sha256="h1",
        file_size=1200,
        title="Deep CNN for Brain Tumor MRI Segmentation",
        processing_status="ready",
    )
    db_session.add(doc)
    await db_session.flush()

    chunk = DocumentChunk(
        document_id=doc.id,
        owner_id=user.id,
        chunk_index=0,
        page_start=1,
        page_end=1,
        text="The proposed U-Net achieves 93.8% Dice on BraTS 2021 benchmark with 480 training scans.",
        token_count=18,
        content_hash="ch1",
        embedding=[0.05] * 1536,
    )
    db_session.add(chunk)
    await db_session.commit()

    # 2. Test API interaction
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login
        auth_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "maya@lab.org", "password": "dummy"},
        )
        # Manually create access token for direct test speed
        from researchpilot.core.security import create_access_token
        token = create_access_token({"sub": user.id, "email": user.email})
        headers = {"Authorization": f"Bearer {token}"}

        # Create research run
        create_payload = {
            "research_question": "What is the benchmark accuracy of U-Net in Brain Tumor MRI segmentation?",
            "selected_document_ids": [doc.id],
            "citation_style": "numbered",
            "quick_run": False,
        }
        res = await client.post(
            f"/api/v1/projects/{proj.id}/research-runs",
            headers=headers,
            json=create_payload,
        )
        assert res.status_code == 201
        run_data = res.json()
        assert run_data["status"] == "awaiting_approval"
        assert run_data["plan_json"] is not None
        run_id = run_data["id"]

        # Edit the plan
        patch_payload = {
            "objective": "Refined Objective: U-Net performance on BraTS",
            "sub_questions": ["What is the reported Dice score?"],
            "steps": [{"step_order": 1, "step_type": "retrieval", "title": "Retrieve Dice score passages"}],
        }
        patch_res = await client.patch(
            f"/api/v1/research-runs/{run_id}/plan",
            headers=headers,
            json=patch_payload,
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["plan_json"]["objective"] == "Refined Objective: U-Net performance on BraTS"

        # Approve the plan
        app_res = await client.post(
            f"/api/v1/research-runs/{run_id}/approve",
            headers=headers,
        )
        assert app_res.status_code == 200
        assert app_res.json()["status"] == "queued"

        # Check events
        ev_res = await client.get(f"/api/v1/research-runs/{run_id}/events", headers=headers)
        assert ev_res.status_code == 200
        events = ev_res.json()
        assert len(events) >= 2

        # Cancel the run
        cancel_res = await client.post(
            f"/api/v1/research-runs/{run_id}/cancel",
            headers=headers,
        )
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "cancelled"

        # Retry the cancelled/failed run
        retry_res = await client.post(
            f"/api/v1/research-runs/{run_id}/retry",
            headers=headers,
        )
        assert retry_res.status_code == 200
        assert retry_res.json()["status"] == "queued"


@pytest.mark.asyncio
async def test_full_orchestrator_pipeline_and_citation_verification(db_session):
    """Verify that Orchestrator runs end-to-end, synthesizes report, and verifies citations."""
    user = User(name="Researcher Maya", email="maya2@lab.org", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    proj = Project(owner_id=user.id, title="Deep Learning Review")
    db_session.add(proj)
    await db_session.flush()

    doc = Document(
        project_id=proj.id,
        owner_id=user.id,
        original_filename="transformer_brain.pdf",
        private_storage_key="p2.pdf",
        sha256="h2",
        file_size=1500,
        title="Vision Transformers for Glioblastoma",
        processing_status="ready",
    )
    db_session.add(doc)
    await db_session.flush()

    chunk = DocumentChunk(
        document_id=doc.id,
        owner_id=user.id,
        chunk_index=0,
        page_start=2,
        page_end=2,
        text="The vision transformer architecture achieves 92.4% mean intersection over union.",
        token_count=14,
        content_hash="ch2",
        embedding=[0.01] * 1536,
    )
    db_session.add(chunk)
    await db_session.flush()

    run = ResearchRun(
        project_id=proj.id,
        owner_id=user.id,
        research_question="How effective are transformers for brain tumor segmentation?",
        selected_document_ids=[doc.id],
        citation_style="numbered",
        status="queued",
    )
    db_session.add(run)
    await db_session.commit()

    # Execute orchestrator pipeline
    ai = MockAIProvider()
    orchestrator = ResearchOrchestrator(db_session, ai)
    await orchestrator.run_pipeline(run.id)

    # Refresh run from db
    await db_session.refresh(run)
    assert run.status == "completed"
    assert run.report_json is not None
    assert run.report_markdown is not None
    assert "Literature Review:" in run.report_markdown
    assert "Verification Provenance Summary" in run.report_markdown

    # Assert verification summary
    verif = run.report_json.get("verification_summary", {})
    assert verif.get("status") in ["verified", "verified_with_caveats"]
    assert verif.get("citations_validated", 0) > 0
