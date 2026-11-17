"""Reads the resume (PDF or DOCX) and extracts tech skills from it."""
import re
from pathlib import Path

# Skills we look for. Add more here if your resume has others.
SKILL_KEYWORDS = [
    "python", "java", "javascript", "typescript", "node.js", "nodejs", "express",
    "react", "next.js", "angular", "vue", "html", "css", "tailwind", "bootstrap",
    "django", "flask", "fastapi", "spring", "spring boot", "mongodb", "mysql",
    "postgresql", "sql", "redis", "docker", "kubernetes", "aws", "azure", "gcp",
    "git", "rest", "graphql", "jwt", "redux", "linux", "ci/cd", "jenkins",
    "hibernate", "jdbc", "servlets", "jsp", "postman", "github", "render", "mern",
    "data structures", "algorithms", "oop", "dbms", "tensorflow", "keras",
    "machine learning", "deep learning",
]


def read_resume_text(path: Path) -> str:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Resume not found: {path}. Put your resume there or set RESUME_PATH in .env")
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    if suffix == ".docx":
        from docx import Document
        return "\n".join(p.text for p in Document(str(path)).paragraphs)
    raise ValueError("Resume must be a .pdf or .docx file")


def extract_skills(text: str) -> list[str]:
    lowered = text.lower()
    found = []
    for skill in SKILL_KEYWORDS:
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, lowered):
            found.append(skill)
    return found


def extract_email_and_phone(text: str) -> dict:
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    phone = re.search(r"\+?\d[\d\s-]{8,14}\d", text)
    return {
        "email": email.group(0) if email else "",
        "phone": phone.group(0).strip() if phone else "",
    }


def load_profile(path: Path) -> dict:
    text = read_resume_text(path)
    skills = extract_skills(text)
    contact = extract_email_and_phone(text)
    return {"skills": skills, "contact": contact, "text_length": len(text)}


if __name__ == "__main__":
    import sys
    from config import RESUME_PATH
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else RESUME_PATH
    profile = load_profile(target)
    print("Skills found:", ", ".join(profile["skills"]) or "none")
    print("Contact found:", profile["contact"])
