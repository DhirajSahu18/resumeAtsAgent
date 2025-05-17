# tools/latex_to_json_tool.py
from crewai.tools import BaseTool
import re
import json

class LatexToJsonTool(BaseTool):
    name:str = "LatexToJsonTool"
    description:str = "Converts a LaTeX resume to structured JSON format."

    def _run(self, latex_text: str) -> str:
        # Very basic LaTeX section extraction
        sections = re.findall(r'\\section\*{(.+?)}(.+?)(?=\\section|\Z)', latex_text, re.S)
        resume = {}
        for title, content in sections:
            clean = re.sub(r'\\.+?{|}', '', content)
            resume[title.strip()] = clean.strip()
        return json.dumps(resume, indent=2)
