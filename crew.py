# crew.py

import os
from crewai import Agent, Task, Crew, LLM
from tools.latex_to_json_tool import LatexToJsonTool
from tools.jd_skill_extractor_tool import JDSkillExtractorTool
from tools.ats_metrics_tool import ATSMetricsTool
from tools.resume_rewrite_tool import ResumeRewriteTool
from tools.cover_letter_generator_tool import CoverLetterGeneratorTool
from pdfminer.high_level import extract_text
from dotenv import load_dotenv

load_dotenv()

llm = LLM(
    model="gemini/gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7
)

def run_resume_optimizer(job_description: str):
    resume_text = extract_text("Dhiraj_Sahu_Resume.pdf")  # Your fixed resume
    # Agents
    resume_parser_agent = Agent(
        role='Resume Parser',
        goal='Parse resume text and output a structured JSON',
        backstory='Specializes in interpreting resumes and converting them into structured data formats.',
        tools=[LatexToJsonTool()],
        llm=llm,
        verbose=True
    )

    jd_parser_agent = Agent(
        role='JD Analyzer',
        goal='Extract keywords and job insights from job description text',
        backstory='Expert in understanding job postings and extracting key elements for ATS analysis.',
        tools=[JDSkillExtractorTool()],
        llm=llm,
        verbose=True
    )

    ats_scorer_agent = Agent(
        role='ATS Scorer',
        goal='Compare resume and job description to determine ATS match score and suggestions',
        backstory='Acts as an ATS system to identify keyword matches and rate the resume\'s relevance.',
        tools=[ATSMetricsTool()],
        llm=llm,
        verbose=True
    )

    resume_optimizer_agent = Agent(
        role='Resume Optimizer',
        goal='Enhance resume based on job description to improve ATS score',
        backstory='Expert in tailoring resumes to job descriptions by inserting relevant keywords and skills.',
        tools=[ResumeRewriteTool()],
        llm=llm,
        verbose=True
    )

    cover_letter_agent = Agent(
        role='Cover Letter Generator',
        goal='Write a tailored LaTeX cover letter for the given job and resume',
        backstory='Experienced in composing professional and personalized cover letters in LaTeX format.',
        tools=[CoverLetterGeneratorTool()],
        llm=llm,
        verbose=True
    )

    # Tasks
    task_1 = Task(
        description=f'Parse the following resume text into structured JSON:\n\n{resume_text}',
        expected_output='JSON representation of the resume',
        agent=resume_parser_agent
    )

    task_2 = Task(
        description=f'Analyze the following job description and extract job title, skills, responsibilities, and requirements:\n\n{job_description}',
        expected_output='Parsed job description summary with keywords and key points',
        agent=jd_parser_agent
    )

    task_3 = Task(
        description='Calculate ATS score by comparing the resume JSON and job description summary.',
        expected_output='ATS score report with matched and missing keywords, and suggestions',
        agent=ats_scorer_agent
    )

    task_4 = Task(
        description='Rewrite the resume JSON to improve the ATS score based on JD analysis.',
        expected_output='Optimized resume JSON with better job relevance and keyword inclusion',
        agent=resume_optimizer_agent
    )

    task_5 = Task(
        description='Generate a personalized LaTeX cover letter using the updated resume and job description.',
        expected_output='LaTeX formatted cover letter tailored to the job also with correct indentation , formatting and structure',
        agent=cover_letter_agent
    )

    crew = Crew(
        agents=[
            resume_parser_agent,
            jd_parser_agent,
            ats_scorer_agent,
            resume_optimizer_agent,
            cover_letter_agent
        ],
        tasks=[task_1, task_2, task_3, task_4, task_5],
        verbose=True
    )

    result = crew.kickoff()
    print("\n\n=== FINAL OUTPUT ===\n")
    print(result)

# Entry point
if __name__ == '__main__':
    # Example usage
    job_description = """We are looking for a Machine Learning Engineer with experience in NLP, Python, TensorFlow, and model deployment..."""
    run_resume_optimizer(job_description)
