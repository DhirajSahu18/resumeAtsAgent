import os
import re
import json
from crewai import Agent, Task, Crew, LLM
from pdfminer.high_level import extract_text
from dotenv import load_dotenv

# PDF generation imports
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Flowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib import colors

load_dotenv()

llm = LLM(
    model="gemini/gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7
)

def extract_company_name(jd_text: str) -> str:
    """Extract company name from job description with improved pattern matching."""
    patterns = [
        r'\b(at|@)\s+([A-Z][\w& ]+)',
        r'position\s+(at|with)\s+([A-Z][\w& ]+)',
        r'(job|role|opportunity)\s+(at|with)\s+([A-Z][\w& ]+)',
        r'([A-Z][A-Za-z0-9]+([\s&]+[A-Z][A-Za-z0-9]+)*)\s+is\s+(looking|hiring|seeking)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, jd_text, re.IGNORECASE)
        if match:
            groups = match.groups()
            return groups[-1].strip().replace(" ", "_")
    
    return "Company"

class BulletPoint(Flowable):
    """Custom flowable for bullet points"""
    def __init__(self, text, bullet_char="•", indent=20):
        Flowable.__init__(self)
        self.text = text
        self.bullet_char = bullet_char
        self.indent = indent
        
    def draw(self):
        self.canv.drawString(0, 0, self.bullet_char)
        self.canv.drawString(self.indent, 0, self.text)
        
    def wrap(self, availWidth, availHeight):
        return availWidth, 14

def create_resume_pdf(resume_json: dict, filename: str):
    """Create a professional resume PDF using ReportLab."""
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=12,
        alignment=TA_CENTER,
        textColor=HexColor('#2C3E50')
    )
    
    contact_style = ParagraphStyle(
        'Contact',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=16,
        textColor=HexColor('#2C3E50'),
        borderWidth=1,
        borderColor=HexColor('#2C3E50'),
        borderPadding=4
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        leftIndent=0
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        leftIndent=20,
        bulletIndent=10
    )
    
    # Build the document
    story = []
    
    # Name
    name = resume_json.get('name', 'Candidate Name')
    story.append(Paragraph(name, title_style))
    
    # Contact information
    email = resume_json.get('email', 'email@example.com')
    phone = resume_json.get('phone', '(123) 456-7890')
    contact_info = f"✉ {email} | ☎ {phone}"
    story.append(Paragraph(contact_info, contact_style))
    
    # Skills section
    skills = resume_json.get('skills', [])
    if skills:
        story.append(Paragraph("SKILLS", section_header_style))
        skills_text = " • ".join(skills)
        story.append(Paragraph(skills_text, body_style))
        story.append(Spacer(1, 12))
    
    # Education section
    education = resume_json.get('education', [])
    if education:
        story.append(Paragraph("EDUCATION", section_header_style))
        for edu in education:
            story.append(Paragraph(f"• {edu}", bullet_style))
        story.append(Spacer(1, 12))
    
    # Experience section
    experience = resume_json.get('experience', [])
    if experience:
        story.append(Paragraph("EXPERIENCE", section_header_style))
        for exp in experience:
            # Job title and company
            job_title = f"<b>{exp.get('role', 'Role')}</b> at {exp.get('company', 'Company')} ({exp.get('year', 'Year')})"
            story.append(Paragraph(job_title, body_style))
            
            # Responsibilities
            responsibilities = exp.get('responsibilities', '')
            if responsibilities:
                # Split responsibilities into bullet points
                resp_items = re.split(r'[;.]\s+', responsibilities)
                resp_items = [r.strip() for r in resp_items if r.strip()]
                
                for resp in resp_items:
                    if resp and not resp.endswith('.'):
                        resp += '.'
                    story.append(Paragraph(f"• {resp}", bullet_style))
            
            story.append(Spacer(1, 8))
    
    # Build PDF
    doc.build(story)
    return True

def create_cover_letter_pdf(resume_json: dict, job_description: str, filename: str):
    """Create a professional cover letter PDF using ReportLab."""
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_LEFT,
        spaceAfter=20
    )
    
    date_style = ParagraphStyle(
        'Date',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_LEFT,
        spaceAfter=20
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        alignment=TA_LEFT
    )
    
    story = []
    
    # Header with contact info
    name = resume_json.get('name', 'Candidate Name')
    email = resume_json.get('email', 'email@example.com')
    phone = resume_json.get('phone', '(123) 456-7890')
    
    header_text = f"""<b>{name}</b><br/>
{email}<br/>
{phone}"""
    story.append(Paragraph(header_text, header_style))
    
    # Date
    from datetime import datetime
    current_date = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(current_date, date_style))
    
    # Company info
    company_name = extract_company_name(job_description)
    company_address = f"""Hiring Manager<br/>
{company_name}"""
    story.append(Paragraph(company_address, header_style))
    
    # Opening
    story.append(Paragraph("Dear Hiring Manager,", body_style))
    
    # Body paragraphs
    opening_para = f"I am writing to express my strong interest in the Software Engineer position at {company_name}. With my comprehensive background in software development and proven track record of delivering innovative solutions, I am confident that I would be a valuable addition to your team."
    story.append(Paragraph(opening_para, body_style))
    
    # Skills alignment paragraph
    skills = resume_json.get('skills', [])
    if skills:
        key_skills = ', '.join(skills[:5])  # Top 5 skills
        skills_para = f"My technical expertise includes {key_skills}, which directly aligns with the requirements outlined in your job posting. I have successfully applied these skills in various projects and collaborative environments, consistently delivering high-quality results that exceed expectations."
        story.append(Paragraph(skills_para, body_style))
    
    # Experience paragraph
    experience = resume_json.get('experience', [])
    if experience:
        recent_exp = experience[0] if experience else {}
        exp_para = f"In my recent role as {recent_exp.get('role', 'a developer')}, I have demonstrated my ability to work effectively in team environments while managing complex technical challenges. My experience has prepared me well for the responsibilities and opportunities that this position offers."
        story.append(Paragraph(exp_para, body_style))
    
    # Closing paragraph
    closing_para = f"I am excited about the opportunity to contribute to {company_name}'s continued success and innovation. I would welcome the chance to discuss how my skills, experience, and passion for technology can benefit your team. Thank you for considering my application."
    story.append(Paragraph(closing_para, body_style))
    
    # Sign-off
    story.append(Spacer(1, 20))
    story.append(Paragraph("Sincerely,", body_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(name, body_style))
    
    # Build PDF
    doc.build(story)
    return True

def run_resume_optimizer(job_description: str):
    """Main function to run the resume optimization process."""
    try:
        resume_text = extract_text("Dhiraj_Sahu_Resume.pdf")
        print("✅ Successfully loaded resume.")
    except FileNotFoundError:
        print("❌ Error: Dhiraj_Sahu_Resume.pdf not found.")
        return

    # Resume parser agent
    resume_parser_agent = Agent(
        role='Resume Parser',
        goal='Extract all key information from a resume with 100% accuracy',
        backstory='''You are an expert NLP specialist trusted by Fortune 500 companies to parse resume text into structured data. 
        You have a perfect track record of identifying names, contact details, skills, education history, and work experience from any resume format.
        Your strength is contextual understanding – you know how to identify skills even when not explicitly labeled as such, and recognize the true meaning of various resume sections.''',
        tools=[],
        llm=llm,
        verbose=True
    )

    # JD parser agent
    jd_parser_agent = Agent(
        role='JD Analyzer',
        goal='Extract every critical element from a job description with perfect precision',
        backstory='''You are an elite recruiter who has analyzed over 10,000 job descriptions for top companies.
        You have unmatched ability to identify explicit and implicit requirements, technical skills, soft skills, and company values.
        Your analysis is so precise that you can determine exactly what the hiring manager is looking for, even reading between the lines.
        You specialize in understanding industry-specific jargon and translating requirements into clear, actionable data points.''',
        tools=[],
        llm=llm,
        verbose=True
    )

    # ATS scorer agent
    ats_scorer_agent = Agent(
        role='ATS Matcher',
        goal='Calculate precise ATS matching scores with the exact algorithms used by industry-leading ATS systems',
        backstory='''You are a former lead engineer who built ATS systems for multiple Fortune 100 companies.
        You intimately understand how modern ATS algorithms parse, score, and rank resumes against job descriptions.
        You can identify exactly which keywords matter most, how keyword proximity impacts scores, and how semantic matching is evaluated.
        Your recommendations consistently help candidates achieve 85%+ match rates and interview callbacks.''',
        tools=[],
        llm=llm,
        verbose=True
    )

    # Resume optimizer agent
    resume_optimizer_agent = Agent(
        role='Resume Enhancement Specialist',
        goal='Transform any resume to achieve maximum ATS match while maintaining absolute truthfulness',
        backstory='''You are a professional resume writer with 15+ years of experience helping candidates land roles at top companies.
        You've studied every ATS system on the market and know exactly how to optimize content while maintaining authenticity.
        Your specialty is strategic keyword placement, achievement quantification, and context-appropriate industry terminology.
        You never fabricate experience but excel at presenting genuine qualifications in the most favorable light possible.''',
        tools=[],
        llm=llm,
        verbose=True
    )

    # Define tasks
    task_1 = Task(
        description=f"""
        Parse the following resume with extreme attention to detail, ensuring you extract EVERY piece of relevant information.
        
        1. Identify the candidate's full name, email address, and phone number
        2. Extract ALL skills mentioned, including those embedded within experience descriptions
        3. Capture complete education history with degrees, institutions, dates, and relevant honors
        4. Extract ALL work experience with exact company names, precise dates, detailed roles, and comprehensive responsibilities
        5. Look for achievements with metrics and quantifiable results
        
        Format your output as a clean, valid JSON object with these fields:
        - name: Full name of the candidate
        - email: Email address
        - phone: Phone number
        - skills: Array of ALL skills found (minimum 15 skills expected)
        - education: Array of education entries with complete details
        - experience: Array of objects containing {{
            "company": company name,
            "year": employment period,
            "role": job title,
            "responsibilities": detailed description of duties and achievements
        }}
        
        Resume text:
        {resume_text}
        """,
        expected_output='Complete and highly detailed JSON representation of the resume with no missing information',
        agent=resume_parser_agent
    )

    task_2 = Task(
        description=f"""
        Perform a comprehensive analysis of this job description. Your goal is to extract EVERY detail that would be relevant for matching a candidate.
        
        Extract the following with extremely high precision:
        1. Job title - exact title as stated in the description
        2. Required technical skills - ALL technical abilities, tools, languages, frameworks mentioned
        3. Required soft skills - ALL interpersonal abilities, communication skills, work style preferences
        4. Primary responsibilities - EVERY duty and expected function listed
        5. Educational requirements - degrees, certifications, or specific knowledge domains
        6. Experience level - years of experience or seniority indicators
        7. Company values - cultural aspects emphasized in the description
        
        Format your output as a clean, valid JSON object with these fields:
        - job_title: exact job title
        - company: company name if mentioned
        - skills: array of ALL required skills (technical and soft)
        - responsibilities: array of ALL job duties
        - requirements: array of ALL qualifications including education and experience
        - values: array of company values or cultural aspects
        
        Job description:
        {job_description}
        """,
        expected_output='Comprehensive and highly detailed JSON analysis of the job description with no missing information',
        agent=jd_parser_agent
    )

    task_3 = Task(
        description="""
        Perform a detailed ATS match analysis between the resume and job description using the exact methods employed by modern Applicant Tracking Systems.
        
        Your analysis must include:
        
        1. EXACT MATCH KEYWORDS: Direct one-to-one matches between resume and job description
        2. SEMANTIC MATCH KEYWORDS: Terms that are functionally equivalent but not identical
        3. MISSING CRITICAL KEYWORDS: Required skills/qualifications completely absent from the resume
        4. EXPERIENCE ALIGNMENT: How well the candidate's background matches required responsibilities
        5. EDUCATION ALIGNMENT: How the candidate's education meets stated requirements
        6. SECTION-BY-SECTION SCORE: Individual scores for skills, experience, and education sections
        
        Calculate an OVERALL ATS SCORE using this weighted formula:
        - Skills match: 40% of total score
        - Experience relevance: 35% of total score
        - Education match: 15% of total score
        - Keyword density: 10% of total score
        
        Output a detailed JSON object with:
        - ats_score: Overall percentage score (0-100)
        - section_scores: Individual scores for skills, experience, education
        - exact_matches: Array of directly matching keywords
        - semantic_matches: Array of semantically equivalent terms
        - missing_keywords: Array of critical missing terms with PRIORITY rankings (high/medium/low)
        - improvement_suggestions: Array of specific, actionable recommendations
        
        Use the resume and job description from previous tasks.
        """,
        expected_output='Detailed ATS match analysis with precise scores, keyword matches, and prioritized improvement recommendations',
        agent=ats_scorer_agent
    )

    task_4 = Task(
        description="""
        Optimize the resume to achieve a 90%+ ATS match score while maintaining complete truthfulness and authenticity.
        
        Follow these specific optimization steps:
        
        1. STRATEGIC KEYWORD INTEGRATION: Incorporate ALL high-priority missing keywords from the ATS report naturally into appropriate sections
        2. EXPERIENCE ENHANCEMENT: Rewrite experience bullet points to align directly with job responsibilities
        3. QUANTIFICATION: Add metrics and achievement data where possible
        4. SKILLS PRIORITIZATION: Reorder skills to place job-relevant ones first
        5. REDUNDANCY ELIMINATION: Remove duplicate or irrelevant information
        6. SEMANTIC OPTIMIZATION: Replace weak terms with stronger, ATS-friendly alternatives
        
        The output must be a COMPLETE, VALID JSON object with the exact same structure as the original resume JSON:
        {
            "name": candidate name,
            "email": email address,
            "phone": phone number,
            "skills": array of skills (prioritized by relevance),
            "education": array of education entries,
            "experience": array of objects with {
                "company": company name,
                "year": employment period,
                "role": job title,
                "responsibilities": enhanced descriptions aligned with job requirements
            }
        }
        There should be all the previous resuume information, but with enhanced, ATS-friendly content. The format for the previous resume must be maintained.
        Any skills or experiences added must be 100% justified by the original resume content - NO FABRICATION allowed.
        """,
        expected_output='Optimized resume JSON with strategically enhanced content for maximum ATS compatibility along with proper format and structure like the original resume',
        agent=resume_optimizer_agent
    )

    # Create crew and run
    crew = Crew(
        agents=[
            resume_parser_agent,
            jd_parser_agent,
            ats_scorer_agent,
            resume_optimizer_agent
        ],
        tasks=[task_1, task_2, task_3, task_4],
        llm=llm,
        verbose=True
    )

    try:
        print("\n🚀 Starting resume optimization process...")
        results = crew.kickoff()
        
        # Get the task outputs
        resume_parser_output = results.tasks_output[0]
        jd_parser_output = results.tasks_output[1]
        ats_scorer_output = results.tasks_output[2]
        resume_optimizer_output = results.tasks_output[3]

        print("\n=== Processing Task Outputs ===")
        
        # Extract optimized resume JSON
        try:
            if isinstance(resume_optimizer_output, str):
                json_match = re.search(r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}', resume_optimizer_output, re.DOTALL)
                if json_match:
                    optimized_resume_json = json.loads(json_match.group(0))
                else:
                    optimized_resume_json = json.loads(resume_optimizer_output)
            elif hasattr(resume_optimizer_output, 'raw'):
                raw_data = resume_optimizer_output.raw
                if isinstance(raw_data, str):
                    json_match = re.search(r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}', raw_data, re.DOTALL)
                    if json_match:
                        optimized_resume_json = json.loads(json_match.group(0))
                    else:
                        optimized_resume_json = json.loads(raw_data)
                else:
                    optimized_resume_json = raw_data
            else:
                optimized_resume_json = resume_optimizer_output
                
            print("✅ Successfully extracted optimized resume JSON")
            
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"⚠️ Error parsing optimized resume JSON: {e}")
            # Fallback to creating a basic resume structure
            optimized_resume_json = {
                "name": "Candidate",
                "email": "example@email.com",
                "phone": "123-456-7890",
                "skills": ["Python", "JavaScript", "Problem Solving", "Communication"],
                "education": ["Bachelor's Degree in Computer Science"],
                "experience": [{
                    "company": "Tech Company",
                    "year": "2020-2023",
                    "role": "Software Developer",
                    "responsibilities": "Developed software applications using modern technologies."
                }]
            }
            print("⚠️ Using fallback resume JSON structure")

        # Create output directory
        os.makedirs("output", exist_ok=True)

        # Generate PDFs using ReportLab
        print("\n=== Generating PDFs ===")
        
        try:
            resume_pdf_path = os.path.join("output", "Resume.pdf")
            if create_resume_pdf(optimized_resume_json, resume_pdf_path):
                print(f"✅ Successfully created Resume.pdf")
            else:
                print(f"⚠️ Failed to create Resume.pdf")
        except Exception as e:
            print(f"⚠️ Error creating resume PDF: {e}")

        try:
            cover_letter_pdf_path = os.path.join("output", "Cover_Letter.pdf")
            if create_cover_letter_pdf(optimized_resume_json, job_description, cover_letter_pdf_path):
                print(f"✅ Successfully created Cover_Letter.pdf")
            else:
                print(f"⚠️ Failed to create Cover_Letter.pdf")
        except Exception as e:
            print(f"⚠️ Error creating cover letter PDF: {e}")

        # Save ATS report as JSON
        try:
            if isinstance(ats_scorer_output, str):
                json_match = re.search(r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}', ats_scorer_output, re.DOTALL)
                if json_match:
                    ats_report = json.loads(json_match.group(0))
                    ats_report_file = os.path.join("output", "ATS_Report.json")
                    with open(ats_report_file, "w") as f:
                        json.dump(ats_report, f, indent=2)
                    print(f"✅ Saved ATS report: {ats_report_file}")
            elif hasattr(ats_scorer_output, 'raw'):
                raw_data = ats_scorer_output.raw
                if isinstance(raw_data, str):
                    json_match = re.search(r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}', raw_data, re.DOTALL)
                    if json_match:
                        ats_report = json.loads(json_match.group(0))
                        ats_report_file = os.path.join("output", "ATS_Report.json")
                        with open(ats_report_file, "w") as f:
                            json.dump(ats_report, f, indent=2)
                        print(f"✅ Saved ATS report: {ats_report_file}")
        except Exception as e:
            print(f"⚠️ Could not save ATS report: {e}")

        # Save optimized resume JSON for reference
        try:
            resume_json_file = os.path.join("output", "Optimized_Resume.json")
            with open(resume_json_file, "w") as f:
                json.dump(optimized_resume_json, f, indent=2)
            print(f"✅ Saved optimized resume JSON: {resume_json_file}")
        except Exception as e:
            print(f"⚠️ Could not save resume JSON: {e}")

        print("\n🎉 Process complete! Check the output directory for your files.")
        print("📁 Generated files:")
        print("   • Resume.pdf - Optimized resume")
        print("   • Cover_Letter.pdf - Customized cover letter")
        print("   • ATS_Report.json - Detailed ATS analysis")
        print("   • Optimized_Resume.json - Resume data in JSON format")

    except Exception as e:
        print(f"❌ Error during crew execution: {e}")
        import traceback
        traceback.print_exc()

# Example usage
if __name__ == '__main__':
    job_description = """
    This is an exciting opportunity for a programmer / engineer with existing experience to build an AI based system for a financial services company. We are looking to bring our compliance and administrative services into the modern era with AI based technology to help us complete tasks such as recommendation letter writing, document formatting, file / error checking and document naming.

The role can be remote or hybrid depending.

Job Types: Full-time, Part-time

Pay: £48,045.00-£53,372.00 per year

Expected hours: 10 – 40 per week

Schedule:

Flexitime
Work Location: Remote

Reference ID: AI based software developer / engineer required
    """
    run_resume_optimizer(job_description)