"""CLI entry point for resume-builder.

Usage (via uv)::

    uv run resume-builder --json resume.json --output my_resume.docx
    uv run resume-builder                        # legacy Python data

Usage (direct)::

    python -m resume_builder --json resume.json
"""

import argparse
from collections import OrderedDict

from resume_builder.person_builder import PersonBuilder
from resume_builder.education_builder import EducationFactory
from resume_builder.cert_builder import CertFactory
from resume_builder.format_experience import format_experience, format_experience_skills
from resume_builder.schema_adapter import ResumeSchemaAdapter
from resume_builder.document_styles import (
    create_styled_document,
    add_name_heading,
    add_job_title,
    add_contact_line,
    add_summary,
    add_section_heading,
    add_subsection_heading,
    add_experience_header,
    add_bullet_point,
    add_tech_tags,
    add_education_entry,
    add_project_entry,
    add_certifications_table,
    add_activity_bullets,
    add_inline_list,
    add_preferences_section,
    add_spacer,
    create_skills_table,
    Colors,
    Fonts,
)
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH


# ---------------------------------------------------------------------------
# Skill categorization helpers
# ---------------------------------------------------------------------------

# Friendly display names for skill categories
_CATEGORY_LABELS = OrderedDict([
    ("languages", "Programming Languages"),
    ("frameworks", "Frameworks & Libraries"),
    ("cloud", "Cloud Platforms"),
    ("devops", "DevOps & Infrastructure"),
    ("databases", "Databases"),
    ("observability", "Observability & Monitoring"),
    ("data", "Data Engineering"),
    ("genai", "Generative AI"),
    ("ml", "Machine Learning"),
    ("api", "API & Integration"),
    ("security", "Security"),
    ("tools", "Tools & Platforms"),
])


def _group_skills_by_category(skills):
    """Group Skill objects by their category, returning an OrderedDict of label → [name, ...]."""
    from collections import defaultdict
    grouped = defaultdict(list)
    uncategorized = []

    for skill in skills:
        cat = getattr(skill, "category", None)
        name = getattr(skill, "name", str(skill))
        if cat and cat in _CATEGORY_LABELS:
            grouped[cat].append(name)
        elif cat:
            grouped[cat].append(name)
        else:
            uncategorized.append(name)

    result = OrderedDict()
    for key, label in _CATEGORY_LABELS.items():
        if key in grouped:
            result[label] = grouped[key]

    # Any categories not in our predefined list
    for key in sorted(grouped.keys()):
        if key not in _CATEGORY_LABELS:
            result[key.replace("_", " ").title()] = grouped[key]

    if uncategorized:
        result["Other"] = uncategorized

    return result


# ---------------------------------------------------------------------------
# Resume builder (works with both legacy and JSON-schema Person objects)
# ---------------------------------------------------------------------------

def build_resume(person):
    """Build a polished Word document from a Person object."""
    doc = create_styled_document()

    # === HEADER ============================================================
    add_name_heading(doc, person.name or "Resume")

    if person.job_title:
        add_job_title(doc, person.job_title)

    # Contact info line
    contact_parts = []
    if person.email:
        contact_parts.append(person.email)
    if person.phone:
        contact_parts.append(person.phone)
    if person.location:
        contact_parts.append(person.location)
    if person.linkedin:
        contact_parts.append(person.linkedin)
    if person.github:
        contact_parts.append(person.github)
    if person.portfolio:
        contact_parts.append(person.portfolio)
    if contact_parts:
        add_contact_line(doc, contact_parts)

    # Professional summary
    if person.summary:
        add_summary(doc, person.summary)

    # === EXPERIENCE ========================================================
    add_section_heading(doc, "Experience")
    format_experience(doc, person.experience)

    # === EDUCATION =========================================================
    if person.education:
        add_section_heading(doc, "Education")
        for edu in person.education:
            title = getattr(edu, "display_title", None)
            if not title:
                title = f"{edu.major}" if edu.major else ""

            institution = edu.school_name or ""
            location = edu.location or ""
            date_range = getattr(edu, "date_range", None) or getattr(edu, "dates", None) or ""

            add_education_entry(
                doc,
                title=title,
                institution=institution,
                location=location,
                date_range=date_range,
                gpa=edu.gpa,
                honors=getattr(edu, "honors", None),
                coursework=edu.coursework,
            )

    # === SKILLS ============================================================
    add_section_heading(doc, "Skills")

    # Experience-derived skills (legacy)
    has_project_skills = any(
        getattr(exp, "projects", None) for exp in person.experience
    )
    if has_project_skills:
        add_subsection_heading(doc, "Experience Skills")
        format_experience_skills(doc, person.experience)

    # Technical skills grouped by category
    if person.skills:
        # Check if skills are Skill objects with categories
        has_categories = any(
            getattr(s, "category", None) for s in person.skills
        )
        if has_categories:
            add_subsection_heading(doc, "Technical Skills")
            grouped = _group_skills_by_category(person.skills)
            create_skills_table(doc, grouped)
        else:
            # Plain list (legacy) — sort alphabetically
            add_subsection_heading(doc, "Technical Skills (A-Z)")
            arr = sorted(person.skills)
            add_inline_list(doc, arr)

    # Soft skills
    if person.soft_skills:
        add_spacer(doc, pts=2)
        add_subsection_heading(doc, "Soft Skills")
        # Display as bullet points for better readability
        for skill in person.soft_skills:
            add_bullet_point(doc, skill)

    # Spoken languages
    if person.languages:
        add_spacer(doc, pts=2)
        add_subsection_heading(doc, "Languages")
        lang_strs = []
        for lang in person.languages:
            if isinstance(lang, dict):
                lang_strs.append(
                    f"{lang.get('language', '?')} ({lang.get('proficiency', '?')})"
                )
            else:
                lang_strs.append(str(lang))
        add_inline_list(doc, lang_strs)

    # === PROJECTS (top-level) ==============================================
    if person.projects:
        add_section_heading(doc, "Projects")
        for proj in person.projects:
            bullets = getattr(proj, "all_bullets", proj.highlights or proj.actions)
            tech = getattr(proj, "all_tech", proj.technologies or proj.skills)
            add_project_entry(
                doc,
                name=proj.name,
                description=proj.description,
                url=proj.url,
                bullets=bullets,
                technologies=tech,
            )

    # === ACTIVITIES ========================================================
    if person.activities:
        add_section_heading(doc, "Activities & Awards")
        add_activity_bullets(doc, person.activities)

    # === CERTIFICATIONS ====================================================
    if person.certifications:
        add_section_heading(doc, "Certifications")
        add_certifications_table(doc, person.certifications)

    # === PREFERENCES =======================================================
    if person.preferences:
        add_section_heading(doc, "Preferences")
        add_preferences_section(doc, person.preferences)

    return doc


# ---------------------------------------------------------------------------
# Legacy data loader
# ---------------------------------------------------------------------------

def build_legacy_person():
    """Build a Person using the legacy Python-coded personal info."""
    from resume_builder.personal_info import sergio_david_munoz_sierra as sdms

    utep_education = EducationFactory.create_education(
        "Computer Science",
        "Math",
        "The University of Texas at El Paso",
        "Dic 2018",
        "El Paso, TX",
        2.4,
        [
            "Artificial Intelligence",
            "Numerical Analysis",
            "Computer Networks",
            "Software Construction",
            "Secure Web Systems",
        ],
        ["Google Ignite CS Program", "Miner's Cyber Security Club (MSSC)"],
        [
            "Dr. Omar Baddredin - Crowd-sourcing Road Topology and Driving "
            "Patterns using Smartphone's Sensors"
        ],
        ["Research with Dr. Omar Baddredin - UTD - 4th Place "],
    )

    certs = CertFactory.from_file("certs.txt")

    sergio_builder = (
        PersonBuilder()
        .add_experience(sdms.job0)
        .add_experience(sdms.job1)
        .add_experience(sdms.job2)
        .add_experience(sdms.job3)
        .add_experience(sdms.job4)
        .add_experience(sdms.job5)
        .add_experience(sdms.job6)
        .add_experience(sdms.job7)
        .set_skills(
            [
                "postman", "REST", "sonarqube", "swagger-api",
                "aws-aurora", "mongo-db", "graphql", "redis", "sql",
                "java-8+", "java-android", "mvn",
                "js-node", "js-vue", "js-nuxt", "js-express",
                "python2", "python3", "python-scrapy", "python-flask", "python-pandas",
                "spring-boot", "spring-security", "spring-profiles", "spring-data",
                "bash", "kafka", "vim", "yarn", "solidity",
                "html", "css", "php", "jinja",
                "git", "github-actions", "gitlab-cicd",
                "aws-amplify", "aws-iam", "aws-serverless", "aws-vpc",
                "aws-codepipeline", "aws-cloudformation",
                "ansible", "consul", "kubernetes-training",
                "docker", "docker-compose", "docker-swarm", "docker-images",
                "elastic-stack", "elastic-search", "log-stash", "kibana",
                "arch-linux", "centos", "debian", "mint", "ubuntu-flavors", "proxmox",
                "english-fluent", "spanish-fluent", "french-wp",
            ]
        )
        .add_activity("1st Place - 2019 RESET Hackathon (Blockchain)")
        .add_activity("2nd Place - 2021 Verac Hackathon (Android)")
        .add_activity("3rd Place - 2018 UTD Research Symposium (Android)")
        .add_activity("4th Place - 2020 SANS Institute CTF (Pen Testing)")
        .set_certs(certs)
    )

    sergio = sergio_builder.build()
    sergio.name = "Sergio David Munoz Sierra"
    sergio.job_title = "Future Master of Science in Analytics"
    return sergio


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point for the ``resume-builder`` console script."""
    parser = argparse.ArgumentParser(
        prog="resume-builder",
        description="Build a .docx resume from JSON or legacy Python data.",
    )
    parser.add_argument(
        "--json",
        type=str,
        default=None,
        help="Path to a resume JSON file (new schema). If omitted, uses legacy data.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="resume.docx",
        help="Output .docx file name (default: resume.docx)",
    )
    args = parser.parse_args()

    if args.json:
        person = ResumeSchemaAdapter.from_json_file(args.json)
    else:
        person = build_legacy_person()

    resume = build_resume(person)
    resume.save(args.output)
    print(f"Resume saved to {args.output}")


if __name__ == "__main__":
    main()
