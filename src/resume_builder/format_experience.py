"""Format experience entries for Word documents.

Supports both:
  - Legacy format: experience with nested projects (actions + skills per project)
  - JSON schema format: experience with flat achievements + technologies lists
"""
import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


def format_experience(doc, experience):
    """Add experience entries to *doc*."""
    for exp in experience:
        # Build header text
        date_str = getattr(exp, "date_range", None) or exp.dates or ""
        text = f"{exp.role} at {exp.company_name} in {exp.location} - {date_str}"
        h = doc.add_heading(text, level=3)
        h.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

        # Description (new schema)
        if getattr(exp, "description", None):
            p.add_run(exp.description + "\n").italic = True

        # Legacy project-based format
        if exp.projects:
            for proj in exp.projects:
                # Handle both list-of-projects and single-project
                items = proj if isinstance(proj, list) else [proj]
                for j in items:
                    p.add_run(f"\n{j.name} for {j.duration}:\n").bold = True
                    p.add_run(f"{j.description}\n").italic = True
                    for a in j.actions:
                        p.add_run(f"- {a}\n")

        # Flat achievements (new schema)
        if getattr(exp, "achievements", None):
            for achievement in exp.achievements:
                p.add_run(f"- {achievement}\n")

        # Technologies list (new schema)
        if getattr(exp, "technologies", None):
            p.add_run("\nTechnologies: ").bold = True
            p.add_run(", ".join(exp.technologies))


def format_experience_skills(doc, experience):
    """Add per-experience skill summaries to *doc*."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    for exp in experience:
        # Legacy project-based skills
        if exp.projects:
            for proj in exp.projects:
                items = proj if isinstance(proj, list) else [proj]
                for j in items:
                    if j.skills:
                        p.add_run(f"{j.name}: ").bold = True
                        p.add_run(", ".join(str(x) for x in j.skills) + "\n")

        # Flat technologies (new schema)
        if getattr(exp, "technologies", None) and not exp.projects:
            p.add_run(f"{exp.role} @ {exp.company_name}: ").bold = True
            p.add_run(", ".join(exp.technologies) + "\n")
