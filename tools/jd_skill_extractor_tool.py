import re
from crewai.tools import BaseTool as Tool

class JDSkillExtractorTool(Tool):
    name:str = "JDSkillExtractorTool"
    description:str = "Extracts job title, skills, responsibilities, and requirements from a job description."

    def _run(self, jd_text: str) -> dict:
        """
        Parse job description text to extract key elements.
        Args:
            jd_text: Raw job description text.
        Returns:
            Dictionary containing job title, skills, responsibilities, and requirements.
        """
        jd_summary = {
            "job_title": "",
            "skills": [],
            "responsibilities": [],
            "requirements": []
        }

        # Extract job title
        title_pattern = r"(?:Position|Role|Job Title)[:\s]*([^\n]+)|([A-Z][\w\s]+?)(?=\s+\bat\b|\s+\bfor\b|\s+\bto\b|\n)"
        title_match = re.search(title_pattern, jd_text, re.IGNORECASE)
        if title_match:
            jd_summary["job_title"] = title_match.group(1) or title_match.group(2) or "Unknown"

        # Extract skills (looks for phrases like "skills", "experience in", "knowledge of")
        skills_pattern = r"(?:skills|experience in|knowledge of|proficient in|using|use of)[\s:]*([^\n.]+)"
        skills_matches = re.findall(skills_pattern, jd_text, re.IGNORECASE)
        for match in skills_matches:
            skills = [s.strip() for s in match.split(",") if s.strip()]
            jd_summary["skills"].extend(skills)

        # Extract responsibilities (looks for action-oriented phrases)
        responsibilities_pattern = r"(?:responsibilities|you will|duties)[\s:]*([\s\S]*?)(?=\n[A-Z]|\Z)"
        responsibilities_match = re.search(responsibilities_pattern, jd_text, re.IGNORECASE)
        if responsibilities_match:
            responsibilities_text = responsibilities_match.group(1).strip()
            jd_summary["responsibilities"] = [r.strip() for r in responsibilities_text.split(".") if r.strip()]

        # Extract requirements (looks for "requirements", "you’ll need", etc.)
        requirements_pattern = r"(?:requirements|you’ll need|qualifications)[\s:]*([\s\S]*?)(?=\n[A-Z]|\Z)"
        requirements_match = re.search(requirements_pattern, jd_text, re.IGNORECASE)
        if requirements_match:
            requirements_text = requirements_match.group(1).strip()
            jd_summary["requirements"] = [req.strip() for req in requirements_text.split(".") if req.strip()]

        # Additional cleanup: Remove duplicates and normalize
        jd_summary["skills"] = list(set(jd_summary["skills"]))
        jd_summary["responsibilities"] = list(set(jd_summary["responsibilities"]))
        jd_summary["requirements"] = list(set(jd_summary["requirements"]))

        return jd_summary