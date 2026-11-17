"""Markdown and structured report builder for synthesized literature reviews."""
from researchpilot.agents.schemas import SynthesisReport


def render_report_to_markdown(report: SynthesisReport) -> str:
    """Format structured report object into publication-grade Markdown."""
    md = []

    # Title & Metadata
    md.append(f"# {report.title}\n")
    md.append(f"**Research Question:** *{report.research_question}*\n")
    md.append("---\n")

    # Executive Summary
    md.append("## Executive Summary\n")
    md.append(f"{report.executive_summary}\n")

    # Scope & Methodology
    md.append("## Corpus Scope & Methodology\n")
    md.append(f"{report.scope_and_methods}\n")

    # Thematic Synthesis
    md.append("## Thematic Synthesis\n")
    for theme in report.thematic_synthesis:
        t_name = theme.get("theme", "Key Theme")
        t_content = theme.get("content", "")
        t_cits = " ".join(theme.get("citations", []))
        md.append(f"### {t_name}\n")
        md.append(f"{t_content} {t_cits}\n")

    # Comparative Matrix
    md.append("## Comparative Methodology & Performance Matrix\n")
    md.append("| Paper | Methodology | Dataset / Benchmark | Reported Performance | Comparability |\n")
    md.append("| :--- | :--- | :--- | :--- | :--- |\n")
    for row in report.comparison_matrix:
        md.append(
            f"| **{row.paper_title}** | {row.methodology} | {row.dataset} | {row.metrics_reported} | `{row.comparability}` ({row.comparability_reason}) |\n"
        )
    md.append("\n")

    # Paper-by-Paper Summaries
    md.append("## Paper-by-Paper Analyses\n")
    for paper in report.paper_summaries:
        year_str = f" ({paper.publication_year})" if paper.publication_year else ""
        md.append(f"### {paper.paper_title}{year_str}\n")
        md.append(f"- **Objective:** {paper.objective}\n")
        md.append(f"- **Approach / Model:** {paper.method_or_model}\n")
        md.append(f"- **Dataset & Sample Size:** {paper.dataset_or_population} (N = {paper.sample_size})\n")
        if paper.key_findings:
            md.append("- **Key Findings:**\n")
            for f in paper.key_findings:
                md.append(f"  - {f}\n")
        if paper.author_limitations:
            md.append("- **Author-Acknowledged Limitations:**\n")
            for lim in paper.author_limitations:
                md.append(f"  - {lim}\n")
        md.append("\n")

    # Agreements and Disagreements
    md.append("## Cross-Paper Evidence Relationships\n")
    for rel in report.agreements_and_disagreements:
        cits = " ".join(rel.cited_keys)
        md.append(f"### {rel.topic} — `{rel.classification.upper()}`\n")
        md.append(f"{rel.explanation} {cits}\n")

    # Candidate Research Gaps
    md.append("## Candidate Research Gaps (Observed Corpus)\n")
    for gap in report.candidate_research_gaps:
        md.append(f"### {gap.title}\n")
        md.append(f"{gap.description}\n\n")
        md.append(f"> **Evidence Basis:** {gap.evidence_basis}\n")
        md.append(f"> *Caveat:* {gap.scope_caveat}\n\n")

    # Limitations & Warnings
    if report.limitations:
        md.append("## Review Limitations & Boundaries\n")
        for l in report.limitations:
            md.append(f"- {l}\n")
        md.append("\n")

    # Conclusion
    md.append("## Conclusion & Suggested Next Steps\n")
    md.append(f"{report.conclusion}\n")

    # References
    md.append("## Grounded References\n")
    for ref in report.references:
        key = ref.get("citation_key", "[?]")
        title = ref.get("title", "Document")
        page = ref.get("page", 1)
        excerpt = ref.get("excerpt", "")
        md.append(f"- **{key}** *{title}* (Page {page})\n")
        if excerpt:
            md.append(f'  > "{excerpt}"\n')
    md.append("\n")

    # Verification Summary
    v = report.verification_summary
    md.append("## Verification Provenance Summary\n")
    md.append(
        f"Status: **{v.get('status', 'verified').upper()}** | "
        f"Claims Checked: {v.get('claims_checked', 0)} | "
        f"Citations Verified: {v.get('citations_validated', 0)} | "
        f"Unsupported Claims Removed: {v.get('unsupported_removed', 0)}\n"
    )

    return "\n".join(md)
