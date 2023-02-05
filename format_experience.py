import docx
def format_experience(doc, experience):
    for exp in experience:
        #p = doc.add_paragraph()
        #p.paragraph_format.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.JUSTIFY
        text = f"{exp.role} at {exp.company_name} in {exp.location} - {exp.dates}"
        h = doc.add_heading(text, level=3)
        h.paragraph_format.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.JUSTIFY

        p = doc.add_paragraph()
        for proj in exp.projects:
            for j in proj:
                #p.add_run(f"{j}")
                p.add_run(f"\n{j.name} for {j.duration}:\n").bold = True
                p.add_run(f"{j.description}\n").italic = True
                #p.add_run(f"{j.team_size}").bold = True
                for a in j.actions:
                    p.add_run(f"- {a}\n")

def format_experience_skills(doc, experience):
    p = doc.add_paragraph()
    for exp in experience:
        for proj in exp.projects:
            for j in proj:
                p.add_run(f"{j.name}: ").bold = True
                p.add_run(", ".join([str(x) for x in j.skills])+"\n")