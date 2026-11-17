"""Research Run execution and report API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from researchpilot.agents.planner import ResearchPlanner
from researchpilot.api.deps import get_current_user
from researchpilot.api.schemas.run_schemas import (
    AgentEventResponse,
    ResearchPlanUpdateRequest,
    ResearchRunCreateRequest,
    ResearchRunResponse,
)
from researchpilot.db.models import AgentEvent, Document, ResearchRun, User
from researchpilot.db.session import get_db_session
from researchpilot.repositories.job_repo import JobRepository
from researchpilot.repositories.project_repo import ProjectRepository
from researchpilot.services.ai_provider import get_ai_provider

router = APIRouter(tags=["Research Runs"])


@router.post("/projects/{project_id}/research-runs", response_model=ResearchRunResponse, status_code=status.HTTP_201_CREATED)
async def create_research_run(
    project_id: str,
    payload: ResearchRunCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a research run, validate documents, generate initial plan, and optionally auto-approve."""
    proj_repo = ProjectRepository(session)
    project = await proj_repo.get_by_id_and_owner(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")

    # Validate selected documents belong to user and are ready
    doc_stmt = select(Document).where(
        Document.id.in_(payload.selected_document_ids),
        Document.project_id == project_id,
        Document.owner_id == current_user.id,
    )
    doc_res = await session.execute(doc_stmt)
    docs = list(doc_res.scalars().all())

    if len(docs) != len(payload.selected_document_ids):
        raise HTTPException(status_code=400, detail="One or more selected documents are invalid or unauthorized")

    for d in docs:
        if d.processing_status != "ready":
            raise HTTPException(
                status_code=400,
                detail=f"Document '{d.original_filename}' is still {d.processing_status}. Please wait until indexing finishes.",
            )

    # Generate initial research plan
    ai_provider = get_ai_provider()
    planner = ResearchPlanner(ai_provider)
    papers_context = [{"title": d.title or d.original_filename, "year": str(d.publication_year or "Unknown")} for d in docs]

    plan = await planner.generate_plan(
        question=payload.research_question,
        papers_context=papers_context,
        user_instructions=payload.user_instructions,
    )

    initial_status = "queued" if payload.quick_run else "awaiting_approval"

    run = ResearchRun(
        project_id=project_id,
        owner_id=current_user.id,
        research_question=payload.research_question,
        selected_document_ids=payload.selected_document_ids,
        citation_style=payload.citation_style,
        status=initial_status,
        plan_json=plan.model_dump(),
    )
    session.add(run)
    await session.flush()

    # Emit initial planning event
    event = AgentEvent(
        run_id=run.id,
        sequence=1,
        event_type="plan_created",
        safe_summary=f"Generated plan for research question: '{payload.research_question[:60]}...'",
        metadata_json={"quick_run": payload.quick_run},
    )
    session.add(event)

    # If quick_run, immediately enqueue execution job
    if payload.quick_run:
        job_repo = JobRepository(session)
        await job_repo.enqueue(
            owner_id=current_user.id,
            project_id=project_id,
            target_id=run.id,
            job_type="execute_research",
        )

    await session.commit()
    return run


@router.get("/research-runs/{run_id}", response_model=ResearchRunResponse)
async def get_research_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get research run details and current status."""
    run = await session.get(ResearchRun, run_id)
    if not run or run.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Research run not found or unauthorized")
    return run


@router.patch("/research-runs/{run_id}/plan", response_model=ResearchRunResponse)
async def update_research_plan(
    run_id: str,
    payload: ResearchPlanUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Edit research plan before approval."""
    run = await session.get(ResearchRun, run_id)
    if not run or run.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Research run not found or unauthorized")

    if run.status != "awaiting_approval":
        raise HTTPException(status_code=409, detail=f"Cannot edit plan in status '{run.status}'")

    updated_plan = run.plan_json or {}
    updated_plan["objective"] = payload.objective
    updated_plan["sub_questions"] = payload.sub_questions
    updated_plan["steps"] = payload.steps

    run.plan_json = updated_plan
    await session.commit()
    return run


@router.post("/research-runs/{run_id}/approve", response_model=ResearchRunResponse)
async def approve_research_plan(
    run_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Approve research plan and trigger background agent execution."""
    run = await session.get(ResearchRun, run_id)
    if not run or run.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Research run not found or unauthorized")

    if run.status != "awaiting_approval":
        raise HTTPException(status_code=409, detail=f"Run is in state '{run.status}', not awaiting approval")

    run.status = "queued"

    job_repo = JobRepository(session)
    await job_repo.enqueue(
        owner_id=current_user.id,
        project_id=run.project_id,
        target_id=run.id,
        job_type="execute_research",
    )

    event = AgentEvent(
        run_id=run.id,
        sequence=2,
        event_type="plan_approved",
        safe_summary="User reviewed and approved research plan. Execution enqueued.",
    )
    session.add(event)
    await session.commit()
    return run


@router.post("/research-runs/{run_id}/cancel", response_model=ResearchRunResponse)
async def cancel_research_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Cancel a queued or running research execution."""
    run = await session.get(ResearchRun, run_id)
    if not run or run.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Research run not found or unauthorized")

    if run.status in ["completed", "failed", "cancelled"]:
        raise HTTPException(status_code=409, detail=f"Cannot cancel run in terminal state '{run.status}'")

    run.status = "cancelled"
    event = AgentEvent(
        run_id=run.id,
        sequence=999,
        event_type="run_cancelled",
        safe_summary="Research run cancelled by user.",
    )
    session.add(event)
    await session.commit()
    return run


@router.get("/research-runs/{run_id}/events", response_model=list[AgentEventResponse])
async def get_run_events(
    run_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieve operational timeline events for a research run."""
    run = await session.get(ResearchRun, run_id)
    if not run or run.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Research run not found or unauthorized")

    stmt = (
        select(AgentEvent)
        .where(AgentEvent.run_id == run_id)
        .order_by(AgentEvent.sequence.asc())
    )
    res = await session.execute(stmt)
    return list(res.scalars().all())


@router.get("/research-runs/{run_id}/report")
async def get_run_report(
    run_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieve synthesized literature review report."""
    run = await session.get(ResearchRun, run_id)
    if not run or run.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Research run not found or unauthorized")

    if run.status != "completed" or not run.report_json:
        raise HTTPException(status_code=409, detail=f"Report not available. Run is in status '{run.status}'")

    return {
        "run_id": run.id,
        "question": run.research_question,
        "report_json": run.report_json,
        "report_markdown": run.report_markdown,
    }


@router.get("/research-runs/{run_id}/export")
async def export_run_report(
    run_id: str,
    format: str = "markdown",
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Export report as Markdown or PDF."""
    run = await session.get(ResearchRun, run_id)
    if not run or run.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Research run not found or unauthorized")

    if run.status != "completed" or not run.report_markdown:
        raise HTTPException(status_code=409, detail="Report not ready for export")

    if format == "pdf":
        # Generate clean printable HTML/PDF structure
        html_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{run.research_question}</title>
<style>
body {{ font-family: -apple-system, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; color: #1e293b; }}
h1, h2, h3 {{ color: #0f172a; }}
pre, code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 4px; }}
table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
th, td {{ border: 1px solid #cbd5e1; padding: 8px 12px; text-align: left; }}
th {{ background: #f8fafc; }}
blockquote {{ border-left: 4px solid #3b82f6; margin: 0; padding-left: 16px; color: #475569; }}
</style>
</head>
<body>
<pre>{run.report_markdown}</pre>
</body>
</html>"""
        return Response(
            content=html_doc,
            media_type="text/html",
            headers={"Content-Disposition": 'inline; filename="research_report.html"'},
        )

    return PlainTextResponse(
        content=run.report_markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": 'attachment; filename="research_report.md"'},
    )
