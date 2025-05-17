# tools/jd_skill_extractor_tool.py
from crewai.tools import BaseTool
from gemini import model

class JDSkillExtractorTool(BaseTool):
    name:str = "JDSkillExtractorTool"
    description:str = "Extracts skills, keywords, and role insights from a job description."

    def _run(self, job_description: str) -> dict:
        prompt = f"""
        Extract the following from this job description:
        1. Job Title
        2. Company Name
        3. Key Technical Skills
        4. Soft Skills
        5. Responsibilities
        6. Required Experience

        Text:
        {job_description}
        """
        response = model.generate_content(prompt)
        return response.text
