from crewai.tools import BaseTool
from typing import Dict

class ATSMetricsTool(BaseTool):
    name: str = "ATS Score Calculator"
    description: str = "Compares resume JSON with JD JSON to compute ATS score and suggestions."

    def _run(self, inputs: Dict) -> Dict:
        resume = inputs.get("resume", {})
        jd = inputs.get("job_description", {})

        resume_skills = set([s.lower() for s in resume.get("skills", [])])
        jd_skills = set([s.lower() for s in jd.get("skills", [])])

        matched = resume_skills & jd_skills
        missing = jd_skills - resume_skills

        score = int(len(matched) / max(len(jd_skills), 1) * 100)

        return {
            "score": score,
            "matched_skills": list(matched),
            "missing_skills": list(missing),
            "suggestions": f"Add missing keywords: {', '.join(missing)}"
        }
