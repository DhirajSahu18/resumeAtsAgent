from crewai.tools import BaseTool
from typing import Dict

class CoverLetterGeneratorTool(BaseTool):
    name: str = "Cover Letter Generator"
    description: str = "Generates a LaTeX formatted cover letter based on resume and JD."

    def _run(self, inputs: Dict) -> str:
        name = inputs["resume"].get("name", "Candidate")
        job_title = inputs["job_description"].get("job_title", "a position")
        matched_skills = inputs["ats_score"].get("matched_skills", [])

        return f"""
\\documentclass{{letter}}
\\usepackage{{hyperref}}

\\begin{{document}}

\\begin{{letter}}{{HR Department \\\\ Company Name}}

\\opening{{Dear Hiring Manager,}}

I am writing to express my interest in the {job_title} role at your organization. With my background and experience in {', '.join(matched_skills)}, I believe I am a strong fit for the position.

My resume showcases a strong alignment with your requirements, and I am confident my contributions can add significant value to your team.

Thank you for your time and consideration.

\\closing{{Sincerely,}}

{name}

\\end{{letter}}
\\end{{document}}
"""
