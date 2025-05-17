from crewai.tools import BaseTool as Tool
import copy

class ResumeRewriteTool(Tool):
    name:str = "ResumeRewriteTool"
    description:str = "Optimizes resume JSON by incorporating job description keywords and suggestions."

    def _run(self, resume_json: dict, jd_summary: dict, ats_report: dict) -> dict:
        """
        Rewrite resume JSON to improve ATS score.
        Args:
            resume_json: Original resume JSON.
            jd_summary: Parsed job description data.
            ats_report: ATS metrics report with suggestions.
        Returns:
            Optimized resume JSON.
        """
        optimized_resume = copy.deepcopy(resume_json)

        # Add missing skills from ATS report
        missing_keywords = ats_report.get("missing_keywords", [])
        current_skills = set(optimized_resume.get("skills", []))
        optimized_resume["skills"] = list(current_skills.union(missing_keywords))

        # Tailor experience to include job responsibilities
        responsibilities = jd_summary.get("responsibilities", [])
        if responsibilities:
            for responsibility in responsibilities[:2]:  # Add up to 2 responsibilities to avoid overloading
                optimized_resume["experience"].append(
                    f"Contributed to {responsibility.lower()} in a professional setting."
                )

        # Ensure education section is populated if empty
        if not optimized_resume.get("education"):
            optimized_resume["education"] = ["Relevant coursework or degree aligned with job requirements."]

        # Clean up duplicates
        optimized_resume["skills"] = list(set(optimized_resume["skills"]))
        optimized_resume["experience"] = list(set(optimized_resume["experience"]))
        optimized_resume["education"] = list(set(optimized_resume["education"]))

        return optimized_resume