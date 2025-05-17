import os
import re
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

def extract_company_name(jd_text: str) -> str:
    match = re.search(r'\b(at|@)\s+([A-Z][\w& ]+)', jd_text, re.IGNORECASE)
    return match.group(2).strip().replace(" ", "_") if match else "company"

def resume_json_to_latex(resume_json: dict) -> str:
    skills = ', '.join(resume_json.get("skills", []))
    education = '\n'.join(resume_json.get("education", []))
    experience = '\n'.join(resume_json.get("experience", []))

    return f"""
\\documentclass{{article}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{hyperref}}
\\begin{{document}}

\\title{{Resume - {resume_json.get('name', 'Candidate')}}}
\\author{{{resume_json.get('name', 'Candidate')}}}
\\date{{}}

\\maketitle

\\section*{{Contact Information}}
Email: {resume_json.get('email', 'N/A')} \\\\
Phone: {resume_json.get('phone', 'N/A')}

\\section*{{Skills}}
{skills}

\\section*{{Education}}
{education}

\\section*{{Experience}}
{experience}

\\end{{document}}
"""

def run_resume_optimizer(job_description: str):
    resume_text = extract_text("Dhiraj_Sahu_Resume.pdf")

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

    resume_latex_agent = Agent(
        role='Resume LaTeX Generator',
        goal='Generate LaTeX resume from structured JSON data',
        backstory='Specializes in converting structured resume data into LaTeX format for easy printing.',
        tools=[],
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
        description='Generate LaTeX resume from the optimized resume JSON.',
        expected_output='LaTeX formatted resume with correct indentation , formatting and structure',
        agent=resume_latex_agent
    )

    task_6 = Task(
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
            resume_latex_agent,
            cover_letter_agent
        ],
        tasks=[task_1, task_2, task_3, task_4, task_5 , task_6],
        llm=llm,
        verbose=True
    )

    results = crew.kickoff()
    print(results.tasks_output[3])  # See available keys like 'task_1', 'task_2', etc.


    optimized_resume_json = results.tasks_output[3]
    cover_letter_latex = results.tasks_output[5]

    name = optimized_resume_json.get("name", "candidate").replace(" ", "_")
    company = extract_company_name(job_description).lower()

    resume_latex = resume_json_to_latex(optimized_resume_json)

    os.makedirs("output", exist_ok=True)
    resume_file = f"output/{name}_resume_{company}.tex"
    cover_letter_file = f"output/{name}_cover_letter_{company}.tex"

    with open(resume_file, "w") as f:
        f.write(resume_latex)

    with open(cover_letter_file, "w") as f:
        f.write(cover_letter_latex)

    print(f"\n✅ Saved:\n{resume_file}\n{cover_letter_file}")



# Example usage
if __name__ == '__main__':
    job_description = """
    
Are you a Software Engineer looking for your next opportunity? How would you like to shape the future of some of our EdTech products with your coding skills? Join us and be a part of something brilliant! 

Tribal is a leading EdTech business providing market leading software solutions to the global education market. We strive to research, develop and deliver the products, services and solutions needed by education institutes worldwide to support their primary goals of educating students, providing optimum learning experiences and ultimately delivering successful outcomes.

We are recruiting for a Software Engineer to join our Semestry Development Team. Our Semestry product is a comprehensive software solution designed to address timetabling and scheduling challenges in higher education institutions. It offers a range of features to help universities plan, build, deliver, and operate schedules efficiently. It aims to enhance curriculum planning and improve the overall learning experience for students and faculty by providing insights and managing scheduling constraints.

This is a full time permanent role, offering a fully remote working arrangement with travel when required.

The Role

As a Software Engineer, part of our TermTime platform, you will be designing, developing, and maintaining our comprehensive timetabling and scheduling solutions. Not only that, you will also be part of the team who are reimagining this product, redeveloping and creating a brand new innovative and functional advanced platform for our customers! Your responsibilities will include:

Creating software solutions by writing clean, efficient and maintainable code.
Ensuring software quality by identifying and fixing bugs.
Working in partnership with Software Architect, other developers and testers to understand requirements to deliver features. 
Updating and improving existing software to enhance performance and functionality.
Analysing and addressing technical challenges to find effective solutions.
Recommend ideas on how the product can be developed and improved to enhance performance and usability.
The skills you’ll need:

Experience in a full stack Web-based software development role.
Use of PHP Laravel, TypeScript/JavaScript and React.
An understanding of best-practice related to crafting secure, efficient and high quality code.
Experience in agile methodologies.
It would be great if you had:

An understanding of best-practice database design for building efficient applications.
Experience with API design and 3rd party system integrations.
Experience with containerised applications.
Exposure to deploying code to cloud infrastructure.
Using best in class CI/CD techniques would be beneficial.
Experience in redeveloping a product from grass roots to deployment.
What can Tribal offer you? 

We offer a range of exceptional benefits to support your wellbeing and work-life balance, including a comprehensive Health Cash Plan, Private Medical Insurance and Employee Assistance Programme, along with a generous parental leave package and the ability to buy or sell holiday each year. We also offer the option of working overseas for up to 8 weeks per year. You'll also have access to E-Learning Opportunities to enhance your skills, Volunteer Days to give back to your community and access to Achievers, our reward and recognition platform, to ensure you can thrive both personally and professionally in a supportive and rewarding environment.

We’re committed to creating an environment that enables employees to balance their responsibilities inside and outside of work and encourage and support a range of flexible working patterns for all colleagues. If you need flexibility, apply and discuss your needs with us.

Criminal Records and Security Checks

If you are successful in your application, a security/criminal record check will be required before we can employ you, If, following the check the nature of a conviction is deemed unacceptable, this may lead to an offer of employment being withdrawn.

As an equal opportunity employer, Tribal celebrate diversity and are committed to creating an inclusive environment for all employees. We make sure that our recruitment and selection processes never discriminate based upon any protected characteristics and actively welcome applications from all groups, not least those underrepresented in the tech sector. 
    """
    run_resume_optimizer(job_description)
