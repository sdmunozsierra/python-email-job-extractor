"""CLI entry point for resume-builder.

Usage (via uv)::

    uv run resume-builder --json resume.json --output my_resume.docx
    uv run resume-builder                        # legacy Python data

Usage (direct)::

    python -m resume_builder --json resume.json
"""

import argparse

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH

from resume_builder.person_builder import PersonBuilder
from resume_builder.education_builder import EducationFactory
from resume_builder.cert_builder import CertFactory
from resume_builder.format_experience import format_experience, format_experience_skills
from resume_builder.schema_adapter import ResumeSchemaAdapter


# ---------------------------------------------------------------------------
# Resume builder (works with both legacy and JSON-schema Person objects)
# ---------------------------------------------------------------------------

def build_resume(person):
    """Build a Word document from a Person object."""
    doc = docx.Document()

    # --- Header -----------------------------------------------------------
    header = doc.add_heading(person.name or "Resume", level=1)
    if person.job_title:
        header.add_run("\n" + person.job_title).bold = True
    if person.summary:
        p = doc.add_paragraph()
        p.add_run(person.summary).italic = True

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
        p = doc.add_paragraph()
        p.add_run(" | ".join(contact_parts))
    doc.add_paragraph()

    # --- Experience -------------------------------------------------------
    doc.add_heading("Experience", level=2)
    format_experience(doc, person.experience)
    doc.add_paragraph()

    # --- Education --------------------------------------------------------
    if person.education:
        doc.add_heading("Education", level=2)
        for edu in person.education:
            title = getattr(edu, "display_title", None)
            if title:
                text = f"{title} — {edu.school_name}"
            else:
                text = f"{edu.major} — {edu.school_name}"
            h = doc.add_heading(text, level=3)
            p = doc.add_paragraph()
            if edu.location:
                p.add_run(f"Location: {edu.location}\n")
            date_range = getattr(edu, "date_range", None) or getattr(edu, "dates", None)
            if date_range:
                p.add_run(f"Dates: {date_range}\n")
            if edu.gpa:
                p.add_run(f"GPA: {edu.gpa}\n")
            if getattr(edu, "honors", None):
                p.add_run(f"Honors: {edu.honors}\n")
            coursework = edu.coursework
            if coursework:
                flat = []
                for item in coursework:
                    if isinstance(item, list):
                        flat.extend(item)
                    else:
                        flat.append(item)
                p.add_run("Coursework: ").bold = True
                p.add_run(", ".join(str(c) for c in flat))
        doc.add_paragraph()

    # --- Skills -----------------------------------------------------------
    doc.add_heading("Skills", level=2)

    # Experience-derived skills (legacy)
    has_project_skills = any(
        getattr(exp, "projects", None) for exp in person.experience
    )
    if has_project_skills:
        doc.add_heading("Experience Skills", level=3)
        format_experience_skills(doc, person.experience)

    # Technical skills (A-z)
    if person.skills:
        doc.add_heading("Technical Skills (A-z)", level=3)
        arr = sorted(person.skills)
        p = doc.add_paragraph()
        p.add_run(", ".join(str(x) for x in arr))

    # Soft skills
    if person.soft_skills:
        doc.add_heading("Soft Skills", level=3)
        p = doc.add_paragraph()
        p.add_run(", ".join(person.soft_skills))

    # Spoken languages
    if person.languages:
        doc.add_heading("Languages", level=3)
        p = doc.add_paragraph()
        lang_strs = []
        for lang in person.languages:
            if isinstance(lang, dict):
                lang_strs.append(
                    f"{lang.get('language', '?')} ({lang.get('proficiency', '?')})"
                )
            else:
                lang_strs.append(str(lang))
        p.add_run(", ".join(lang_strs))

    doc.add_paragraph()

    # --- Projects (top-level) ---------------------------------------------
    if person.projects:
        doc.add_heading("Projects", level=2)
        for proj in person.projects:
            doc.add_heading(proj.name, level=3)
            p = doc.add_paragraph()
            p.add_run(proj.description).italic = True
            if proj.url:
                p.add_run(f"\nURL: {proj.url}")
            bullets = getattr(proj, "all_bullets", proj.highlights or proj.actions)
            for bullet in bullets:
                p.add_run(f"\n- {bullet}")
            tech = getattr(proj, "all_tech", proj.technologies or proj.skills)
            if tech:
                p.add_run(f"\nTechnologies: {', '.join(tech)}")
        doc.add_paragraph()

    # --- Activities -------------------------------------------------------
    if person.activities:
        doc.add_heading("Activities", level=2)
        p = doc.add_paragraph()
        p.add_run(", ".join(str(x) for x in person.activities))

    # --- Certifications ---------------------------------------------------
    if person.certifications:
        doc.add_heading("Certifications", level=2)
        table = doc.add_table(rows=1, cols=3)
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "Name"
        hdr_cells[1].text = "Issuer"
        hdr_cells[2].text = "Date"
        for cert in person.certifications:
            row_cells = table.add_row().cells
            row_cells[0].text = cert.title or ""
            row_cells[1].text = cert.issuer or ""
            row_cells[2].text = cert.completion_date or ""

    # --- Preferences ------------------------------------------------------
    if person.preferences:
        doc.add_heading("Preferences", level=2)
        p = doc.add_paragraph()
        prefs = person.preferences
        if prefs.get("desired_roles"):
            p.add_run("Desired Roles: ").bold = True
            p.add_run(", ".join(prefs["desired_roles"]) + "\n")
        if prefs.get("industries"):
            p.add_run("Industries: ").bold = True
            p.add_run(", ".join(prefs["industries"]) + "\n")
        if prefs.get("locations"):
            p.add_run("Locations: ").bold = True
            p.add_run(", ".join(prefs["locations"]) + "\n")
        if prefs.get("remote_preference"):
            p.add_run("Remote Preference: ").bold = True
            p.add_run(prefs["remote_preference"] + "\n")
        if prefs.get("engagement_types"):
            p.add_run("Engagement Types: ").bold = True
            p.add_run(", ".join(prefs["engagement_types"]) + "\n")

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
