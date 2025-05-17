from crewai.tools import BaseTool as Tool

class CoverLetterGeneratorTool(Tool):
    name:str = "CoverLetterGeneratorTool"
    description:str = "Generates a LaTeX-formatted cover letter tailored to the job and resume."

    def _run(self, resume_json: dict, jd_summary: dict) -> str:
        """
        Generate a LaTeX cover letter.
        Args:
            resume_json: Optimized resume JSON.
            jd_summary: Parsed job description data.
        Returns:
            LaTeX-formatted cover letter string.
        """
        name = resume_json.get("name", "Candidate")
        job_title = jd_summary.get("job_title", "the position")
        company = jd_summary.get("company", "the company") if " at " not in jd_summary.get("job_title", "") else jd_summary.get("job_title", "").split(" at ")[1]
        skills = ", ".join(resume_json.get("skills", [])[:3])  # Highlight top 3 skills
        experience = resume_json.get("experience", [None])[0] or "relevant professional experience"

        cover_letter = f"""
\\documentclass{{letter}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{hyperref}}
\\signature{{{name}}}
\\address{{{name} \\\\ {resume_json.get('email', 'N/A')} \\\\ {resume_json.get('phone', 'N/A')}}}
\\begin{{document}}

\\begin{{letter}}{{Hiring Manager \\\\ {company} \\\\ Address Line 1 \\\\ City, State, ZIP}}
\\opening{{Dear Hiring Manager,}}

I am excited to apply for the {job_title} position at {company}. With my expertise in {skills} and {experience}, I am confident in my ability to contribute to your team and help achieve your organization's goals.

Your commitment to [mention something specific from the job description, e.g., "delivering innovative scheduling solutions for higher education"] resonates with my passion for [related passion, e.g., "enhancing educational experiences through technology"]. At [previous company or role], I successfully [specific achievement, e.g., "developed a web-based application that improved scheduling efficiency by 20\\%"]. My experience aligns closely with the responsibilities of this role, including [specific responsibility from jd_summary, e.g., "designing and maintaining software solutions"].

I am particularly drawn to {company}'s [specific value or goal, e.g., "focus on improving student outcomes"], and I am eager to bring my skills in [specific skill, e.g., "PHP Laravel and React"] to support your mission. I am confident that my technical expertise and collaborative approach make me a strong candidate for this role.

Thank you for considering my application. I look forward to the opportunity to discuss how I can contribute to {company}'s success. Please feel free to contact me at {resume_json.get('email', 'N/A')} or {resume_json.get('phone', 'N/A')}.

\\closing{{Sincerely,}}
\\end{{letter}}
\\end{{document}}
"""
        return cover_letter