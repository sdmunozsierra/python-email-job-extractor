"""
Match result report generation in Markdown format.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from .models import MatchResult


def _grade_emoji(grade: str) -> str:
    """Get emoji for match grade."""
    mapping = {
        "excellent": "🟢",
        "good": "🟡",
        "fair": "🟠",
        "poor": "🔴",
        "unqualified": "⛔",
    }
    return mapping.get(grade, "❓")


def _recommendation_emoji(rec: str) -> str:
    """Get emoji for recommendation."""
    mapping = {
        "strong_apply": "✅",
        "apply": "👍",
        "consider": "🤔",
        "skip": "👎",
        "not_recommended": "❌",
    }
    return mapping.get(rec, "❓")


def _score_bar(score: float, width: int = 20) -> str:
    """Generate a visual score bar."""
    filled = int(score / 100 * width)
    empty = width - filled
    return "█" * filled + "░" * empty


def _bullets(items: List[str], empty_msg: str = "(none)") -> str:
    """Format a list as bullet points."""
    if not items:
        return f"- {empty_msg}"
    return "\n".join(f"- {item}" for item in items)


def render_match_markdown(result: MatchResult, job: Optional[Dict] = None) -> str:
    """
    Render a match result as a Markdown report.
    
    Args:
        result: MatchResult object
        job: Optional job opportunity dict for additional context
        
    Returns:
        Formatted markdown string
    """
    lines: List[str] = []
    
    # Frontmatter
    lines.append("---")
    lines.append(f'job_id: "{result.job_id}"')
    lines.append(f'resume_id: "{result.resume_id or "unknown"}"')
    lines.append(f'overall_score: {result.overall_score}')
    lines.append(f'match_grade: "{result.match_grade}"')
    lines.append(f'recommendation: "{result.recommendation}"')
    lines.append(f'timestamp: "{result.timestamp.isoformat() if result.timestamp else datetime.now(timezone.utc).isoformat()}"')
    lines.append("---")
    lines.append("")
    
    # Title
    job_title = job.get("job_title", "Job") if job else "Job"
    company = job.get("company", "Unknown Company") if job else "Unknown Company"
    lines.append(f"# Match Report: {job_title} at {company}")
    lines.append("")
    
    # Overall Assessment
    lines.append("## Overall Assessment")
    lines.append("")
    lines.append(f"**Score:** {result.overall_score:.0f}/100 {_score_bar(result.overall_score)}")
    lines.append(f"**Grade:** {_grade_emoji(result.match_grade)} {result.match_grade.title()}")
    lines.append(f"**Recommendation:** {_recommendation_emoji(result.recommendation)} {result.recommendation.replace('_', ' ').title()}")
    lines.append("")
    
    # Category Scores
    lines.append("## Category Breakdown")
    lines.append("")
    lines.append("| Category | Score | Weight | Weighted |")
    lines.append("|----------|-------|--------|----------|")
    
    categories = [
        ("Skills", result.skills_match.score, result.skills_match.weight),
        ("Experience", result.experience_match.score, result.experience_match.weight),
        ("Education", result.education_score.score, result.education_score.weight),
        ("Location", result.location_score.score, result.location_score.weight),
        ("Culture Fit", result.culture_fit_score.score, result.culture_fit_score.weight),
    ]
    
    for name, score, weight in categories:
        weighted = score * weight
        lines.append(f"| {name} | {score:.0f} | {weight*100:.0f}% | {weighted:.1f} |")
    lines.append("")
    
    # Skills Analysis
    lines.append("## Skills Analysis")
    lines.append("")
    
    sm = result.skills_match
    if sm.mandatory_total > 0:
        lines.append(f"**Mandatory Skills:** {sm.mandatory_met}/{sm.mandatory_total} ({sm.mandatory_met/sm.mandatory_total*100:.0f}%)")
    if sm.preferred_total > 0:
        lines.append(f"**Preferred Skills:** {sm.preferred_met}/{sm.preferred_total} ({sm.preferred_met/sm.preferred_total*100:.0f}%)")
    lines.append("")
    
    if sm.matched_mandatory:
        lines.append("### ✅ Matched Mandatory Skills")
        lines.append(_bullets(sm.matched_mandatory))
        lines.append("")
    
    if sm.missing_mandatory:
        lines.append("### ❌ Missing Mandatory Skills")
        lines.append(_bullets(sm.missing_mandatory))
        lines.append("")
    
    if sm.matched_preferred:
        lines.append("### ✅ Matched Preferred Skills")
        lines.append(_bullets(sm.matched_preferred))
        lines.append("")
    
    if sm.missing_preferred:
        lines.append("### ⚠️ Missing Preferred Skills")
        lines.append(_bullets(sm.missing_preferred))
        lines.append("")
    
    if sm.bonus_skills:
        lines.append("### 🌟 Bonus Skills (Exceeding Requirements)")
        lines.append(_bullets(sm.bonus_skills))
        lines.append("")
    
    if sm.transferable_skills:
        lines.append("### 🔄 Transferable Skills")
        lines.append(_bullets(sm.transferable_skills))
        lines.append("")
    
    # Experience Analysis
    lines.append("## Experience Analysis")
    lines.append("")
    
    em = result.experience_match
    if em.years_required is not None or em.years_candidate is not None:
        lines.append(f"**Required:** {em.years_required or '?'} years | **Candidate:** {em.years_candidate or '?'} years")
    if em.role_relevance:
        lines.append(f"**Role Relevance:** {em.role_relevance.title()}")
    lines.append("")
    
    if em.relevant_positions:
        lines.append("### Relevant Positions")
        for pos in em.relevant_positions:
            lines.append(f"**{pos.get('title', 'Unknown')}** at {pos.get('company', 'Unknown')} ({pos.get('relevance', 'unknown')} relevance)")
            if pos.get("key_achievements"):
                for ach in pos["key_achievements"]:
                    lines.append(f"  - {ach}")
        lines.append("")
    
    if em.experience_gaps:
        lines.append("### Experience Gaps")
        lines.append(_bullets(em.experience_gaps))
        lines.append("")
    
    if em.career_progression_notes:
        lines.append(f"**Career Notes:** {em.career_progression_notes}")
        lines.append("")
    
    # Insights
    lines.append("## Insights")
    lines.append("")
    
    ins = result.insights
    if ins.strengths:
        lines.append("### 💪 Strengths")
        lines.append(_bullets(ins.strengths))
        lines.append("")
    
    if ins.concerns:
        lines.append("### ⚠️ Concerns")
        lines.append(_bullets(ins.concerns))
        lines.append("")
    
    if ins.opportunities:
        lines.append("### 🚀 Opportunities")
        lines.append(_bullets(ins.opportunities))
        lines.append("")
    
    if ins.talking_points:
        lines.append("### 💬 Talking Points for Interview")
        lines.append(_bullets(ins.talking_points))
        lines.append("")
    
    if ins.questions_to_ask:
        lines.append("### ❓ Questions to Ask")
        lines.append(_bullets(ins.questions_to_ask))
        lines.append("")
    
    # Resume Tailoring
    if result.resume_tailoring:
        lines.append("## Resume Tailoring Suggestions")
        lines.append("")
        
        rt = result.resume_tailoring
        if rt.keywords_to_add:
            lines.append("### Keywords to Add")
            lines.append(", ".join(f"`{kw}`" for kw in rt.keywords_to_add))
            lines.append("")
        
        if rt.skills_to_highlight:
            lines.append("### Skills to Highlight")
            lines.append(_bullets(rt.skills_to_highlight))
            lines.append("")
        
        if rt.experience_to_emphasize:
            lines.append("### Experience to Emphasize")
            lines.append(_bullets(rt.experience_to_emphasize))
            lines.append("")
        
        if rt.achievements_to_feature:
            lines.append("### Achievements to Feature")
            lines.append(_bullets(rt.achievements_to_feature))
            lines.append("")
        
        if rt.summary_suggestions:
            lines.append("### Summary Suggestions")
            lines.append(f"> {rt.summary_suggestions}")
            lines.append("")
    
    # Application Strategy
    if result.application_strategy:
        lines.append("## Application Strategy")
        lines.append("")
        
        strat = result.application_strategy
        lines.append(f"**Approach:** {strat.approach.replace('_', ' ').title()}")
        lines.append(f"**Urgency:** {strat.urgency.replace('_', ' ').title()}")
        lines.append("")
        
        if strat.cover_letter_focus:
            lines.append("### Cover Letter Focus Points")
            lines.append(_bullets(strat.cover_letter_focus))
            lines.append("")
        
        if strat.potential_objections:
            lines.append("### Addressing Potential Objections")
            for obj in strat.potential_objections:
                lines.append(f"**Objection:** {obj.get('objection', '')}")
                lines.append(f"**Counter:** {obj.get('counter', '')}")
                lines.append("")
    
    # Metadata
    lines.append("---")
    lines.append("")
    lines.append(f"*Generated at: {result.timestamp.isoformat() if result.timestamp else 'Unknown'}*")
    if result.model_used:
        lines.append(f"*Model: {result.model_used}*")
    if result.processing_time_ms:
        lines.append(f"*Processing time: {result.processing_time_ms:.0f}ms*")
    
    return "\n".join(lines)


def render_match_summary(results: List[MatchResult], jobs: Optional[List[Dict]] = None) -> str:
    """
    Render a summary report for multiple match results.
    
    Args:
        results: List of MatchResult objects (should be sorted by score)
        jobs: Optional list of job opportunity dicts
        
    Returns:
        Formatted markdown string
    """
    jobs_map = {}
    if jobs:
        for job in jobs:
            job_id = job.get("source_email", {}).get("message_id")
            if job_id:
                jobs_map[job_id] = job
    
    lines: List[str] = []
    
    lines.append("# Job Match Summary Report")
    lines.append("")
    lines.append(f"**Total Jobs Analyzed:** {len(results)}")
    lines.append(f"**Report Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")
    
    # Stats
    excellent = sum(1 for r in results if r.match_grade == "excellent")
    good = sum(1 for r in results if r.match_grade == "good")
    fair = sum(1 for r in results if r.match_grade == "fair")
    poor = sum(1 for r in results if r.match_grade == "poor")
    unqualified = sum(1 for r in results if r.match_grade == "unqualified")
    
    lines.append("## Match Distribution")
    lines.append("")
    lines.append(f"- 🟢 Excellent: {excellent}")
    lines.append(f"- 🟡 Good: {good}")
    lines.append(f"- 🟠 Fair: {fair}")
    lines.append(f"- 🔴 Poor: {poor}")
    lines.append(f"- ⛔ Unqualified: {unqualified}")
    lines.append("")
    
    # Recommendations
    strong_apply = [r for r in results if r.recommendation == "strong_apply"]
    apply = [r for r in results if r.recommendation == "apply"]
    consider = [r for r in results if r.recommendation == "consider"]
    
    lines.append("## Recommended Actions")
    lines.append("")
    lines.append(f"- ✅ Strong Apply: {len(strong_apply)}")
    lines.append(f"- 👍 Apply: {len(apply)}")
    lines.append(f"- 🤔 Consider: {len(consider)}")
    lines.append("")
    
    # Ranked list
    lines.append("## Ranked Opportunities")
    lines.append("")
    lines.append("| Rank | Score | Grade | Job Title | Company | Recommendation |")
    lines.append("|------|-------|-------|-----------|---------|----------------|")
    
    for i, result in enumerate(results, 1):
        job = jobs_map.get(result.job_id, {})
        title = job.get("job_title", "Unknown")[:30]
        company = job.get("company", "Unknown")[:20]
        grade_em = _grade_emoji(result.match_grade)
        rec_em = _recommendation_emoji(result.recommendation)
        
        lines.append(
            f"| {i} | {result.overall_score:.0f} | {grade_em} {result.match_grade} | {title} | {company} | {rec_em} {result.recommendation.replace('_', ' ')} |"
        )
    
    lines.append("")
    
    # Top picks detail
    if strong_apply or apply:
        lines.append("## Top Picks - Details")
        lines.append("")
        
        top_picks = (strong_apply + apply)[:5]  # Top 5
        for result in top_picks:
            job = jobs_map.get(result.job_id, {})
            title = job.get("job_title", "Unknown")
            company = job.get("company", "Unknown")
            
            lines.append(f"### {title} at {company}")
            lines.append(f"**Score:** {result.overall_score:.0f} | **Grade:** {result.match_grade}")
            lines.append("")
            
            if result.insights.strengths:
                lines.append("**Key Strengths:**")
                for s in result.insights.strengths[:3]:
                    lines.append(f"- {s}")
                lines.append("")
            
            if result.skills_match.missing_mandatory:
                lines.append("**Gaps to Address:**")
                for m in result.skills_match.missing_mandatory[:3]:
                    lines.append(f"- {m}")
                lines.append("")
    
    return "\n".join(lines)
