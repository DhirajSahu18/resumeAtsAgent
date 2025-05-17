# tools/ats_metrics_tool.py
from crewai.tools import BaseTool
from gemini import model
import json

class ATSMetricsTool(BaseTool):
    name:str = "ATSMetricsTool"
    description:str = "Compares resume and JD data to calculate ATS score and identify missing content."

    def _run(self, resume_json: str, jd_summary: str) -> str:
        prompt = f"""
        Compare the following resume (in JSON) with the job description summary. 
        Score it out of 100 based on relevance and keyword match.

        Resume JSON:
        {resume_json}

        JD Summary:
        {jd_summary}

        Output:
        - ATS Score
        - Matched Keywords
        - Missing Keywords
        - Suggestions to improve
        """
        response = model.generate_content(prompt)
        return response.text
