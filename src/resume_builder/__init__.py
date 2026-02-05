"""resume-builder — generate .docx resumes from a JSON schema or Python data.

Quick start::

    from resume_builder.schema_adapter import ResumeSchemaAdapter
    from resume_builder.cli import build_resume

    person = ResumeSchemaAdapter.from_json_file("resume.json")
    doc = build_resume(person)
    doc.save("output.docx")
"""

__version__ = "0.1.0"
