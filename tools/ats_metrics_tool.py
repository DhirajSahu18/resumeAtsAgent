from crewai.tools import BaseTool as Tool
from fuzzywuzzy import fuzz
import json

class ATSMetricsTool(Tool):
    name:str = "ATSMetricsTool"
    description:str = "Compares resume and job description to calculate ATS score and provide suggestions."

    def _run(self, resume_json: dict, jd_summary: dict) -> dict:
        """
        Calculate ATS score by comparing resume and job description.
        Args:
            resume_json: Structured resume data.
            jd_summary: Parsed job description data.
        Returns:
            Dictionary with ATS score, matched keywords, missing keywords, and suggestions.
        """
        ats_report = {
            "ats_score": 0,
            "matched_keywords": [],
            "missing_keywords": [],
            "suggestions": []
        }

        # Extract skills from resume and job description
        resume_skills = set(resume_json.get("skills", []))
        jd_skills = set(jd_summary.get("skills", []))

        # Calculate matches using fuzzy matching for partial similarity
        matched_keywords = []
        for resume_skill in resume_skills:
            for jd_skill in jd_skills:
                if fuzz.ratio(resume_skill.lower(), jd_skill.lower()) > 80:  # Threshold for similarity
                    matched_keywords.append(jd_skill)
                    break

        # Identify missing keywords
        missing_keywords = list(jd_skills - set(matched_keywords))
        ats_report["matched_keywords"] = matched_keywords
        ats_report["missing_keywords"] = missing_keywords

        # Calculate ATS score (percentage of matched keywords)
        total_keywords = len(jd_skills)
        matched_count = len(matched_keywords)
        ats_report["ats_score"] = (matched_count / total_keywords * 100) if total_keywords > 0 else 0

        # Generate suggestions
        if missing_keywords:
            ats_report["suggestions"].append(
                f"Add the following missing skills to your resume: {', '.join(missing_keywords)}"
            )
        if ats_report["ats_score"] < 70:
            ats_report["suggestions"].append(
                "Tailor your experience descriptions to include responsibilities mentioned in the job description."
            )
        if not resume_json.get("education"):
            ats_report["suggestions"].append("Ensure your education section is complete and relevant.")

        return ats_report