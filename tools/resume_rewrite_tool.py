# tools/resume_rewrite_tool.py
from crewai.tools import BaseTool
from gemini import model

class ResumeRewriteTool(BaseTool):
    name:str = "ResumeRewriteTool"
    description:str = "Updates resume content to better match the job description."

    def _run(self, resume_json: str, jd_summary: str) -> str:
        prompt = f"""
        You are an expert resume editor.

        Based on this job description:
        {jd_summary}

        Rewrite and enhance this resume (in JSON format) to:
        - Include missing relevant skills (realistically)
        - Mirror language from the job description
        - Keep content honest and concise

        Resume JSON:
        {resume_json}

        Return the updated resume JSON:
        """
        response = model.generate_content(prompt)
        return response.text
