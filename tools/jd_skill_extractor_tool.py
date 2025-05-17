from crewai.tools import BaseTool
from typing import Dict
import re

class JDSkillExtractorTool(BaseTool):
    name: str = "JD Skill Extractor Tool"
    description: str = "Extracts job title, skills, responsibilities, and requirements from JD text."

    def _run(self, jd_text: str) -> Dict:
        skills = re.findall(r'\b(machine learning|deep learning|python|tensorflow|nlp|docker|aws|deployment|git)\b', jd_text, re.IGNORECASE)
        skills = list(set([s.lower() for s in skills]))

        return {
            "job_title": jd_text.split("\n")[0],
            "skills": skills,
            "responsibilities": "Extracted based on keyword patterns or bullet points.",
            "requirements": "Parsed general required technologies and degrees."
        }
