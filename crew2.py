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

def extract_latex_resume_content(file_path: str) -> str:
    """Extract and parse content from LaTeX resume file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            latex_content = file.read()
        print("✅ Successfully loaded LaTeX resume from resume.txt")
        return latex_content
    except FileNotFoundError:
        print("❌ Error: resume.txt not found.")
        return ""
    except Exception as e:
        print(f"❌ Error reading resume.txt: {e}")
        return ""

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
    """Create a professional resume PDF using ReportLab with enhanced formatting."""
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
    
    # Custom styles matching the original resume aesthetic
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=12,
        alignment=TA_CENTER,
        textColor=HexColor('#2C3E50'),
        fontName='Helvetica-Bold'
    )
    
    contact_style = ParagraphStyle(
        'Contact',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=HexColor('#333333')
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=16,
        textColor=HexColor('#2C3E50'),
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=HexColor('#2C3E50'),
        borderPadding=4
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        leftIndent=0,
        alignment=TA_LEFT
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        leftIndent=20,
        bulletIndent=10
    )
    
    experience_header_style = ParagraphStyle(
        'ExperienceHeader',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=4,
        fontName='Helvetica-Bold',
        textColor=HexColor('#2C3E50')
    )
    
    # Build the document
    story = []
    
    # Name
    name = resume_json.get('name', 'Dhiraj Sahu')
    story.append(Paragraph(name, title_style))
    
    # Contact information (enhanced format)
    email = resume_json.get('email', 'dhirajksahu01@gmail.com')
    phone = resume_json.get('phone', '9324211798')
    location = resume_json.get('location', 'Mumbai, Maharashtra')
    portfolio = resume_json.get('portfolio', 'dhirajsahuportfolio.com')
    linkedin = resume_json.get('linkedin', 'Dhiraj Sahu')
    github = resume_json.get('github', 'DhirajSahu18')
    
    contact_info = f"""📍 {location} | ✉ {email} | ☎ {phone}<br/>
🌐 {portfolio} | 💼 LinkedIn: {linkedin} | 👨‍💻 GitHub: {github}"""
    story.append(Paragraph(contact_info, contact_style))
    
    # About Me section
    about_me = resume_json.get('about_me', '')
    if about_me:
        story.append(Paragraph("ABOUT ME", section_header_style))
        story.append(Paragraph(about_me, body_style))
        story.append(Spacer(1, 12))
    
    # Skills section (enhanced categorization)
    skills = resume_json.get('skills', {})
    if skills:
        story.append(Paragraph("TECHNICAL SKILLS", section_header_style))
        
        # Handle both dict and list formats
        if isinstance(skills, dict):
            for category, skill_list in skills.items():
                if isinstance(skill_list, list):
                    skills_text = ", ".join(skill_list)
                else:
                    skills_text = skill_list
                story.append(Paragraph(f"<b>{category}:</b> {skills_text}", body_style))
        elif isinstance(skills, list):
            skills_text = " • ".join(skills)
            story.append(Paragraph(skills_text, body_style))
        
        story.append(Spacer(1, 12))
    
    # Experience section (enhanced format)
    experience = resume_json.get('experience', [])
    if experience:
        story.append(Paragraph("PROFESSIONAL EXPERIENCE", section_header_style))
        for exp in experience:
            # Job title, company, and duration
            role = exp.get('role', 'Role')
            company = exp.get('company', 'Company')
            duration = exp.get('duration', exp.get('year', 'Duration'))
            location_exp = exp.get('location', '')
            
            exp_header = f"<b>{role}</b> | {company}"
            if location_exp:
                exp_header += f" | {location_exp}"
            exp_header += f" | <i>{duration}</i>"
            
            story.append(Paragraph(exp_header, experience_header_style))
            
            # Responsibilities
            responsibilities = exp.get('responsibilities', [])
            if isinstance(responsibilities, str):
                # Split string into bullet points
                resp_items = re.split(r'[;.]\s*(?=[A-Z])', responsibilities)
                resp_items = [r.strip() for r in resp_items if r.strip()]
            else:
                resp_items = responsibilities
            
            for resp in resp_items:
                if resp and not resp.endswith('.'):
                    resp += '.'
                story.append(Paragraph(f"• {resp}", bullet_style))
            
            story.append(Spacer(1, 8))
    
    # Education section
    education = resume_json.get('education', [])
    if education:
        story.append(Paragraph("EDUCATION", section_header_style))
        for edu in education:
            if isinstance(edu, dict):
                degree = edu.get('degree', '')
                institution = edu.get('institution', '')
                year = edu.get('year', '')
                gpa = edu.get('gpa', '')
                
                edu_text = f"<b>{degree}</b> | {institution}"
                if year:
                    edu_text += f" | {year}"
                if gpa:
                    edu_text += f" | {gpa}"
                
                story.append(Paragraph(edu_text, body_style))
                
                # Additional details
                coursework = edu.get('coursework', '')
                if coursework:
                    story.append(Paragraph(f"<b>Coursework:</b> {coursework}", bullet_style))
            else:
                story.append(Paragraph(f"• {edu}", bullet_style))
        
        story.append(Spacer(1, 12))
    
    # Projects section
    projects = resume_json.get('projects', [])
    if projects:
        story.append(Paragraph("PROJECTS", section_header_style))
        for project in projects:
            if isinstance(project, dict):
                title = project.get('title', 'Project')
                description = project.get('description', '')
                technologies = project.get('technologies', '')
                links = project.get('links', {})
                
                project_header = f"<b>{title}</b>"
                if links:
                    link_text = " | ".join([f"{k}: {v}" for k, v in links.items()])
                    project_header += f" | {link_text}"
                
                story.append(Paragraph(project_header, experience_header_style))
                
                if description:
                    if isinstance(description, list):
                        for desc in description:
                            story.append(Paragraph(f"• {desc}", bullet_style))
                    else:
                        story.append(Paragraph(description, body_style))
                
                if technologies:
                    story.append(Paragraph(f"<b>Technologies:</b> {technologies}", bullet_style))
            else:
                story.append(Paragraph(f"• {project}", bullet_style))
        
        story.append(Spacer(1, 12))
    
    # Publications section
    publications = resume_json.get('publications', [])
    if publications:
        story.append(Paragraph("PUBLICATIONS", section_header_style))
        for pub in publications:
            if isinstance(pub, dict):
                title = pub.get('title', '')
                authors = pub.get('authors', '')
                date = pub.get('date', '')
                link = pub.get('link', '')
                
                pub_text = f"<b>{title}</b>"
                if authors:
                    pub_text += f" | {authors}"
                if date:
                    pub_text += f" | {date}"
                if link:
                    pub_text += f" | {link}"
                
                story.append(Paragraph(pub_text, body_style))
            else:
                story.append(Paragraph(f"• {pub}", bullet_style))
    
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
    name = resume_json.get('name', 'Dhiraj Sahu')
    email = resume_json.get('email', 'dhirajksahu01@gmail.com')
    phone = resume_json.get('phone', '9324211798')
    location = resume_json.get('location', 'Mumbai, Maharashtra')
    
    header_text = f"""<b>{name}</b><br/>
{email}<br/>
{phone}<br/>
{location}"""
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
    
    # Body paragraphs - more personalized based on actual resume content
    about_me = resume_json.get('about_me', '')
    opening_para = f"I am writing to express my strong interest in the position at {company_name}. {about_me[:100]}... With my comprehensive background in software development and proven track record of delivering innovative solutions, I am confident that I would be a valuable addition to your team."
    story.append(Paragraph(opening_para, body_style))
    
    # Skills alignment paragraph
    skills = resume_json.get('skills', {})
    if skills:
        # Extract key skills from the structured format
        key_skills = []
        if isinstance(skills, dict):
            for category, skill_list in skills.items():
                if isinstance(skill_list, list):
                    key_skills.extend(skill_list[:3])  # Top 3 from each category
                elif isinstance(skill_list, str):
                    key_skills.extend(skill_list.split(',')[:3])
        elif isinstance(skills, list):
            key_skills = skills[:8]
        
        key_skills_text = ', '.join(key_skills[:8])  # Top 8 skills
        skills_para = f"My technical expertise includes {key_skills_text}, which directly aligns with the requirements outlined in your job posting. I have successfully applied these skills in various projects and collaborative environments, consistently delivering high-quality results that exceed expectations."
        story.append(Paragraph(skills_para, body_style))
    
    # Experience paragraph
    experience = resume_json.get('experience', [])
    if experience:
        recent_exp = experience[0] if experience else {}
        role = recent_exp.get('role', 'a developer')
        company_exp = recent_exp.get('company', 'my previous role')
        exp_para = f"In my recent role as {role} at {company_exp}, I have demonstrated my ability to work effectively in team environments while managing complex technical challenges. My experience has prepared me well for the responsibilities and opportunities that this position offers."
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
    
    # Load resume from LaTeX file
    latex_resume_content = extract_latex_resume_content("resume.txt")
    if not latex_resume_content:
        print("❌ Could not load resume content. Exiting.")
        return

    # Enhanced Resume parser agent with LaTeX understanding
    resume_parser_agent = Agent(
        role='LaTeX Resume Parser & Content Extractor',
        goal='Extract and structure ALL information from LaTeX resume with 100% fidelity to original content',
        backstory='''You are an expert LaTeX document parser and NLP specialist with extensive experience in academic and professional document processing. 
        You have a perfect understanding of LaTeX syntax, commands, and document structure. Your specialty is extracting comprehensive information from LaTeX resumes while preserving all original content, formatting context, and hierarchical relationships.
        You excel at identifying personal information, technical skills categorization, work experience with detailed descriptions, educational background, projects with technologies used, and publications.
        Your parsing maintains the exact content and context from the original document without any loss or modification.''',
        tools=[],
        llm=llm,
        verbose=True
    )

    # Enhanced JD parser agent
    jd_parser_agent = Agent(
        role='Advanced JD Analyzer & Requirements Extractor',
        goal='Extract every critical element from job descriptions with AI-powered insight recognition',
        backstory='''You are an elite recruiter and AI specialist who has analyzed over 15,000 job descriptions across various industries.
        You have unmatched ability to identify explicit requirements, implicit expectations, technical skills, soft skills, company culture indicators, and growth opportunities.
        Your analysis goes beyond surface-level requirements to understand the underlying business needs, team dynamics, and success factors.
        You specialize in identifying keyword patterns that ATS systems prioritize and understanding industry-specific terminology and trends.''',
        tools=[],
        llm=llm,
        verbose=True
    )

    # Enhanced ATS scorer agent
    ats_scorer_agent = Agent(
        role='Advanced ATS Matching & Scoring Specialist',
        goal='Perform comprehensive ATS analysis using cutting-edge algorithms and industry best practices',
        backstory='''You are a former principal engineer who designed and optimized ATS systems for Fortune 50 companies and major recruiting platforms.
        You have deep knowledge of modern ATS algorithms, including semantic matching, keyword weighting, contextual analysis, and machine learning-based scoring.
        You understand how different ATS systems (Workday, Greenhouse, Lever, etc.) parse and rank resumes, and you can predict scoring patterns with 95% accuracy.
        Your expertise includes identifying critical optimization opportunities while maintaining content authenticity and professional standards.''',
        tools=[],
        llm=llm,
        verbose=True
    )

    # Enhanced Resume optimizer agent
    resume_optimizer_agent = Agent(
        role='Strategic Resume Enhancement & ATS Optimization Specialist',
        goal='Transform resumes for maximum ATS compatibility while preserving authenticity and enhancing professional presentation',
        backstory='''You are a master resume strategist with 20+ years of experience helping professionals at all levels land roles at top companies including FAANG, consulting firms, and Fortune 100 corporations.
        You have an exceptional understanding of ATS optimization, keyword strategy, achievement quantification, and professional presentation.
        Your approach combines deep technical knowledge of ATS systems with psychological understanding of hiring managers and recruiters.
        You excel at strategic content enhancement, maintaining truthfulness while maximizing impact, and adapting content for specific roles and industries.
        You never fabricate experience but masterfully present genuine qualifications in the most compelling and ATS-friendly manner possible.''',
        tools=[],
        llm=llm,
        verbose=True
    )

    # Define enhanced tasks
    task_1 = Task(
        description=f"""
        Parse this LaTeX resume document with extreme precision and comprehensive extraction. Maintain ALL original content while structuring it for optimization.
        
        CRITICAL REQUIREMENTS:
        1. Extract the candidate's complete personal information (name, email, phone, location, portfolio, LinkedIn, GitHub)
        2. Preserve the "About Me" section exactly as written
        3. Extract ALL technical skills with their original categorization (Languages, Front-End, Back-End, Databases, DevOps, ML, Tools, Other Skills)
        4. Capture complete work experience with exact company names, locations, dates, roles, and ALL responsibility bullet points
        5. Extract full educational background with institutions, degrees, dates, GPAs, and coursework details
        6. Capture ALL projects with titles, descriptions, technologies, and links
        7. Extract publications with complete citation information
        8. Maintain the hierarchical structure and relationships between sections
        
        OUTPUT FORMAT: Clean, valid JSON with this exact structure:
        {{
            "name": "Full name",
            "email": "Email address", 
            "phone": "Phone number",
            "location": "Location",
            "portfolio": "Portfolio URL",
            "linkedin": "LinkedIn profile",
            "github": "GitHub profile",
            "about_me": "Complete about me text",
            "skills": {{
                "Languages": ["list of languages"],
                "Front-End": ["list of frontend skills"],
                "Back-End": ["list of backend skills"],
                "Databases": ["list of database skills"],
                "DevOps / Deployment": ["list of devops skills"],
                "Machine Learning": ["list of ML skills"],
                "Tools & Platforms": ["list of tools"],
                "Other Skills": ["list of other skills"]
            }},
            "experience": [
                {{
                    "role": "Job title",
                    "company": "Company name", 
                    "location": "Location",
                    "duration": "Time period",
                    "responsibilities": ["List of all bullet points"]
                }}
            ],
            "education": [
                {{
                    "degree": "Degree type and field",
                    "institution": "Institution name",
                    "year": "Time period", 
                    "gpa": "GPA if available",
                    "coursework": "Coursework if available"
                }}
            ],
            "projects": [
                {{
                    "title": "Project name",
                    "description": ["List of bullet points"],
                    "technologies": "Technologies used",
                    "links": {{"GitHub": "link", "Deployment": "link"}}
                }}
            ],
            "publications": [
                {{
                    "title": "Publication title",
                    "authors": "Authors",
                    "date": "Publication date",
                    "link": "Link if available"
                }}
            ]
        }}
        
        LaTeX Resume Content:
        {latex_resume_content}
        """,
        expected_output='Complete and highly detailed JSON representation of the LaTeX resume with no missing information and preserved original content',
        agent=resume_parser_agent
    )

    task_2 = Task(
        description=f"""
        Perform an exhaustive analysis of this job description to extract every detail relevant for optimal resume matching.
        
        ANALYSIS REQUIREMENTS:
        1. Job title and role level identification
        2. Company name and industry context
        3. All required technical skills (programming languages, frameworks, tools, platforms)
        4. All required soft skills (communication, leadership, teamwork, etc.)
        5. Specific responsibilities and daily tasks
        6. Educational requirements and preferred qualifications
        7. Experience level expectations (years, seniority)
        8. Company culture and values indicators
        9. Keywords and phrases that would be prioritized by ATS systems
        10. Industry-specific terminology and jargon
        
        OUTPUT FORMAT: Comprehensive JSON structure:
        {{
            "job_title": "Exact job title",
            "company": "Company name",
            "industry": "Industry sector",
            "role_level": "Seniority level",
            "required_skills": {{
                "technical": ["All technical requirements"],
                "soft": ["All soft skill requirements"],
                "tools": ["Specific tools and platforms"]
            }},
            "responsibilities": ["All job duties and expectations"],
            "requirements": {{
                "education": ["Educational requirements"],
                "experience": ["Experience requirements"],
                "certifications": ["Any certifications mentioned"]
            }},
            "company_values": ["Cultural aspects and values"],
            "keywords": ["High-priority ATS keywords"],
            "nice_to_have": ["Preferred but not required qualifications"]
        }}
        
        Job Description:
        {job_description}
        """,
        expected_output='Comprehensive and detailed JSON analysis of the job description with complete requirement extraction',
        agent=jd_parser_agent
    )

    task_3 = Task(
        description="""
        Conduct a comprehensive ATS compatibility analysis using advanced matching algorithms and industry best practices.
        
        ANALYSIS METHODOLOGY:
        1. KEYWORD MATCHING ANALYSIS:
           - Direct exact matches between resume and job description
           - Semantic matches (synonyms, related terms, industry equivalents)
           - Contextual matches (skills used in relevant contexts)
           - Missing critical keywords with impact assessment
        
        2. SECTION-SPECIFIC SCORING:
           - Technical skills alignment (40% weight)
           - Experience relevance and impact (35% weight) 
           - Education and certification match (15% weight)
           - Keyword density and distribution (10% weight)
        
        3. ADVANCED METRICS:
           - Content overlap percentage
           - Keyword frequency optimization
           - Professional presentation score
           - Industry terminology usage
           - Achievement quantification level
        
        4. OPTIMIZATION OPPORTUNITIES:
           - High-impact missing keywords (critical for ATS ranking)
           - Medium-impact enhancements (moderate improvement potential)
           - Low-impact additions (minor optimization opportunities)
           - Content restructuring recommendations
           - Achievement enhancement suggestions
        
        OUTPUT FORMAT: Detailed analysis JSON:
        {{
            "overall_ats_score": "Percentage score (0-100)",
            "section_scores": {{
                "technical_skills": "Score with breakdown",
                "experience_relevance": "Score with analysis", 
                "education_match": "Score with details",
                "keyword_optimization": "Score with assessment"
            }},
            "keyword_analysis": {{
                "exact_matches": ["Direct keyword matches"],
                "semantic_matches": ["Related/synonym matches"],
                "missing_critical": ["High-priority missing terms"],
                "missing_moderate": ["Medium-priority missing terms"],
                "missing_minor": ["Low-priority missing terms"]  
            }},
            "content_analysis": {{
                "strengths": ["Current resume strengths"],
                "gaps": ["Areas needing improvement"],
                "opportunities": ["Enhancement opportunities"]
            }},
            "optimization_recommendations": {{
                "high_priority": ["Critical changes for maximum impact"],
                "medium_priority": ["Important improvements"], 
                "low_priority": ["Minor enhancements"],
                "content_strategy": ["Overall content improvement strategy"]
            }}
        }}
        
        Use the comprehensive resume and job description data from previous tasks for this analysis.
        """,
        expected_output='Advanced ATS compatibility analysis with detailed scoring, keyword analysis, and strategic optimization recommendations',
        agent=ats_scorer_agent
    )

    task_4 = Task(
        description="""
        Strategically optimize the resume for maximum ATS compatibility and professional impact while maintaining complete authenticity.
        
        OPTIMIZATION STRATEGY:
        1. CONTENT PRESERVATION: Maintain ALL original information, experiences, and achievements
        2. STRATEGIC KEYWORD INTEGRATION: Naturally incorporate high-priority missing keywords into appropriate sections
        3. ACHIEVEMENT ENHANCEMENT: Strengthen bullet points with quantifiable results and impact metrics
        4. TECHNICAL SKILLS OPTIMIZATION: Prioritize and reorganize skills based on job relevance
        5. EXPERIENCE ALIGNMENT: Reframe responsibilities to align with job requirements while staying truthful
        6. CONTENT STRUCTURE: Optimize section organization and information hierarchy
        7. PROFESSIONAL PRESENTATION: Enhance language for maximum impact and ATS compatibility
        
        CRITICAL REQUIREMENTS:
        - Preserve ALL original content and experiences
        - No fabrication or false information
        - Maintain professional authenticity
        - Optimize for target ATS score of 90%+
        - Keep the exact same JSON structure as the original parsed resume
        - Enhance content strategically without changing core facts
        
        OUTPUT: Complete optimized resume JSON with identical structure to original:
        {{
            "name": "Dhiraj Sahu",
            "email": "dhirajksahu01@gmail.com",
            "phone": "9324211798", 
            "location": "Mumbai, Maharashtra",
            "portfolio": "dhirajsahuportfolio.com",
            "linkedin": "Dhiraj Sahu",
            "github": "DhirajSahu18",
            "about_me": "Enhanced professional summary with strategic keyword integration",
            "skills": {{
                "Languages": ["Optimized list prioritizing job-relevant languages"],
                "Front-End": ["Enhanced frontend skills with job-relevant emphasis"],
                "Back-End": ["Optimized backend skills"],
                "Databases": ["Enhanced database skills"],
                "DevOps / Deployment": ["Optimized DevOps skills"],
                "Machine Learning": ["Enhanced ML skills"],
                "Tools & Platforms": ["Optimized tools list"],
                "Other Skills": ["Enhanced other skills"]
            }},
            "experience": [
                {{
                    "role": "Original role title",
                    "company": "Original company",
                    "location": "Original location", 
                    "duration": "Original duration",
                    "responsibilities": ["Enhanced bullet points with strategic keywords and quantifiable achievements"]
                }}
            ],
            "education": ["Enhanced education section with original information"],
            "projects": ["Enhanced projects with strategic optimization"],
            "publications": ["Original publications information"]
        }}
        
        The optimization must result in significantly improved ATS compatibility while maintaining complete truthfulness and professional authenticity.
        Use the original resume data and ATS analysis from previous tasks.
        """,
        expected_output='Strategically optimized resume JSON with enhanced ATS compatibility, preserved authenticity, and maximum professional impact',
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
        print("\n🚀 Starting enhanced resume optimization process...")
        print("📄 Processing LaTeX resume from resume.txt...")
        results = crew.kickoff()
        
        # Get the task outputs
        resume_parser_output = results.tasks_output[0]
        jd_parser_output = results.tasks_output[1]
        ats_scorer_output = results.tasks_output[2]
        resume_optimizer_output = results.tasks_output[3]

        print("\n=== Processing Task Outputs ===")
        
        # Extract optimized resume JSON with better error handling
        try:
            if isinstance(resume_optimizer_output.raw, str):
                # Try to extract JSON from the raw output
                optimized_resume_text = resume_optimizer_output.raw
                
                # Look for JSON content between triple backticks or curly braces
                json_match = re.search(r'```json\s*(\{.*\})\s*```', optimized_resume_text, re.DOTALL)
                if not json_match:
                    json_match = re.search(r'(\{.*\})', optimized_resume_text, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(1)
                    optimized_resume_json = json.loads(json_str)
                else:
                    # Fallback: try to parse the entire output as JSON
                    optimized_resume_json = json.loads(optimized_resume_text)
            else:
                optimized_resume_json = resume_optimizer_output.raw
                
            print("✅ Successfully extracted optimized resume JSON")
            
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"❌ Error parsing optimized resume JSON: {e}")
            print("🔄 Using fallback: original parsed resume")
            
            # Fallback to original parsed resume
            try:
                if isinstance(resume_parser_output.raw, str):
                    original_json_match = re.search(r'```json\s*(\{.*\})\s*```', resume_parser_output.raw, re.DOTALL)
                    if not original_json_match:
                        original_json_match = re.search(r'(\{.*\})', resume_parser_output.raw, re.DOTALL)
                    
                    if original_json_match:
                        optimized_resume_json = json.loads(original_json_match.group(1))
                    else:
                        optimized_resume_json = json.loads(resume_parser_output.raw)
                else:
                    optimized_resume_json = resume_parser_output.raw
            except Exception as fallback_e:
                print(f"❌ Fallback also failed: {fallback_e}")
                return

        # Extract company name for file naming
        company_name = extract_company_name(job_description)
        
        # Generate file names with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        resume_filename = f"optimized_resume_{company_name}_{timestamp}.pdf"
        cover_letter_filename = f"cover_letter_{company_name}_{timestamp}.pdf"
        json_filename = f"optimized_resume_{company_name}_{timestamp}.json"
        analysis_filename = f"ats_analysis_{company_name}_{timestamp}.txt"
        
        # Save optimized resume JSON
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(optimized_resume_json, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved optimized resume JSON: {json_filename}")
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")

        # Generate resume PDF
        try:
            print(f"📄 Generating optimized resume PDF: {resume_filename}")
            if create_resume_pdf(optimized_resume_json, resume_filename):
                print(f"✅ Successfully created resume PDF: {resume_filename}")
            else:
                print("❌ Failed to create resume PDF")
        except Exception as e:
            print(f"❌ Error creating resume PDF: {e}")

        # Generate cover letter PDF
        try:
            print(f"📄 Generating cover letter PDF: {cover_letter_filename}")
            if create_cover_letter_pdf(optimized_resume_json, job_description, cover_letter_filename):
                print(f"✅ Successfully created cover letter PDF: {cover_letter_filename}")
            else:
                print("❌ Failed to create cover letter PDF")
        except Exception as e:
            print(f"❌ Error creating cover letter PDF: {e}")

        # Save ATS analysis
        try:
            with open(analysis_filename, 'w', encoding='utf-8') as f:
                f.write("=== ATS COMPATIBILITY ANALYSIS ===\n\n")
                
                # Write job description analysis
                f.write("JOB DESCRIPTION ANALYSIS:\n")
                f.write("-" * 50 + "\n")
                if isinstance(jd_parser_output.raw, str):
                    f.write(jd_parser_output.raw)
                else:
                    f.write(str(jd_parser_output.raw))
                f.write("\n\n")
                
                # Write ATS scoring analysis
                f.write("ATS SCORING ANALYSIS:\n")
                f.write("-" * 50 + "\n")
                if isinstance(ats_scorer_output.raw, str):
                    f.write(ats_scorer_output.raw)
                else:
                    f.write(str(ats_scorer_output.raw))
                f.write("\n\n")
                
                # Write optimization summary
                f.write("OPTIMIZATION SUMMARY:\n")
                f.write("-" * 50 + "\n")
                f.write("The resume has been optimized based on the ATS analysis above.\n")
                f.write("Key improvements include:\n")
                f.write("- Strategic keyword integration\n")
                f.write("- Enhanced skill presentation\n")
                f.write("- Improved achievement quantification\n")
                f.write("- Better alignment with job requirements\n")
                f.write("- Professional formatting optimization\n")
                
            print(f"✅ Saved ATS analysis: {analysis_filename}")
        except Exception as e:
            print(f"❌ Error saving analysis: {e}")

        # Print summary
        print("\n" + "="*60)
        print("🎉 RESUME OPTIMIZATION COMPLETE!")
        print("="*60)
        print(f"📁 Generated Files:")
        print(f"   • Resume PDF: {resume_filename}")
        print(f"   • Cover Letter PDF: {cover_letter_filename}")
        print(f"   • Resume JSON: {json_filename}")
        print(f"   • ATS Analysis: {analysis_filename}")
        print("\n✨ Your resume has been strategically optimized for ATS compatibility!")
        print("💡 Review the analysis file for detailed insights and recommendations.")
        
        # Display key metrics if available
        try:
            if isinstance(ats_scorer_output.raw, str):
                # Try to extract ATS score from the analysis
                score_match = re.search(r'overall_ats_score["\']:\s*["\']?(\d+)', ats_scorer_output.raw)
                if score_match:
                    ats_score = score_match.group(1)
                    print(f"📊 Estimated ATS Score: {ats_score}%")
        except:
            pass
            
        return True

    except Exception as e:
        print(f"\n❌ Error during resume optimization: {str(e)}")
        print("🔍 Please check your resume.txt file and job description.")
        return False

def main():
    """Main function to run the resume optimizer with user input."""
    print("🚀 Welcome to the Advanced Resume Optimizer!")
    print("=" * 50)
    print("This tool will optimize your LaTeX resume for specific job applications.")
    print("📋 Requirements:")
    print("   • resume.txt file containing your LaTeX resume")
    print("   • Job description text")
    print("   • GEMINI_API_KEY in your .env file")
    print("")
    
    # Check if resume file exists
    if not os.path.exists("resume.txt"):
        print("❌ Error: resume.txt not found!")
        print("💡 Please create a resume.txt file with your LaTeX resume content.")
        return
    
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not found in environment variables!")
        print("💡 Please add your Gemini API key to your .env file.")
        return
    
    # Get job description from user
    print("📝 Please paste the job description below:")
    print("   (Press Enter twice when finished)")
    
    job_description_lines = []
    empty_line_count = 0
    
    while True:
        line = input()
        if line == "":
            empty_line_count += 1
            if empty_line_count >= 2:
                break
        else:
            empty_line_count = 0
            job_description_lines.append(line)
    
    job_description = "\n".join(job_description_lines).strip()
    
    if not job_description:
        print("❌ Error: No job description provided!")
        return
    
    print(f"\n📄 Job description received ({len(job_description)} characters)")
    print("🔄 Starting optimization process...")
    
    # Run the optimization
    success = run_resume_optimizer(job_description)
    
    if success:
        print("\n🎯 Optimization completed successfully!")
        print("📧 Your optimized resume and cover letter are ready for submission!")
    else:
        print("\n❌ Optimization failed. Please check the error messages above.")

if __name__ == "__main__":
    main()