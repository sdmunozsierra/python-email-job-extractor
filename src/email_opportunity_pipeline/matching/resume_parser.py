"""
Resume parser for JSON and Markdown formats.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    Resume,
    PersonalInfo,
    Skills,
    Skill,
    Language,
    Certification,
    Experience,
    Education,
    Project,
    JobPreferences,
)


class ResumeParser:
    """
    Parses resume files in various formats (JSON, Markdown).
    """

    def parse(self, file_path: str | Path) -> Resume:
        """
        Parse a resume file and return a Resume object.
        
        Args:
            file_path: Path to the resume file (.json or .md)
            
        Returns:
            Resume object
            
        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If file does not exist
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Resume file not found: {path}")
        
        content = path.read_text(encoding="utf-8")
        suffix = path.suffix.lower()
        
        if suffix == ".json":
            return self._parse_json(content, str(path))
        elif suffix in (".md", ".markdown"):
            return self._parse_markdown(content, str(path))
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def _parse_json(self, content: str, source_file: str) -> Resume:
        """Parse JSON format resume."""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in resume file: {e}")
        
        return Resume.from_dict(data, source_file=source_file)

    def _parse_markdown(self, content: str, source_file: str) -> Resume:
        """
        Parse Markdown format resume.
        
        Expects a structured markdown with headers like:
        # Name
        ## Contact
        ## Summary
        ## Skills
        ## Experience
        ## Education
        ## Projects
        """
        lines = content.strip().split("\n")
        
        # Initialize data structure
        data: Dict[str, Any] = {
            "personal": {"name": "Unknown"},
            "skills": {"technical": [], "soft": [], "languages": [], "certifications": []},
            "experience": [],
            "education": [],
            "projects": [],
        }
        
        current_section = None
        current_subsection = None
        current_entry: Optional[Dict] = None
        buffer: List[str] = []
        
        def flush_buffer():
            nonlocal buffer
            if buffer and current_entry is not None:
                text = " ".join(buffer).strip()
                if current_section == "experience":
                    if "description" not in current_entry:
                        current_entry["description"] = text
                elif current_section == "education":
                    if "notes" not in current_entry:
                        current_entry["notes"] = text
            buffer = []

        for line in lines:
            stripped = line.strip()
            
            # H1 - Name
            if stripped.startswith("# ") and not stripped.startswith("## "):
                data["personal"]["name"] = stripped[2:].strip()
                continue
            
            # H2 - Major sections
            if stripped.startswith("## "):
                flush_buffer()
                section_name = stripped[3:].strip().lower()
                current_section = self._normalize_section_name(section_name)
                current_subsection = None
                current_entry = None
                continue
            
            # H3 - Subsections (job titles, degrees, project names)
            if stripped.startswith("### "):
                flush_buffer()
                entry_name = stripped[4:].strip()
                current_entry = self._create_entry(current_section, entry_name, data)
                continue
            
            # Process content based on section
            if current_section == "contact" or current_section == "personal":
                self._parse_contact_line(stripped, data)
            elif current_section == "summary":
                if stripped:
                    data["personal"]["summary"] = data["personal"].get("summary", "") + stripped + " "
            elif current_section == "skills":
                self._parse_skills_line(stripped, data)
            elif current_section in ("experience", "education", "projects"):
                if stripped.startswith("- "):
                    item = stripped[2:].strip()
                    if current_entry:
                        self._add_item_to_entry(current_section, current_entry, item)
                elif stripped.startswith("**") and ":" in stripped:
                    self._parse_metadata_line(stripped, current_section, current_entry, data)
                elif stripped:
                    buffer.append(stripped)
        
        flush_buffer()
        
        # Clean up summary
        if data["personal"].get("summary"):
            data["personal"]["summary"] = data["personal"]["summary"].strip()
        
        return Resume.from_dict(data, source_file=source_file)

    def _normalize_section_name(self, name: str) -> str:
        """Normalize section names to standard keys."""
        mapping = {
            "contact": "contact",
            "contact info": "contact",
            "contact information": "contact",
            "personal": "personal",
            "personal info": "personal",
            "summary": "summary",
            "professional summary": "summary",
            "about": "summary",
            "about me": "summary",
            "objective": "summary",
            "skills": "skills",
            "technical skills": "skills",
            "core skills": "skills",
            "experience": "experience",
            "work experience": "experience",
            "employment": "experience",
            "employment history": "experience",
            "professional experience": "experience",
            "education": "education",
            "academic background": "education",
            "projects": "projects",
            "personal projects": "projects",
            "portfolio": "projects",
            "certifications": "certifications",
            "certificates": "certifications",
            "languages": "languages",
        }
        return mapping.get(name, name)

    def _parse_contact_line(self, line: str, data: Dict[str, Any]) -> None:
        """Parse a contact information line."""
        if not line:
            return
        
        lower = line.lower()
        
        # Email
        email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", line)
        if email_match:
            data["personal"]["email"] = email_match.group()
            return
        
        # Phone
        phone_match = re.search(r"[\d\s\-\(\)\+]{10,}", line)
        if phone_match and not any(kw in lower for kw in ["github", "linkedin", "http"]):
            data["personal"]["phone"] = phone_match.group().strip()
            return
        
        # LinkedIn
        if "linkedin" in lower:
            url_match = re.search(r"https?://[\w./\-]+", line)
            if url_match:
                data["personal"]["linkedin"] = url_match.group()
            return
        
        # GitHub
        if "github" in lower:
            url_match = re.search(r"https?://[\w./\-]+", line)
            if url_match:
                data["personal"]["github"] = url_match.group()
            return
        
        # Location (usually just text without special patterns)
        if "location" in lower or "," in line:
            # Remove label if present
            location = re.sub(r"^(location|address):?\s*", "", line, flags=re.I).strip()
            if location:
                data["personal"]["location"] = location

    def _parse_skills_line(self, line: str, data: Dict[str, Any]) -> None:
        """Parse a skills line."""
        if not line:
            return
        
        # Handle bullet points
        if line.startswith("- "):
            line = line[2:].strip()
        
        # Check for category prefix
        if ":" in line:
            category, skills_text = line.split(":", 1)
            category = category.strip().lower()
            skills_text = skills_text.strip()
        else:
            category = "technical"
            skills_text = line
        
        # Parse comma-separated skills
        skills = [s.strip() for s in re.split(r"[,;]", skills_text) if s.strip()]
        
        if any(kw in category for kw in ["soft", "interpersonal", "leadership"]):
            data["skills"]["soft"].extend(skills)
        elif any(kw in category for kw in ["language", "spoken"]):
            for lang in skills:
                data["skills"]["languages"].append({"language": lang})
        else:
            for skill in skills:
                # Check for level in parentheses
                level_match = re.search(r"\((\w+)\)$", skill)
                if level_match:
                    skill_name = skill[:level_match.start()].strip()
                    level = level_match.group(1).lower()
                else:
                    skill_name = skill
                    level = None
                
                data["skills"]["technical"].append({
                    "name": skill_name,
                    "level": level,
                    "category": category if category != "technical" else None,
                })

    def _create_entry(self, section: str, name: str, data: Dict[str, Any]) -> Optional[Dict]:
        """Create a new entry for a section."""
        if section == "experience":
            # Try to parse "Title at Company" or "Title - Company"
            if " at " in name:
                parts = name.split(" at ", 1)
                title, company = parts[0].strip(), parts[1].strip()
            elif " - " in name:
                parts = name.split(" - ", 1)
                title, company = parts[0].strip(), parts[1].strip()
            else:
                title, company = name, ""
            
            entry = {"title": title, "company": company, "achievements": [], "technologies": []}
            data["experience"].append(entry)
            return entry
        
        elif section == "education":
            # Try to parse "Degree in Field - Institution" or similar
            if " - " in name:
                parts = name.split(" - ", 1)
                degree_part, institution = parts[0].strip(), parts[1].strip()
            else:
                degree_part, institution = name, ""
            
            # Try to extract field from degree
            if " in " in degree_part:
                degree, field_name = degree_part.split(" in ", 1)
            else:
                degree, field_name = degree_part, None
            
            entry = {
                "degree": degree.strip(),
                "field": field_name.strip() if field_name else None,
                "institution": institution,
                "relevant_coursework": [],
            }
            data["education"].append(entry)
            return entry
        
        elif section == "projects":
            entry = {"name": name, "technologies": [], "highlights": []}
            data["projects"].append(entry)
            return entry
        
        return None

    def _add_item_to_entry(self, section: str, entry: Dict, item: str) -> None:
        """Add a bullet point item to an entry."""
        if section == "experience":
            entry["achievements"].append(item)
        elif section == "education":
            entry["relevant_coursework"].append(item)
        elif section == "projects":
            entry["highlights"].append(item)

    def _parse_metadata_line(
        self, 
        line: str, 
        section: str, 
        entry: Optional[Dict],
        data: Dict[str, Any]
    ) -> None:
        """Parse metadata lines like **Duration:** 2020-2023."""
        if not entry:
            return
        
        # Extract key-value from **Key:** Value format
        match = re.match(r"\*\*([^*]+)\*\*:?\s*(.+)", line)
        if not match:
            return
        
        key = match.group(1).strip().lower()
        value = match.group(2).strip()
        
        if section == "experience":
            if key in ("dates", "duration", "period"):
                # Try to parse date range
                if " - " in value:
                    start, end = value.split(" - ", 1)
                    entry["start_date"] = start.strip()
                    entry["end_date"] = end.strip() if end.strip().lower() != "present" else None
                    entry["current"] = end.strip().lower() == "present"
                else:
                    entry["start_date"] = value
            elif key == "location":
                entry["location"] = value
            elif key in ("tech", "technologies", "stack"):
                techs = [t.strip() for t in re.split(r"[,;]", value) if t.strip()]
                entry["technologies"].extend(techs)
            elif key == "company":
                entry["company"] = value
        
        elif section == "education":
            if key in ("dates", "duration", "years"):
                if " - " in value:
                    start, end = value.split(" - ", 1)
                    entry["start_date"] = start.strip()
                    entry["end_date"] = end.strip()
                else:
                    entry["end_date"] = value
            elif key == "gpa":
                entry["gpa"] = value
            elif key in ("honors", "awards"):
                entry["honors"] = value
            elif key == "location":
                entry["location"] = value
        
        elif section == "projects":
            if key in ("url", "link", "github"):
                entry["url"] = value
            elif key in ("tech", "technologies", "stack", "built with"):
                techs = [t.strip() for t in re.split(r"[,;]", value) if t.strip()]
                entry["technologies"].extend(techs)
            elif key == "description":
                entry["description"] = value


def parse_resume_file(file_path: str | Path) -> Resume:
    """
    Convenience function to parse a resume file.
    
    Args:
        file_path: Path to the resume file
        
    Returns:
        Resume object
    """
    parser = ResumeParser()
    return parser.parse(file_path)
