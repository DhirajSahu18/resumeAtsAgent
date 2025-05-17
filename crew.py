import os
import re
import json
import subprocess
from crewai import Agent, Task, Crew, LLM
from pdfminer.high_level import extract_text
from dotenv import load_dotenv

load_dotenv()

llm = LLM(
    model="gemini/gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7
)

def extract_company_name(jd_text: str) -> str:
    """Extract company name from job description with improved pattern matching."""
    # Try to match company name patterns like "at Company", "@ Company", "with Company"
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
            # Return the company name (last group in each pattern)
            return groups[-1].strip().replace(" ", "_")
    
    return "Company"  # Default fallback

def resume_json_to_latex(resume_json: dict) -> str:
    """Convert resume JSON to LaTeX format with improved formatting."""
    # Format skills with better spacing
    skills = ', '.join(resume_json.get("skills", []))
    
    # Format education with better structure
    education_items = resume_json.get("education", [])
    education = '\n\\begin{itemize}\n' + \
                '\n'.join([f'\\item {edu}' for edu in education_items]) + \
                '\n\\end{itemize}' if education_items else 'No education information available.'
    
    # Format experience with better structure and formatting
    experience_items = resume_json.get("experience", [])
    if experience_items:
        experience = ''
        for exp in experience_items:
            experience += f"\\subsection*{{{exp.get('role', 'Role')} at {exp.get('company', 'Company')}, {exp.get('year', 'Year')}}}\n"
            experience += "\\begin{itemize}\n"
            # Split responsibilities into bullet points if they contain semicolons or periods
            responsibilities = exp.get('responsibilities', '')
            resp_items = re.split(r'[;.]\s+', responsibilities)
            resp_items = [r.strip() for r in resp_items if r.strip()]
            
            for resp in resp_items:
                if resp and not resp.endswith('.'):
                    resp += '.'
                experience += f"\\item {resp}\n"
            experience += "\\end{itemize}\n"
    else:
        experience = 'No experience information available.'

    return f"""
\\documentclass{{article}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{hyperref}}
\\usepackage{{enumitem}}
\\usepackage{{fontawesome5}}
\\usepackage{{titlesec}}
\\usepackage{{color}}
\\definecolor{{linkcolor}}{{HTML}}{{0066cc}}
\\hypersetup{{colorlinks=true, linkcolor=linkcolor, urlcolor=linkcolor}}

\\titleformat{{\\section}}{{\\Large\\bfseries\\color{{linkcolor}}}}{{}}{{0em}}{{\\underline}}

\\begin{{document}}

\\begin{{center}}
\\textbf{{\\Huge {resume_json.get('name', 'Candidate')}}}

\\vspace{{0.5em}}
\\faEnvelope\\ {resume_json.get('email', 'N/A')} \\quad \\faPhone\\ {resume_json.get('phone', 'N/A')}
\\end{{center}}

\\section*{{Skills}}
{skills}

\\section*{{Education}}
{education}

\\section*{{Experience}}
{experience}

\\end{{document}}
"""

def compile_latex_to_pdf(tex_file_path):
    """Compile LaTeX file to PDF using pdflatex."""
    try:
        # Get the directory containing the tex file
        directory = os.path.dirname(tex_file_path)
        
        # Run pdflatex command (twice to ensure references are resolved)
        subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', tex_file_path],
            cwd=directory,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', tex_file_path],
            cwd=directory,
            check=True,
            capture_output=True
        )
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error compiling {tex_file_path}: {e}")
        print(f"pdflatex output: {e.stdout.decode('utf-8', errors='ignore')}")
        print(f"pdflatex error: {e.stderr.decode('utf-8', errors='ignore')}")
        return False
    except Exception as e:
        print(f"Unexpected error compiling {tex_file_path}: {e}")
        return False

def run_resume_optimizer(job_description: str):
    """Main function to run the resume optimization process with improved agents."""
    try:
        resume_text = extract_text("Dhiraj_Sahu_Resume.pdf")
        print("✅ Successfully loaded resume.")
    except FileNotFoundError:
        print("❌ Error: Dhiraj_Sahu_Resume.pdf not found.")
        return

    # Improved agent with better prompt for resume parsing
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

    # Improved agent with better prompt for job description analysis
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

    # Improved agent with better prompt for ATS scoring
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

    # Improved agent with better prompt for resume optimization
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

    # Improved agent with better prompt for LaTeX resume generation
    resume_latex_agent = Agent(
        role='LaTeX Resume Designer',
        goal='Create visually stunning yet ATS-compatible LaTeX resumes',
        backstory='''You are a document design specialist who combines deep LaTeX expertise with knowledge of ATS parsing algorithms.
        You've created custom resume templates for over 1,000 successful job seekers across all industries.
        You understand exactly which LaTeX elements improve readability while maintaining perfect ATS compatibility.
        Your designs achieve the perfect balance between visual appeal and machine readability.''',
        tools=[],
        llm=llm,
        verbose=True
    )

    # Improved agent with better prompt for cover letter generation
    cover_letter_agent = Agent(
        role='Personalized Cover Letter Writer',
        goal='Craft compelling, customized cover letters that directly address job requirements',
        backstory='''You are an award-winning copywriter who specializes in persuasive professional communications.
        You've helped thousands of professionals secure interviews through perfectly tailored cover letters.
        Your superpower is connecting candidate experiences directly to employer needs with authentic, compelling narratives.
        You know exactly how to balance professionalism, personality, and precision for maximum impact.''',
        tools=[],
        llm=llm,
        verbose=True
    )

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
        description=f"""
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
        description=f"""
        Optimize the resume to achieve a 90%+ ATS match score while maintaining complete truthfulness and authenticity.
        
        Follow these specific optimization steps:
        
        1. STRATEGIC KEYWORD INTEGRATION: Incorporate ALL high-priority missing keywords from the ATS report naturally into appropriate sections
        2. EXPERIENCE ENHANCEMENT: Rewrite experience bullet points to align directly with job responsibilities
        3. QUANTIFICATION: Add metrics and achievement data where possible
        4. SKILLS PRIORITIZATION: Reorder skills to place job-relevant ones first
        5. REDUNDANCY ELIMINATION: Remove duplicate or irrelevant information
        6. SEMANTIC OPTIMIZATION: Replace weak terms with stronger, ATS-friendly alternatives
        
        The output must be a COMPLETE, VALID JSON object with the exact same structure as the original resume JSON:
        {{
            "name": candidate name,
            "email": email address,
            "phone": phone number,
            "skills": array of skills (prioritized by relevance),
            "education": array of education entries,
            "experience": array of objects with {{
                "company": company name,
                "year": employment period,
                "role": job title,
                "responsibilities": enhanced descriptions aligned with job requirements
            }}
        }}
        
        Any skills or experiences added must be 100% justified by the original resume content - NO FABRICATION allowed.
        """,
        expected_output='Optimized resume JSON with strategically enhanced content for maximum ATS compatibility',
        agent=resume_optimizer_agent
    )

    task_5 = Task(
        description=f"""
        Create a professionally formatted LaTeX resume that is both visually appealing AND fully ATS-compatible.
        
        Your LaTeX document must include:
        
        1. CLEAN FORMATTING: Professional spacing, alignment, and visual hierarchy
        2. ATS OPTIMIZATION: Plain text compatibility for parsing systems
        3. STRATEGIC HIGHLIGHTING: Bold/italic for key terms matching job requirements
        4. SECTION ORGANIZATION: Clear section headers with consistent formatting
        5. CONTENT PRIORITIZATION: Most relevant information prominently positioned
        
        Use these LaTeX packages and design elements:
        - geometry package with 1-inch margins
        - hyperref package with proper color setup
        - fontawesome5 for contact icons
        - enumitem for clean bullet formatting
        - titlesec for customized section headers
        
        Structure the document with:
        - Name and contact centered at top
        - Clean section headers with subtle styling (underline or color)
        - Bulleted lists for skills, education, and experience
        
        The output must be COMPLETE, VALID LaTeX code ready for compilation without errors.
        
        Use the optimized resume JSON from the previous task as your source content.
        """,
        expected_output='Professionally formatted, ATS-optimized LaTeX resume with perfect syntax and visual appeal',
        agent=resume_latex_agent
    )

    task_6 = Task(
        description=f"""
        Create a compelling, personalized cover letter that directly connects the candidate's qualifications to the job requirements.
        
        Your cover letter must include:
        
        1. PROPER BUSINESS LETTER FORMAT: Complete with date, addresses, and professional closing
        2. COMPELLING OPENING: Engaging first paragraph that states the position and source
        3. QUALIFICATION ALIGNMENT: 2-3 paragraphs connecting specific experiences to job requirements
        4. COMPANY KNOWLEDGE: Reference to company mission, values, or recent achievements
        5. CONFIDENT CLOSING: Clear call to action and contact information
        6. ATS OPTIMIZATION: Strategic inclusion of 5-7 key job requirement terms
        
        Use these LaTeX elements:
        - letter document class with proper spacing
        - address, opening, and closing with correct formatting
        - hyperref for email/phone linking
        - professional, persuasive tone throughout
        
        The letter should be 250-400 words, professionally formatted, and directly targeted to THIS SPECIFIC job.
        
        The output must be COMPLETE, VALID LaTeX code ready for compilation without errors.
        
        Use the optimized resume JSON and job description summary from previous tasks.
        """,
        expected_output='Customized, compelling LaTeX cover letter that perfectly connects candidate qualifications to job requirements',
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
        tasks=[task_1, task_2, task_3, task_4, task_5, task_6],
        llm=llm,
        verbose=True
    )

    try:
        print("\n🚀 Starting resume optimization process...")
        results = crew.kickoff()
        
        # Get the task outputs directly
        resume_parser_output = results.tasks_output[0]  # Task 1 output
        jd_parser_output = results.tasks_output[1]      # Task 2 output
        ats_scorer_output = results.tasks_output[2]     # Task 3 output
        resume_optimizer_output = results.tasks_output[3]  # Task 4 output
        resume_latex_output = results.tasks_output[4]   # Task 5 output
        cover_letter_output = results.tasks_output[5]   # Task 6 output
        

        print("\n=== Processing Task Outputs ===")
        
        # Extract optimized resume JSON with improved error handling
        try:
            # Try to parse as JSON if it's a string
            if isinstance(resume_optimizer_output, str):
                # Look for JSON object in the string using a more robust pattern
                json_match = re.search(r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}', resume_optimizer_output, re.DOTALL)
                if json_match:
                    optimized_resume_json = json.loads(json_match.group(0))
                else:
                    optimized_resume_json = json.loads(resume_optimizer_output)
            elif hasattr(resume_optimizer_output, 'raw'):
                # If it's a TaskOutput object
                raw_data = resume_optimizer_output.raw
                if isinstance(raw_data, str):
                    json_match = re.search(r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}', raw_data, re.DOTALL)
                    if json_match:
                        optimized_resume_json = json.loads(json_match.group(0))
                    else:
                        optimized_resume_json = json.loads(raw_data)
                else:
                    # Already a dict
                    optimized_resume_json = raw_data
            else:
                # Assume it's already a dict
                optimized_resume_json = resume_optimizer_output
                
            print(f"✅ Successfully extracted optimized resume JSON")
            
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"⚠️ Error parsing optimized resume JSON: {e}")
            # Fall back to parsing the initial resume
            try:
                if isinstance(resume_parser_output, str):
                    json_match = re.search(r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}', resume_parser_output, re.DOTALL)
                    if json_match:
                        optimized_resume_json = json.loads(json_match.group(0))
                    else:
                        optimized_resume_json = json.loads(resume_parser_output)
                elif hasattr(resume_parser_output, 'raw'):
                    raw_data = resume_parser_output.raw
                    if isinstance(raw_data, str):
                        json_match = re.search(r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}', raw_data, re.DOTALL)
                        if json_match:
                            optimized_resume_json = json.loads(json_match.group(0))
                        else:
                            optimized_resume_json = json.loads(raw_data)
                    else:
                        optimized_resume_json = raw_data
                else:
                    optimized_resume_json = resume_parser_output
                print(f"✅ Using original parsed resume JSON as fallback")
            except Exception as e2:
                print(f"⚠️ Error parsing original resume JSON: {e2}")
                # Create a basic empty resume JSON as last resort
                optimized_resume_json = {
                    "name": "Candidate",
                    "email": "example@email.com",
                    "phone": "123-456-7890",
                    "skills": [],
                    "education": [],
                    "experience": []
                }
                print(f"⚠️ Using empty resume JSON template as last resort")

        # Get resume LaTeX content with improved extraction
        if isinstance(resume_latex_output, str):
            resume_latex = resume_latex_output
        elif hasattr(resume_latex_output, 'raw'):
            resume_latex = resume_latex_output.raw
        else:
            # Generate from JSON if LaTeX output is not available
            resume_latex = resume_json_to_latex(optimized_resume_json)
            
        # Extract LaTeX from task output if it doesn't look like LaTeX
        if not resume_latex.strip().startswith("\\documentclass"):
            # Look for LaTeX code with improved pattern
            latex_match = re.search(r'\\documentclass.*?\\begin\{document\}.*?\\end\{document\}', resume_latex, re.DOTALL)
            if latex_match:
                resume_latex = latex_match.group(0)
            else:
                # Generate from JSON if LaTeX extraction failed
                resume_latex = resume_json_to_latex(optimized_resume_json)
                print("⚠️ Generated LaTeX from JSON as fallback")

        # Get cover letter LaTeX content with improved extraction
        if isinstance(cover_letter_output, str):
            cover_letter_latex = cover_letter_output
        elif hasattr(cover_letter_output, 'raw'):
            cover_letter_latex = cover_letter_output.raw
        else:
            # Create a better cover letter if output is not available
            company_name = extract_company_name(job_description)
            cover_letter_latex = f"""\\documentclass{{letter}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{hyperref}}
\\usepackage{{fontawesome5}}
\\usepackage{{color}}
\\definecolor{{linkcolor}}{{HTML}}{{0066cc}}
\\hypersetup{{colorlinks=true, linkcolor=linkcolor, urlcolor=linkcolor}}

\\begin{{document}}

\\address{{{optimized_resume_json.get('name', 'Candidate')}\\\\
{optimized_resume_json.get('email', 'example@email.com')}\\\\
{optimized_resume_json.get('phone', '123-456-7890')}}}

\\begin{{letter}}{{Hiring Manager\\\\{company_name}}}

\\opening{{Dear Hiring Manager,}}

I am writing to express my interest in the Software Engineer position at {company_name}. With my background in software development and technical expertise, I believe I would be a valuable addition to your team.

My experience aligns well with the requirements outlined in your job posting. I am particularly skilled in problem-solving and collaborative development, with a track record of delivering high-quality solutions.

I am excited about the opportunity to contribute to {company_name}'s innovative work and would welcome the chance to discuss how my skills and experience could benefit your team.

\\closing{{Sincerely,}}

\\end{{letter}}
\\end{{document}}
"""
            print("⚠️ Generated cover letter as fallback")
            
        # Extract LaTeX from task output if it doesn't look like LaTeX
        if not cover_letter_latex.strip().startswith("\\documentclass"):
            # Look for LaTeX code with improved pattern
            latex_match = re.search(r'\\documentclass.*?\\begin\{document\}.*?\\end\{document\}', cover_letter_latex, re.DOTALL)
            if latex_match:
                cover_letter_latex = latex_match.group(0)
            else:
                # Use the improved cover letter template
                company_name = extract_company_name(job_description)
                cover_letter_latex = f"""\\documentclass{{letter}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{hyperref}}
\\usepackage{{fontawesome5}}
\\usepackage{{color}}
\\definecolor{{linkcolor}}{{HTML}}{{0066cc}}
\\hypersetup{{colorlinks=true, linkcolor=linkcolor, urlcolor=linkcolor}}

\\begin{{document}}

\\address{{{optimized_resume_json.get('name', 'Candidate')}\\\\
{optimized_resume_json.get('email', 'example@email.com')}\\\\
{optimized_resume_json.get('phone', '123-456-7890')}}}

\\begin{{letter}}{{Hiring Manager\\\\{company_name}}}

\\opening{{Dear Hiring Manager,}}

I am writing to express my interest in the Software Engineer position at {company_name}. With my background in software development and technical expertise, I believe I would be a valuable addition to your team.

My experience aligns well with the requirements outlined in your job posting. I am particularly skilled in problem-solving and collaborative development, with a track record of delivering high-quality solutions.

I am excited about the opportunity to contribute to {company_name}'s innovative work and would welcome the chance to discuss how my skills and experience could benefit your team.

\\closing{{Sincerely,}}

\\end{{letter}}
\\end{{document}}
"""
                print("⚠️ Generated cover letter from template as fallback")

        # Save outputs
        os.makedirs("output", exist_ok=True)
        resume_file = os.path.join("output", "Resume.tex")
        cover_letter_file = os.path.join("output", "Cover_letter.tex")

        # Save the LaTeX files
        with open(resume_file, "w") as f:
            f.write(resume_latex)
        print(f"✅ Saved resume LaTeX: {resume_file}")

        with open(cover_letter_file, "w") as f:
            f.write(cover_letter_latex)
        print(f"✅ Saved cover letter LaTeX: {cover_letter_file}")

        # Save the ATS score report as JSON
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

        # Compile the LaTeX files to PDF
        print("\n=== Compiling PDFs ===")
        pdf_success = False
        
        # Try to compile resume PDF
        if compile_latex_to_pdf(resume_file):
            print(f"✅ Successfully compiled Resume.pdf")
            pdf_success = True
        else:
            print(f"⚠️ Failed to compile Resume.pdf")
        
        # Try to compile cover letter PDF
        if compile_latex_to_pdf(cover_letter_file):
            print(f"✅ Successfully compiled Cover_letter.pdf")
            pdf_success = True
        else:
            print(f"⚠️ Failed to compile Cover_letter.pdf")
            
        if pdf_success:
            print("\n🎉 Process complete! Check the output directory for your files.")
        else:
            print("""
⚠️ PDF compilation failed. Possible reasons:
1. pdflatex is not installed on your system
2. There are errors in the LaTeX code
3. Required LaTeX packages are missing

You can manually compile the LaTeX files using an online service like Overleaf.
""")

    except Exception as e:
        print(f"❌ Error during crew execution: {e}")
        import traceback
        traceback.print_exc()

# Example usage
if __name__ == '__main__':
    job_description = """
    Software Engineer at TechCorp
    
    We are looking for a talented Software Engineer to join our dynamic team. The ideal candidate will have strong experience in Python development, database management, and web technologies. You will work on designing, developing, and maintaining various software solutions for our clients.
    
    Requirements:
    - Bachelor's degree in Computer Science or related field
    - 3+ years of experience in software development
    - Proficiency in Python, JavaScript, and SQL
    - Experience with web frameworks like Django or Flask
    - Knowledge of RESTful APIs and microservices
    - Familiarity with cloud platforms like AWS or Azure
    - Strong problem-solving and analytical skills
        - Excellent communication and teamwork skills
    - Ability to work in a fast-paced environment

    Responsibilities:
    - Design, develop, and maintain software applications
    - Collaborate with cross-functional teams to ensure project success
    - Troubleshoot and debug software issues
    - Stay up-to-date with emerging technologies and trends
    - Contribute to the continuous improvement of our development processes
    """
    run_resume_optimizer(job_description)