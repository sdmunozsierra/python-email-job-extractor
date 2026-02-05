"""
Resume Matcher - Matches resumes against job opportunities using LLM.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from .models import (
    Resume,
    MatchResult,
    SkillMatch,
    ExperienceMatch,
    CategoryScore,
    MatchInsights,
    ResumeTailoring,
    ApplicationStrategy,
)


# Schema for LLM match analysis output
MATCH_ANALYSIS_SCHEMA = {
    "name": "match_analysis",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "overall_score": {
                "type": "number",
                "description": "Overall match score 0-100",
            },
            "match_grade": {
                "type": "string",
                "enum": ["excellent", "good", "fair", "poor", "unqualified"],
            },
            "recommendation": {
                "type": "string",
                "enum": ["strong_apply", "apply", "consider", "skip", "not_recommended"],
            },
            "skills_analysis": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "score": {"type": "number"},
                    "matched_mandatory": {"type": "array", "items": {"type": "string"}},
                    "missing_mandatory": {"type": "array", "items": {"type": "string"}},
                    "matched_preferred": {"type": "array", "items": {"type": "string"}},
                    "missing_preferred": {"type": "array", "items": {"type": "string"}},
                    "bonus_skills": {"type": "array", "items": {"type": "string"}},
                    "transferable_skills": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "score", "matched_mandatory", "missing_mandatory",
                    "matched_preferred", "missing_preferred",
                    "bonus_skills", "transferable_skills"
                ],
            },
            "experience_analysis": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "score": {"type": "number"},
                    "years_gap": {"type": ["number", "null"]},
                    "role_relevance": {"type": "string", "enum": ["high", "medium", "low", "none"]},
                    "relevant_positions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "title": {"type": "string"},
                                "company": {"type": "string"},
                                "relevance": {"type": "string", "enum": ["high", "medium", "low"]},
                                "key_achievements": {"type": "array", "items": {"type": "string"}},
                            },
                            "required": ["title", "company", "relevance", "key_achievements"],
                        },
                    },
                    "experience_gaps": {"type": "array", "items": {"type": "string"}},
                    "career_progression_notes": {"type": ["string", "null"]},
                },
                "required": [
                    "score", "years_gap", "role_relevance",
                    "relevant_positions", "experience_gaps", "career_progression_notes"
                ],
            },
            "education_analysis": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "score": {"type": "number"},
                    "meets_requirements": {"type": "boolean"},
                    "notes": {"type": ["string", "null"]},
                },
                "required": ["score", "meets_requirements", "notes"],
            },
            "location_analysis": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "score": {"type": "number"},
                    "compatible": {"type": "boolean"},
                    "notes": {"type": ["string", "null"]},
                },
                "required": ["score", "compatible", "notes"],
            },
            "culture_fit": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "score": {"type": "number"},
                    "notes": {"type": ["string", "null"]},
                },
                "required": ["score", "notes"],
            },
            "insights": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "strengths": {"type": "array", "items": {"type": "string"}},
                    "concerns": {"type": "array", "items": {"type": "string"}},
                    "opportunities": {"type": "array", "items": {"type": "string"}},
                    "talking_points": {"type": "array", "items": {"type": "string"}},
                    "questions_to_ask": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["strengths", "concerns", "opportunities", "talking_points", "questions_to_ask"],
            },
            "resume_tailoring": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "keywords_to_add": {"type": "array", "items": {"type": "string"}},
                    "skills_to_highlight": {"type": "array", "items": {"type": "string"}},
                    "experience_to_emphasize": {"type": "array", "items": {"type": "string"}},
                    "achievements_to_feature": {"type": "array", "items": {"type": "string"}},
                    "summary_suggestions": {"type": ["string", "null"]},
                },
                "required": [
                    "keywords_to_add", "skills_to_highlight",
                    "experience_to_emphasize", "achievements_to_feature",
                    "summary_suggestions"
                ],
            },
            "application_strategy": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "approach": {
                        "type": "string",
                        "enum": ["direct_apply", "referral_preferred", "recruiter_contact", "networking_first"],
                    },
                    "urgency": {
                        "type": "string",
                        "enum": ["immediate", "soon", "when_ready", "low_priority"],
                    },
                    "cover_letter_focus": {"type": "array", "items": {"type": "string"}},
                    "potential_objections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "objection": {"type": "string"},
                                "counter": {"type": "string"},
                            },
                            "required": ["objection", "counter"],
                        },
                    },
                },
                "required": ["approach", "urgency", "cover_letter_focus", "potential_objections"],
            },
        },
        "required": [
            "overall_score", "match_grade", "recommendation",
            "skills_analysis", "experience_analysis", "education_analysis",
            "location_analysis", "culture_fit", "insights",
            "resume_tailoring", "application_strategy"
        ],
    },
}


MATCHER_SYSTEM_PROMPT = """You are an expert career advisor and resume analyst. Your task is to analyze how well a candidate's resume matches a job opportunity.

Provide a thorough, honest assessment considering:

1. **Skills Match (35% weight)**
   - How many mandatory skills does the candidate have?
   - How many preferred/nice-to-have skills?
   - Are there transferable skills that could compensate for gaps?
   - Does the candidate have bonus skills beyond requirements?

2. **Experience Match (30% weight)**
   - Does the candidate meet experience year requirements?
   - How relevant is their past work to this role?
   - What positions in their history are most relevant?
   - Are there experience gaps for key responsibilities?

3. **Education Match (15% weight)**
   - Does education meet requirements?
   - Is the field of study relevant?

4. **Location Match (10% weight)**
   - Is location compatible (considering remote options)?
   - Would relocation be needed?

5. **Culture Fit (10% weight)**
   - Based on resume presentation and experience types

**Scoring Guidelines:**
- 85-100: Excellent match - Strong candidate, meets most requirements
- 70-84: Good match - Solid candidate, some gaps but competitive
- 50-69: Fair match - Worth considering but notable gaps exist
- 30-49: Poor match - Significant gaps, unlikely to advance
- 0-29: Unqualified - Does not meet basic requirements

**Recommendation Guidelines:**
- strong_apply: Excellent fit, high confidence
- apply: Good fit, worth pursuing
- consider: Mixed signals, proceed with caution
- skip: Poor fit, better opportunities exist
- not_recommended: Unqualified or major red flags

Be constructive and specific in your feedback. Provide actionable insights for resume tailoring and interview preparation.
"""


class ResumeMatcher:
    """
    Matches resumes against job opportunities using LLM analysis.
    """

    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install optional dependency: pip install -e '.[llm]'") from exc

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def match(
        self,
        resume: Resume,
        job: Dict[str, Any],
        job_analysis: Optional[Dict[str, Any]] = None,
    ) -> MatchResult:
        """
        Match a resume against a job opportunity.
        
        Args:
            resume: Resume object
            job: Job opportunity dictionary
            job_analysis: Optional pre-computed job analysis
            
        Returns:
            MatchResult with scores and insights
        """
        start_time = time.time()
        
        # Build context for the LLM
        context = self._build_match_context(resume, job, job_analysis)
        
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": MATCHER_SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ],
            text={"format": {"type": "json_schema", "json_schema": MATCH_ANALYSIS_SCHEMA}},
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        try:
            analysis = json.loads(response.output_text)
        except json.JSONDecodeError:
            analysis = self._create_fallback_analysis()
        
        return self._build_match_result(
            analysis=analysis,
            job=job,
            resume=resume,
            processing_time=processing_time,
        )

    def _build_match_context(
        self,
        resume: Resume,
        job: Dict[str, Any],
        job_analysis: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build context string for LLM matching."""
        parts = []
        
        # Job information
        parts.append("=== JOB OPPORTUNITY ===")
        parts.append(f"Title: {job.get('job_title', 'Unknown')}")
        parts.append(f"Company: {job.get('company', 'Unknown')}")
        
        if job.get("summary"):
            parts.append(f"Summary: {job['summary']}")
        
        if job.get("locations"):
            parts.append(f"Locations: {', '.join(job['locations'])}")
        parts.append(f"Remote: {job.get('remote', 'Unknown')}")
        parts.append(f"Hybrid: {job.get('hybrid', 'Unknown')}")
        
        if job.get("mandatory_skills"):
            parts.append(f"Mandatory Skills: {', '.join(job['mandatory_skills'])}")
        if job.get("preferred_skills"):
            parts.append(f"Preferred Skills: {', '.join(job['preferred_skills'])}")
        if job.get("hard_requirements"):
            parts.append(f"Hard Requirements:\n- " + "\n- ".join(job['hard_requirements']))
        if job.get("responsibilities"):
            parts.append(f"Responsibilities:\n- " + "\n- ".join(job['responsibilities']))
        if job.get("qualifications"):
            parts.append(f"Qualifications:\n- " + "\n- ".join(job['qualifications']))
        
        # Include job analysis if available
        if job_analysis:
            req = job_analysis.get("requirements", {})
            if req.get("years_experience_min") is not None:
                parts.append(f"Required Experience: {req['years_experience_min']}-{req.get('years_experience_max', '+')} years")
            if req.get("education_required"):
                parts.append(f"Required Education: {req['education_required']}")
            
            tech = job_analysis.get("technical_environment", {})
            if tech.get("languages"):
                parts.append(f"Tech Stack - Languages: {', '.join(tech['languages'])}")
            if tech.get("frameworks"):
                parts.append(f"Tech Stack - Frameworks: {', '.join(tech['frameworks'])}")
        
        # Compensation info
        if job.get("engagement_options"):
            for opt in job["engagement_options"]:
                if opt.get("pay"):
                    pay = opt["pay"]
                    if pay.get("min") or pay.get("max"):
                        parts.append(f"Pay ({opt.get('type', 'Unknown')}): {pay.get('min', '?')}-{pay.get('max', '?')} {pay.get('currency', '')} {pay.get('unit', '')}")
        
        parts.append("")
        
        # Resume information
        parts.append("=== CANDIDATE RESUME ===")
        parts.append(f"Name: {resume.personal.name}")
        if resume.personal.location:
            parts.append(f"Location: {resume.personal.location}")
        if resume.personal.summary:
            parts.append(f"Summary: {resume.personal.summary}")
        
        # Skills
        if resume.skills.technical:
            tech_skills = []
            for s in resume.skills.technical:
                skill_str = s.name
                if s.level:
                    skill_str += f" ({s.level})"
                if s.years:
                    skill_str += f" [{s.years}y]"
                tech_skills.append(skill_str)
            parts.append(f"Technical Skills: {', '.join(tech_skills)}")
        
        if resume.skills.soft:
            parts.append(f"Soft Skills: {', '.join(resume.skills.soft)}")
        
        if resume.skills.certifications:
            certs = [c.name for c in resume.skills.certifications]
            parts.append(f"Certifications: {', '.join(certs)}")
        
        # Experience
        if resume.experience:
            parts.append("\nWork Experience:")
            for exp in resume.experience:
                exp_line = f"- {exp.title} at {exp.company}"
                if exp.start_date:
                    end = exp.end_date or "Present"
                    exp_line += f" ({exp.start_date} - {end})"
                parts.append(exp_line)
                if exp.description:
                    parts.append(f"  {exp.description[:200]}")
                if exp.achievements:
                    for ach in exp.achievements[:3]:
                        parts.append(f"  * {ach}")
                if exp.technologies:
                    parts.append(f"  Technologies: {', '.join(exp.technologies)}")
        
        # Education
        if resume.education:
            parts.append("\nEducation:")
            for edu in resume.education:
                edu_line = f"- {edu.degree}"
                if edu.field:
                    edu_line += f" in {edu.field}"
                edu_line += f" from {edu.institution}"
                if edu.end_date:
                    edu_line += f" ({edu.end_date})"
                parts.append(edu_line)
        
        # Projects
        if resume.projects:
            parts.append("\nProjects:")
            for proj in resume.projects[:3]:
                parts.append(f"- {proj.name}")
                if proj.description:
                    parts.append(f"  {proj.description[:150]}")
                if proj.technologies:
                    parts.append(f"  Tech: {', '.join(proj.technologies)}")
        
        # Preferences
        if resume.preferences:
            parts.append("\nCandidate Preferences:")
            if resume.preferences.remote_preference:
                parts.append(f"  Remote: {resume.preferences.remote_preference}")
            if resume.preferences.desired_roles:
                parts.append(f"  Desired Roles: {', '.join(resume.preferences.desired_roles)}")
            if resume.preferences.salary_min:
                parts.append(f"  Salary Min: {resume.preferences.salary_min} {resume.preferences.salary_currency or ''}")
        
        return "\n".join(parts)

    def _create_fallback_analysis(self) -> Dict[str, Any]:
        """Create a basic analysis when LLM fails."""
        return {
            "overall_score": 0,
            "match_grade": "poor",
            "recommendation": "skip",
            "skills_analysis": {
                "score": 0,
                "matched_mandatory": [],
                "missing_mandatory": [],
                "matched_preferred": [],
                "missing_preferred": [],
                "bonus_skills": [],
                "transferable_skills": [],
            },
            "experience_analysis": {
                "score": 0,
                "years_gap": None,
                "role_relevance": "none",
                "relevant_positions": [],
                "experience_gaps": ["Unable to analyze"],
                "career_progression_notes": None,
            },
            "education_analysis": {
                "score": 0,
                "meets_requirements": False,
                "notes": "Unable to analyze",
            },
            "location_analysis": {
                "score": 0,
                "compatible": False,
                "notes": "Unable to analyze",
            },
            "culture_fit": {
                "score": 0,
                "notes": "Unable to analyze",
            },
            "insights": {
                "strengths": [],
                "concerns": ["Analysis failed - manual review required"],
                "opportunities": [],
                "talking_points": [],
                "questions_to_ask": [],
            },
            "resume_tailoring": {
                "keywords_to_add": [],
                "skills_to_highlight": [],
                "experience_to_emphasize": [],
                "achievements_to_feature": [],
                "summary_suggestions": None,
            },
            "application_strategy": {
                "approach": "direct_apply",
                "urgency": "when_ready",
                "cover_letter_focus": [],
                "potential_objections": [],
            },
        }

    def _build_match_result(
        self,
        analysis: Dict[str, Any],
        job: Dict[str, Any],
        resume: Resume,
        processing_time: float,
    ) -> MatchResult:
        """Build MatchResult from LLM analysis."""
        skills = analysis.get("skills_analysis", {})
        exp = analysis.get("experience_analysis", {})
        edu = analysis.get("education_analysis", {})
        loc = analysis.get("location_analysis", {})
        culture = analysis.get("culture_fit", {})
        insights_data = analysis.get("insights", {})
        tailoring = analysis.get("resume_tailoring", {})
        strategy = analysis.get("application_strategy", {})
        
        job_id = job.get("source_email", {}).get("message_id", "unknown")
        resume_id = resume.source_file or resume.personal.name
        
        return MatchResult(
            job_id=job_id,
            resume_id=resume_id,
            overall_score=analysis.get("overall_score", 0),
            match_grade=analysis.get("match_grade", "poor"),
            recommendation=analysis.get("recommendation", "skip"),
            skills_match=SkillMatch(
                score=skills.get("score", 0),
                matched_mandatory=skills.get("matched_mandatory", []),
                missing_mandatory=skills.get("missing_mandatory", []),
                matched_preferred=skills.get("matched_preferred", []),
                missing_preferred=skills.get("missing_preferred", []),
                bonus_skills=skills.get("bonus_skills", []),
                transferable_skills=skills.get("transferable_skills", []),
                mandatory_met=len(skills.get("matched_mandatory", [])),
                mandatory_total=len(skills.get("matched_mandatory", [])) + len(skills.get("missing_mandatory", [])),
                preferred_met=len(skills.get("matched_preferred", [])),
                preferred_total=len(skills.get("matched_preferred", [])) + len(skills.get("missing_preferred", [])),
            ),
            experience_match=ExperienceMatch(
                score=exp.get("score", 0),
                years_required=None,  # Could be extracted from job analysis
                years_candidate=resume.get_total_experience_years(),
                role_relevance=exp.get("role_relevance"),
                relevant_positions=exp.get("relevant_positions", []),
                experience_gaps=exp.get("experience_gaps", []),
                career_progression_notes=exp.get("career_progression_notes"),
            ),
            education_score=CategoryScore(
                score=edu.get("score", 0),
                weight=0.15,
                notes=edu.get("notes"),
            ),
            location_score=CategoryScore(
                score=loc.get("score", 0),
                weight=0.10,
                notes=loc.get("notes"),
            ),
            culture_fit_score=CategoryScore(
                score=culture.get("score", 0),
                weight=0.10,
                notes=culture.get("notes"),
            ),
            insights=MatchInsights(
                strengths=insights_data.get("strengths", []),
                concerns=insights_data.get("concerns", []),
                opportunities=insights_data.get("opportunities", []),
                talking_points=insights_data.get("talking_points", []),
                questions_to_ask=insights_data.get("questions_to_ask", []),
            ),
            resume_tailoring=ResumeTailoring(
                keywords_to_add=tailoring.get("keywords_to_add", []),
                skills_to_highlight=tailoring.get("skills_to_highlight", []),
                experience_to_emphasize=tailoring.get("experience_to_emphasize", []),
                achievements_to_feature=tailoring.get("achievements_to_feature", []),
                summary_suggestions=tailoring.get("summary_suggestions"),
            ),
            application_strategy=ApplicationStrategy(
                approach=strategy.get("approach", "direct_apply"),
                urgency=strategy.get("urgency", "when_ready"),
                cover_letter_focus=strategy.get("cover_letter_focus", []),
                potential_objections=strategy.get("potential_objections", []),
            ),
            model_used=self.model,
            processing_time_ms=processing_time,
        )

    def match_batch(
        self,
        resume: Resume,
        jobs: List[Dict[str, Any]],
        job_analyses: Optional[List[Dict[str, Any]]] = None,
    ) -> List[MatchResult]:
        """
        Match a resume against multiple job opportunities.
        
        Args:
            resume: Resume object
            jobs: List of job opportunity dictionaries
            job_analyses: Optional pre-computed job analyses
            
        Returns:
            List of MatchResults sorted by overall_score descending
        """
        results = []
        analyses = job_analyses or [None] * len(jobs)
        
        for job, analysis in zip(jobs, analyses):
            result = self.match(resume, job, analysis)
            results.append(result)
        
        # Sort by score descending
        results.sort(key=lambda r: r.overall_score, reverse=True)
        return results


def match_resume_to_job(
    resume: Resume,
    job: Dict[str, Any],
    model: str = "gpt-4o-mini",
) -> MatchResult:
    """
    Convenience function to match a resume to a job.
    
    Args:
        resume: Resume object
        job: Job opportunity dictionary
        model: LLM model to use
        
    Returns:
        MatchResult
    """
    matcher = ResumeMatcher(model=model)
    return matcher.match(resume, job)
