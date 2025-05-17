# tools/cover_letter_generator_tool.py
from crewai.tools import BaseTool
from gemini import model

class CoverLetterGeneratorTool(BaseTool):
    name:str = "CoverLetterGeneratorTool"
    description:str = "Generates a personalized cover letter in LaTeX format."

    def _run(self, resume_json: str, jd_summary: str) -> str:
        prompt = f"""
        Write a professional cover letter in LaTeX format for this job description:

        Job:
        {jd_summary}

        Use the following resume data:
        {resume_json}

        Make sure the tone is formal, enthusiastic, and tailored.
        """
        response = model.generate_content(prompt)
        return response.text
