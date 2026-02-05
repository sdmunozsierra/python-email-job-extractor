"""
Data models for job analysis and resume matching.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Skill:
    """Represents a technical skill with optional proficiency level."""
    name: str
    level: Optional[str] = None  # beginner, intermediate, advanced, expert
    years: Optional[float] = None
    category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "years": self.years,
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        return cls(
            name=data.get("name", ""),
            level=data.get("level"),
            years=data.get("years"),
            category=data.get("category"),
        )


@dataclass
class Language:
    """Represents a spoken/written language."""
    language: str
    proficiency: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"language": self.language, "proficiency": self.proficiency}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Language":
        return cls(
            language=data.get("language", ""),
            proficiency=data.get("proficiency"),
        )


@dataclass
class Certification:
    """Represents a professional certification."""
    name: str
    issuer: Optional[str] = None
    date: Optional[str] = None
    expiry: Optional[str] = None
    credential_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "issuer": self.issuer,
            "date": self.date,
            "expiry": self.expiry,
            "credential_id": self.credential_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Certification":
        return cls(
            name=data.get("name", ""),
            issuer=data.get("issuer"),
            date=data.get("date"),
            expiry=data.get("expiry"),
            credential_id=data.get("credential_id"),
        )


@dataclass
class Experience:
    """Represents a work experience entry."""
    title: str
    company: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    current: bool = False
    description: Optional[str] = None
    achievements: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "current": self.current,
            "description": self.description,
            "achievements": self.achievements,
            "technologies": self.technologies,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Experience":
        return cls(
            title=data.get("title", ""),
            company=data.get("company", ""),
            location=data.get("location"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            current=data.get("current", False),
            description=data.get("description"),
            achievements=data.get("achievements", []) or [],
            technologies=data.get("technologies", []) or [],
        )


@dataclass
class Education:
    """Represents an education entry."""
    degree: str
    institution: str
    field: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None
    honors: Optional[str] = None
    relevant_coursework: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "degree": self.degree,
            "field": self.field,
            "institution": self.institution,
            "location": self.location,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "gpa": self.gpa,
            "honors": self.honors,
            "relevant_coursework": self.relevant_coursework,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Education":
        return cls(
            degree=data.get("degree", ""),
            institution=data.get("institution", ""),
            field=data.get("field"),
            location=data.get("location"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            gpa=data.get("gpa"),
            honors=data.get("honors"),
            relevant_coursework=data.get("relevant_coursework", []) or [],
        )


@dataclass
class Project:
    """Represents a project entry."""
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    technologies: List[str] = field(default_factory=list)
    highlights: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "technologies": self.technologies,
            "highlights": self.highlights,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        return cls(
            name=data.get("name", ""),
            description=data.get("description"),
            url=data.get("url"),
            technologies=data.get("technologies", []) or [],
            highlights=data.get("highlights", []) or [],
        )


@dataclass
class PersonalInfo:
    """Personal information in resume."""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "linkedin": self.linkedin,
            "github": self.github,
            "portfolio": self.portfolio,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersonalInfo":
        return cls(
            name=data.get("name", ""),
            email=data.get("email"),
            phone=data.get("phone"),
            location=data.get("location"),
            linkedin=data.get("linkedin"),
            github=data.get("github"),
            portfolio=data.get("portfolio"),
            summary=data.get("summary"),
        )


@dataclass
class JobPreferences:
    """Job search preferences."""
    desired_roles: List[str] = field(default_factory=list)
    industries: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    remote_preference: Optional[str] = None  # remote_only, hybrid, onsite, flexible
    salary_min: Optional[float] = None
    salary_currency: Optional[str] = None
    engagement_types: List[str] = field(default_factory=list)
    willing_to_relocate: bool = False
    visa_sponsorship_needed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "desired_roles": self.desired_roles,
            "industries": self.industries,
            "locations": self.locations,
            "remote_preference": self.remote_preference,
            "salary_min": self.salary_min,
            "salary_currency": self.salary_currency,
            "engagement_types": self.engagement_types,
            "willing_to_relocate": self.willing_to_relocate,
            "visa_sponsorship_needed": self.visa_sponsorship_needed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobPreferences":
        return cls(
            desired_roles=data.get("desired_roles", []) or [],
            industries=data.get("industries", []) or [],
            locations=data.get("locations", []) or [],
            remote_preference=data.get("remote_preference"),
            salary_min=data.get("salary_min"),
            salary_currency=data.get("salary_currency"),
            engagement_types=data.get("engagement_types", []) or [],
            willing_to_relocate=data.get("willing_to_relocate", False),
            visa_sponsorship_needed=data.get("visa_sponsorship_needed", False),
        )


@dataclass
class Skills:
    """Container for all skill categories."""
    technical: List[Skill] = field(default_factory=list)
    soft: List[str] = field(default_factory=list)
    languages: List[Language] = field(default_factory=list)
    certifications: List[Certification] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "technical": [s.to_dict() for s in self.technical],
            "soft": self.soft,
            "languages": [l.to_dict() for l in self.languages],
            "certifications": [c.to_dict() for c in self.certifications],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skills":
        return cls(
            technical=[Skill.from_dict(s) for s in (data.get("technical", []) or [])],
            soft=data.get("soft", []) or [],
            languages=[Language.from_dict(l) for l in (data.get("languages", []) or [])],
            certifications=[Certification.from_dict(c) for c in (data.get("certifications", []) or [])],
        )

    def get_all_skill_names(self) -> List[str]:
        """Get flat list of all technical skill names."""
        return [s.name for s in self.technical]


@dataclass
class Resume:
    """Complete resume model."""
    personal: PersonalInfo
    skills: Skills = field(default_factory=Skills)
    experience: List[Experience] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    projects: List[Project] = field(default_factory=list)
    preferences: Optional[JobPreferences] = None
    source_file: Optional[str] = None  # Path to original file

    def to_dict(self) -> Dict[str, Any]:
        return {
            "personal": self.personal.to_dict(),
            "skills": self.skills.to_dict(),
            "experience": [e.to_dict() for e in self.experience],
            "education": [e.to_dict() for e in self.education],
            "projects": [p.to_dict() for p in self.projects],
            "preferences": self.preferences.to_dict() if self.preferences else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], source_file: Optional[str] = None) -> "Resume":
        personal_data = data.get("personal", {}) or {}
        skills_data = data.get("skills", {}) or {}
        preferences_data = data.get("preferences")

        return cls(
            personal=PersonalInfo.from_dict(personal_data),
            skills=Skills.from_dict(skills_data),
            experience=[Experience.from_dict(e) for e in (data.get("experience", []) or [])],
            education=[Education.from_dict(e) for e in (data.get("education", []) or [])],
            projects=[Project.from_dict(p) for p in (data.get("projects", []) or [])],
            preferences=JobPreferences.from_dict(preferences_data) if preferences_data else None,
            source_file=source_file,
        )

    def get_total_experience_years(self) -> Optional[float]:
        """Estimate total years of experience."""
        # Simple heuristic based on positions
        if not self.experience:
            return None
        return float(len(self.experience)) * 2  # Rough estimate


# Match Result Models

@dataclass
class CategoryScore:
    """Score for a single matching category."""
    score: float  # 0-100
    weight: float = 0.2
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "weight": self.weight,
            "notes": self.notes,
        }


@dataclass
class SkillMatch:
    """Detailed skill matching analysis."""
    score: float  # 0-100
    weight: float = 0.35
    mandatory_met: int = 0
    mandatory_total: int = 0
    preferred_met: int = 0
    preferred_total: int = 0
    matched_mandatory: List[str] = field(default_factory=list)
    missing_mandatory: List[str] = field(default_factory=list)
    matched_preferred: List[str] = field(default_factory=list)
    missing_preferred: List[str] = field(default_factory=list)
    bonus_skills: List[str] = field(default_factory=list)
    transferable_skills: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "weight": self.weight,
            "mandatory_met": self.mandatory_met,
            "mandatory_total": self.mandatory_total,
            "preferred_met": self.preferred_met,
            "preferred_total": self.preferred_total,
            "matched_mandatory": self.matched_mandatory,
            "missing_mandatory": self.missing_mandatory,
            "matched_preferred": self.matched_preferred,
            "missing_preferred": self.missing_preferred,
            "bonus_skills": self.bonus_skills,
            "transferable_skills": self.transferable_skills,
        }


@dataclass
class ExperienceMatch:
    """Detailed experience matching analysis."""
    score: float  # 0-100
    weight: float = 0.30
    years_required: Optional[float] = None
    years_candidate: Optional[float] = None
    role_relevance: Optional[str] = None
    relevant_positions: List[Dict[str, Any]] = field(default_factory=list)
    experience_gaps: List[str] = field(default_factory=list)
    career_progression_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "weight": self.weight,
            "years_required": self.years_required,
            "years_candidate": self.years_candidate,
            "role_relevance": self.role_relevance,
            "relevant_positions": self.relevant_positions,
            "experience_gaps": self.experience_gaps,
            "career_progression_notes": self.career_progression_notes,
        }


@dataclass
class MatchInsights:
    """Insights and recommendations from match analysis."""
    strengths: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    talking_points: List[str] = field(default_factory=list)
    questions_to_ask: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strengths": self.strengths,
            "concerns": self.concerns,
            "opportunities": self.opportunities,
            "talking_points": self.talking_points,
            "questions_to_ask": self.questions_to_ask,
        }


@dataclass
class ResumeTailoring:
    """Suggestions for tailoring resume to specific job."""
    keywords_to_add: List[str] = field(default_factory=list)
    skills_to_highlight: List[str] = field(default_factory=list)
    experience_to_emphasize: List[str] = field(default_factory=list)
    achievements_to_feature: List[str] = field(default_factory=list)
    summary_suggestions: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "keywords_to_add": self.keywords_to_add,
            "skills_to_highlight": self.skills_to_highlight,
            "experience_to_emphasize": self.experience_to_emphasize,
            "achievements_to_feature": self.achievements_to_feature,
            "summary_suggestions": self.summary_suggestions,
        }


@dataclass
class ApplicationStrategy:
    """Strategy recommendations for applying."""
    approach: str = "direct_apply"  # direct_apply, referral_preferred, recruiter_contact, networking_first
    urgency: str = "when_ready"  # immediate, soon, when_ready, low_priority
    cover_letter_focus: List[str] = field(default_factory=list)
    potential_objections: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approach": self.approach,
            "urgency": self.urgency,
            "cover_letter_focus": self.cover_letter_focus,
            "potential_objections": self.potential_objections,
        }


@dataclass
class MatchResult:
    """Complete job-resume match result."""
    job_id: str
    overall_score: float  # 0-100
    match_grade: str  # excellent, good, fair, poor, unqualified
    recommendation: str  # strong_apply, apply, consider, skip, not_recommended
    
    skills_match: SkillMatch
    experience_match: ExperienceMatch
    education_score: CategoryScore
    location_score: CategoryScore
    culture_fit_score: CategoryScore
    
    insights: MatchInsights
    resume_tailoring: Optional[ResumeTailoring] = None
    application_strategy: Optional[ApplicationStrategy] = None
    
    resume_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    model_used: Optional[str] = None
    processing_time_ms: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "resume_id": self.resume_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "overall_score": self.overall_score,
            "match_grade": self.match_grade,
            "recommendation": self.recommendation,
            "category_scores": {
                "skills_match": self.skills_match.to_dict(),
                "experience_match": self.experience_match.to_dict(),
                "education_match": self.education_score.to_dict(),
                "location_match": self.location_score.to_dict(),
                "culture_fit": self.culture_fit_score.to_dict(),
            },
            "skills_analysis": {
                "matched_mandatory": self.skills_match.matched_mandatory,
                "missing_mandatory": self.skills_match.missing_mandatory,
                "matched_preferred": self.skills_match.matched_preferred,
                "missing_preferred": self.skills_match.missing_preferred,
                "bonus_skills": self.skills_match.bonus_skills,
                "transferable_skills": self.skills_match.transferable_skills,
            },
            "experience_analysis": {
                "relevant_positions": self.experience_match.relevant_positions,
                "experience_gaps": self.experience_match.experience_gaps,
                "career_progression_notes": self.experience_match.career_progression_notes,
            },
            "insights": self.insights.to_dict(),
            "resume_tailoring": self.resume_tailoring.to_dict() if self.resume_tailoring else None,
            "application_strategy": self.application_strategy.to_dict() if self.application_strategy else None,
            "metadata": {
                "model_used": self.model_used,
                "analysis_version": "1.0",
                "processing_time_ms": self.processing_time_ms,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MatchResult":
        """Reconstruct MatchResult from dictionary."""
        cat_scores = data.get("category_scores", {})
        skills_data = cat_scores.get("skills_match", {})
        exp_data = cat_scores.get("experience_match", {})
        skills_analysis = data.get("skills_analysis", {})
        exp_analysis = data.get("experience_analysis", {})
        
        timestamp = None
        if data.get("timestamp"):
            try:
                timestamp = datetime.fromisoformat(data["timestamp"])
            except (ValueError, TypeError):
                pass

        return cls(
            job_id=data.get("job_id", ""),
            resume_id=data.get("resume_id"),
            timestamp=timestamp,
            overall_score=data.get("overall_score", 0),
            match_grade=data.get("match_grade", "poor"),
            recommendation=data.get("recommendation", "skip"),
            skills_match=SkillMatch(
                score=skills_data.get("score", 0),
                weight=skills_data.get("weight", 0.35),
                mandatory_met=skills_data.get("mandatory_met", 0),
                mandatory_total=skills_data.get("mandatory_total", 0),
                preferred_met=skills_data.get("preferred_met", 0),
                preferred_total=skills_data.get("preferred_total", 0),
                matched_mandatory=skills_analysis.get("matched_mandatory", []),
                missing_mandatory=skills_analysis.get("missing_mandatory", []),
                matched_preferred=skills_analysis.get("matched_preferred", []),
                missing_preferred=skills_analysis.get("missing_preferred", []),
                bonus_skills=skills_analysis.get("bonus_skills", []),
                transferable_skills=skills_analysis.get("transferable_skills", []),
            ),
            experience_match=ExperienceMatch(
                score=exp_data.get("score", 0),
                weight=exp_data.get("weight", 0.30),
                years_required=exp_data.get("years_required"),
                years_candidate=exp_data.get("years_candidate"),
                role_relevance=exp_data.get("role_relevance"),
                relevant_positions=exp_analysis.get("relevant_positions", []),
                experience_gaps=exp_analysis.get("experience_gaps", []),
                career_progression_notes=exp_analysis.get("career_progression_notes"),
            ),
            education_score=CategoryScore(
                score=cat_scores.get("education_match", {}).get("score", 0),
                weight=cat_scores.get("education_match", {}).get("weight", 0.15),
                notes=cat_scores.get("education_match", {}).get("notes"),
            ),
            location_score=CategoryScore(
                score=cat_scores.get("location_match", {}).get("score", 0),
                weight=cat_scores.get("location_match", {}).get("weight", 0.10),
                notes=cat_scores.get("location_match", {}).get("notes"),
            ),
            culture_fit_score=CategoryScore(
                score=cat_scores.get("culture_fit", {}).get("score", 0),
                weight=cat_scores.get("culture_fit", {}).get("weight", 0.10),
                notes=cat_scores.get("culture_fit", {}).get("notes"),
            ),
            insights=MatchInsights(
                strengths=data.get("insights", {}).get("strengths", []),
                concerns=data.get("insights", {}).get("concerns", []),
                opportunities=data.get("insights", {}).get("opportunities", []),
                talking_points=data.get("insights", {}).get("talking_points", []),
                questions_to_ask=data.get("insights", {}).get("questions_to_ask", []),
            ),
            resume_tailoring=ResumeTailoring(
                keywords_to_add=data.get("resume_tailoring", {}).get("keywords_to_add", []) if data.get("resume_tailoring") else [],
                skills_to_highlight=data.get("resume_tailoring", {}).get("skills_to_highlight", []) if data.get("resume_tailoring") else [],
                experience_to_emphasize=data.get("resume_tailoring", {}).get("experience_to_emphasize", []) if data.get("resume_tailoring") else [],
                achievements_to_feature=data.get("resume_tailoring", {}).get("achievements_to_feature", []) if data.get("resume_tailoring") else [],
                summary_suggestions=data.get("resume_tailoring", {}).get("summary_suggestions") if data.get("resume_tailoring") else None,
            ) if data.get("resume_tailoring") else None,
            application_strategy=ApplicationStrategy(
                approach=data.get("application_strategy", {}).get("approach", "direct_apply") if data.get("application_strategy") else "direct_apply",
                urgency=data.get("application_strategy", {}).get("urgency", "when_ready") if data.get("application_strategy") else "when_ready",
                cover_letter_focus=data.get("application_strategy", {}).get("cover_letter_focus", []) if data.get("application_strategy") else [],
                potential_objections=data.get("application_strategy", {}).get("potential_objections", []) if data.get("application_strategy") else [],
            ) if data.get("application_strategy") else None,
            model_used=data.get("metadata", {}).get("model_used"),
            processing_time_ms=data.get("metadata", {}).get("processing_time_ms"),
        )
