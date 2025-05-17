from crewai.tools import BaseTool
from typing import Dict
import re

class LatexToJsonTool(BaseTool):
    name: str = "Resume PDF Text to JSON Tool"
    description: str = "Converts raw resume text into structured JSON format."

    def _run(self, text: str) -> Dict:
        data = {}

        # Basic patterns (customize further based on your resume structure)
        data['name'] = re.findall(r'^[A-Z][a-z]+ [A-Z][a-z]+', text)[0] if re.findall(r'^[A-Z][a-z]+ [A-Z][a-z]+', text) else "Unknown"
        data['email'] = re.findall(r'[\w\.-]+@[\w\.-]+', text)[0] if re.findall(r'[\w\.-]+@[\w\.-]+', text) else "Unknown"
        data['phone'] = re.findall(r'\+?\d[\d\s-]{7,}', text)[0] if re.findall(r'\+?\d[\d\s-]{7,}', text) else "Unknown"

        # Skills
        skills_match = re.findall(r'Skills\s*:?\s*(.*?)\n', text, re.IGNORECASE | re.DOTALL)
        data['skills'] = re.split(r',\s*|\s{2,}', skills_match[0]) if skills_match else []

        # Education
        education = re.findall(r'(Bachelor|Master|B\.Tech|M\.Tech|Ph\.D).*?\n', text, re.IGNORECASE)
        data['education'] = education if education else []

        # Experience
        experience = re.findall(r'(?:Experience|Work).*?:?\s*(.*?)\n(?:\s*\n|$)', text, re.IGNORECASE | re.DOTALL)
        data['experience'] = experience

        return data
