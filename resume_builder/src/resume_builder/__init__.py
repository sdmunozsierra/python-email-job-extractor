"""
resume-builder -- Generate .docx Word documents from structured resume data.

This package is intended to be consumed as a git subtree inside a parent
project.  It supports two input modes:

1. JSON resume schema -- a single JSON file with personal info, skills,
   experience, education, projects, certifications, and preferences.
2. Legacy Python data -- the original builder pattern using in-code objects.

Key entry points for programmatic usage::

    from resume_builder.schema_adapter import ResumeSchemaAdapter
    from resume_builder.cli import build_resume

    person = ResumeSchemaAdapter.from_json_file("resume.json")
    doc = build_resume(person)
    doc.save("output.docx")
"""

__version__ = "0.1.0"
