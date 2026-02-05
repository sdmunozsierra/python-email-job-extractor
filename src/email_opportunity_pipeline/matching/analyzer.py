"""
Job Analyzer - Extracts and structures job requirements for matching.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


# Schema name for OpenAI API
JOB_ANALYSIS_SCHEMA_NAME = "job_analysis"

# Schema for structured job analysis output
JOB_ANALYSIS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "role_summary": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "title": {"type": ["string", "null"]},
                "level": {"type": ["string", "null"], "description": "entry, mid, senior, staff, principal, lead, manager, director, vp, c-level"},
                "department": {"type": ["string", "null"]},
                "team_size": {"type": ["string", "null"]},
                "reports_to": {"type": ["string", "null"]},
            },
            "required": ["title", "level", "department", "team_size", "reports_to"],
        },
        "requirements": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "years_experience_min": {"type": ["number", "null"]},
                "years_experience_max": {"type": ["number", "null"]},
                "education_required": {"type": ["string", "null"], "description": "minimum education level"},
                "education_preferred": {"type": ["string", "null"]},
                "mandatory_skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Skills explicitly required or must-have",
                },
                "preferred_skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Nice-to-have skills",
                },
                "certifications_required": {"type": "array", "items": {"type": "string"}},
                "certifications_preferred": {"type": "array", "items": {"type": "string"}},
                "security_clearance": {"type": ["string", "null"]},
                "other_requirements": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "years_experience_min", "years_experience_max", "education_required",
                "education_preferred", "mandatory_skills", "preferred_skills",
                "certifications_required", "certifications_preferred",
                "security_clearance", "other_requirements"
            ],
        },
        "responsibilities": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Key job responsibilities",
        },
        "technical_environment": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "languages": {"type": "array", "items": {"type": "string"}},
                "frameworks": {"type": "array", "items": {"type": "string"}},
                "databases": {"type": "array", "items": {"type": "string"}},
                "cloud_platforms": {"type": "array", "items": {"type": "string"}},
                "tools": {"type": "array", "items": {"type": "string"}},
                "methodologies": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["languages", "frameworks", "databases", "cloud_platforms", "tools", "methodologies"],
        },
        "culture_indicators": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "work_style": {"type": ["string", "null"], "description": "collaborative, autonomous, fast-paced, etc."},
                "values_mentioned": {"type": "array", "items": {"type": "string"}},
                "growth_opportunities": {"type": "array", "items": {"type": "string"}},
                "red_flags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["work_style", "values_mentioned", "growth_opportunities", "red_flags"],
        },
        "compensation_analysis": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "salary_competitive": {"type": ["string", "null"], "description": "assessment: below_market, market, above_market, unknown"},
                "benefits_quality": {"type": ["string", "null"], "description": "poor, average, good, excellent, unknown"},
                "equity_offered": {"type": ["boolean", "null"]},
                "notes": {"type": ["string", "null"]},
            },
            "required": ["salary_competitive", "benefits_quality", "equity_offered", "notes"],
        },
        "keywords": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Important keywords for ATS optimization",
        },
        "role_classification": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "primary_domain": {"type": ["string", "null"], "description": "backend, frontend, fullstack, data, devops, ml, mobile, security, etc."},
                "industry": {"type": ["string", "null"]},
                "company_stage": {"type": ["string", "null"], "description": "startup, scaleup, enterprise, agency, consulting"},
            },
            "required": ["primary_domain", "industry", "company_stage"],
        },
    },
    "required": [
        "role_summary", "requirements", "responsibilities",
        "technical_environment", "culture_indicators",
        "compensation_analysis", "keywords", "role_classification"
    ],
}


ANALYZER_SYSTEM_PROMPT = """You are an expert job analyst. Analyze job opportunities and extract structured information.

Your task is to:
1. Identify all explicit and implicit requirements
2. Distinguish between mandatory ("must have") and preferred ("nice to have") skills
3. Extract the technical environment and tools mentioned
4. Identify culture signals and potential red flags
5. Extract important keywords for ATS optimization
6. Classify the role by domain, level, and company type

Be thorough but precise. Only include information that is stated or can be reasonably inferred from the job posting.
For missing information, use null values.

IMPORTANT:
- Mandatory skills are those explicitly stated as required, must-have, or essential
- Preferred skills are nice-to-have, bonus, or preferred qualifications
- Look for experience requirements in years
- Identify education requirements (degree level)
- Note any certifications or clearances required
"""


class JobAnalyzer:
    """
    Analyzes job opportunities using LLM to extract structured requirements.
    """

    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install optional dependency: pip install -e '.[llm]'") from exc

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def analyze(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a job opportunity and extract structured requirements.
        
        Args:
            job: Job opportunity dictionary (from extraction)
            
        Returns:
            Structured job analysis dictionary
        """
        # Build context from job data
        job_context = self._build_job_context(job)
        
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": ANALYZER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this job opportunity:\n\n{job_context}"},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": JOB_ANALYSIS_SCHEMA_NAME,
                    "schema": JOB_ANALYSIS_SCHEMA,
                }
            },
        )
        
        try:
            analysis = json.loads(response.output_text)
        except json.JSONDecodeError:
            analysis = self._create_fallback_analysis(job)
        
        # Merge with original job data
        analysis["source_job"] = {
            "message_id": job.get("source_email", {}).get("message_id"),
            "job_title": job.get("job_title"),
            "company": job.get("company"),
        }
        
        return analysis

    def _build_job_context(self, job: Dict[str, Any]) -> str:
        """Build a text context from job data for analysis."""
        parts = []
        
        if job.get("job_title"):
            parts.append(f"Title: {job['job_title']}")
        if job.get("company"):
            parts.append(f"Company: {job['company']}")
        if job.get("summary"):
            parts.append(f"Summary: {job['summary']}")
        
        if job.get("locations"):
            parts.append(f"Locations: {', '.join(job['locations'])}")
        if job.get("remote") is not None:
            parts.append(f"Remote: {job['remote']}")
        if job.get("hybrid") is not None:
            parts.append(f"Hybrid: {job['hybrid']}")
        
        if job.get("hard_requirements"):
            parts.append(f"Hard Requirements:\n- " + "\n- ".join(job["hard_requirements"]))
        if job.get("mandatory_skills"):
            parts.append(f"Mandatory Skills:\n- " + "\n- ".join(job["mandatory_skills"]))
        if job.get("preferred_skills"):
            parts.append(f"Preferred Skills:\n- " + "\n- ".join(job["preferred_skills"]))
        if job.get("responsibilities"):
            parts.append(f"Responsibilities:\n- " + "\n- ".join(job["responsibilities"]))
        if job.get("qualifications"):
            parts.append(f"Qualifications:\n- " + "\n- ".join(job["qualifications"]))
        
        # Include engagement options for compensation context
        if job.get("engagement_options"):
            for i, opt in enumerate(job["engagement_options"], 1):
                opt_parts = [f"Option {i}: {opt.get('type', 'UNKNOWN')}"]
                if opt.get("duration"):
                    opt_parts.append(f"  Duration: {opt['duration']}")
                if opt.get("pay"):
                    pay = opt["pay"]
                    pay_str = f"  Pay: {pay.get('min', '?')}-{pay.get('max', '?')} {pay.get('currency', '')} {pay.get('unit', '')}"
                    opt_parts.append(pay_str)
                if opt.get("benefits_notes"):
                    opt_parts.append(f"  Benefits: {opt['benefits_notes']}")
                if opt.get("constraints"):
                    opt_parts.append(f"  Constraints: {', '.join(opt['constraints'])}")
                parts.append("\n".join(opt_parts))
        
        if job.get("evidence"):
            parts.append(f"Additional Context (from email):\n" + "\n".join(job["evidence"][:5]))
        
        return "\n\n".join(parts)

    def _create_fallback_analysis(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Create a basic analysis when LLM fails."""
        return {
            "role_summary": {
                "title": job.get("job_title"),
                "level": None,
                "department": None,
                "team_size": None,
                "reports_to": None,
            },
            "requirements": {
                "years_experience_min": None,
                "years_experience_max": None,
                "education_required": None,
                "education_preferred": None,
                "mandatory_skills": job.get("mandatory_skills", []) or [],
                "preferred_skills": job.get("preferred_skills", []) or [],
                "certifications_required": [],
                "certifications_preferred": [],
                "security_clearance": None,
                "other_requirements": job.get("hard_requirements", []) or [],
            },
            "responsibilities": job.get("responsibilities", []) or [],
            "technical_environment": {
                "languages": [],
                "frameworks": [],
                "databases": [],
                "cloud_platforms": [],
                "tools": [],
                "methodologies": [],
            },
            "culture_indicators": {
                "work_style": None,
                "values_mentioned": [],
                "growth_opportunities": [],
                "red_flags": [],
            },
            "compensation_analysis": {
                "salary_competitive": "unknown",
                "benefits_quality": "unknown",
                "equity_offered": None,
                "notes": None,
            },
            "keywords": job.get("mandatory_skills", [])[:10] or [],
            "role_classification": {
                "primary_domain": None,
                "industry": None,
                "company_stage": None,
            },
        }

    def analyze_batch(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple job opportunities.
        
        Args:
            jobs: List of job opportunity dictionaries
            
        Returns:
            List of job analysis dictionaries
        """
        return [self.analyze(job) for job in jobs]


def analyze_job(job: Dict[str, Any], model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Convenience function to analyze a single job.
    
    Args:
        job: Job opportunity dictionary
        model: LLM model to use
        
    Returns:
        Job analysis dictionary
    """
    analyzer = JobAnalyzer(model=model)
    return analyzer.analyze(job)
