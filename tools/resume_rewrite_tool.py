from crewai.tools import BaseTool
from typing import Dict

class ResumeRewriteTool(BaseTool):
    name: str = "Resume Rewriter"
    description: str = "Rewrites resume JSON to include missing ATS keywords."

    def _run(self, inputs: Dict) -> Dict:
        resume = inputs.get("resume", {})
        missing = inputs.get("ats_score", {}).get("missing_skills", [])

        updated_skills = list(set(resume.get("skills", []) + missing))
        resume["skills"] = updated_skills

        return resume
