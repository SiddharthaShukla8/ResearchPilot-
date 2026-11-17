"""Strict Pydantic schemas for the Research Agent Planner, Tools, and Synthesis Report."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    """An individual atomic step in the research plan."""
    step_order: int
    step_type: Literal["retrieval", "analysis", "comparison", "synthesis", "verification"]
    title: str
    instructions: str
    target_subquestion_index: int | None = None


class ResearchPlan(BaseModel):
    """Structured, editable research plan produced by the Planner."""
    objective: str = Field(description="Refined research objective aligned with user intent")
    sub_questions: list[str] = Field(description="3-7 focused sub-questions breaking down the problem")
    steps: list[PlanStep] = Field(description="Ordered execution steps")
    comparison_dimensions: list[str] = Field(
        default=["Model/Architecture", "Dataset & Benchmark", "Evaluation Metrics", "Quantitative Findings", "Limitations"]
    )
    expected_sections: list[str] = Field(
        default=["Executive Summary", "Corpus Scope & Methods", "Paper-by-Paper Summaries", "Thematic Synthesis", "Comparison Matrix", "Agreements & Disagreements", "Candidate Research Gaps", "Conclusion & Next Steps", "References"]
    )
    potential_limitations: list[str] = Field(default_factory=list)


class ToolCallRecord(BaseModel):
    """Audit record of a bounded allowlisted tool execution."""
    tool_name: str
    arguments: dict[str, Any]
    output_summary: str
    timestamp: datetime


class PaperStructuredAnalysis(BaseModel):
    """Structured extraction for a single academic paper."""
    document_id: str
    paper_title: str
    authors: list[str] = Field(default_factory=list)
    publication_year: int | None = None
    objective: str
    method_or_model: str
    dataset_or_population: str
    sample_size: str = "Not stated"
    evaluation_metrics: list[str] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    author_limitations: list[str] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)


class MethodComparisonRecord(BaseModel):
    """Comparative row across multiple papers."""
    paper_title: str
    document_id: str
    methodology: str
    dataset: str
    metrics_reported: str
    comparability: Literal["directly_comparable", "partially_comparable", "not_directly_comparable"]
    comparability_reason: str


class EvidenceAgreement(BaseModel):
    """Classified consensus or conflict across papers."""
    topic: str
    classification: Literal["agreement", "disagreement", "contextual_difference", "not_comparable"]
    explanation: str
    cited_keys: list[str] = Field(default_factory=list)


class CandidateResearchGap(BaseModel):
    """Candidate gap observed strictly within the uploaded corpus."""
    title: str
    description: str
    evidence_basis: str
    scope_caveat: str = "Observed within uploaded papers only; not an exhaustive claim of all academic literature."


class SynthesisReport(BaseModel):
    """Complete, transparent academic literature review report."""
    title: str
    research_question: str
    executive_summary: str
    scope_and_methods: str
    paper_summaries: list[PaperStructuredAnalysis]
    thematic_synthesis: list[dict[str, Any]]  # [{"theme": str, "content": str, "citations": list[str]}]
    comparison_matrix: list[MethodComparisonRecord]
    agreements_and_disagreements: list[EvidenceAgreement]
    candidate_research_gaps: list[CandidateResearchGap]
    limitations: list[str]
    conclusion: str
    references: list[dict[str, Any]]  # [{"citation_key": "[1]", "document_id": str, "title": str, "page": int, "excerpt": str}]
    verification_summary: dict[str, Any]  # {"claims_checked": int, "supported": int, "unsupported_removed": int, "status": "verified"}
