# # AI Resume Analyzer - Flask Web Application
# # Description: A web application that analyzes a resume PDF against company data from an Excel file.

# import os
# import json
# import requests
# import fitz  # PyMuPDF
# import pandas as pd
# from flask import Flask, request, render_template, redirect, url_for

# # --- Flask App Initialization ---
# app = Flask(__name__)
# # Configure a temporary upload folder
# UPLOAD_FOLDER = 'uploads'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# # Ensure the upload folder exists
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# # --- Data Loading ---

# def load_company_data(filepath="company_data.xlsx"):
#     """
#     Loads company data from the specified Excel file.
    
#     Args:
#         filepath (str): The path to the .xlsx file.

#     Returns:
#         list: A list of dictionaries, where each dictionary represents a company.
#               Returns an empty list if the file is not found or is empty.
#     """
#     try:
#         df = pd.read_excel(filepath)
#         # Convert NaN to empty strings to avoid errors during processing
#         df = df.fillna('')
#         # Convert the DataFrame to a list of dictionaries
#         return df.to_dict('records')
#     except FileNotFoundError:
#         print(f"Error: The file '{filepath}' was not found.")
#         return []
#     except Exception as e:
#         print(f"Error reading or processing the Excel file: {e}")
#         return []

# # Load the company data once when the app starts
# COMPANIES = load_company_data()

# # --- Hardcoded Data (Links) ---
# COURSE_LINKS = {
#     "Python": "https://www.coursera.org/specializations/python",
#     "Java": "https://www.coursera.org/specializations/java-programming",
#     "C++": "https://www.coursera.org/learn/c-plus-plus-introduction",
#     "Cloud": "https://www.coursera.org/professional-certificates/google-cloud-computing",
#     "Data Science": "https://www.coursera.org/professional-certificates/ibm-data-science",
#     "Machine Learning": "https://www.coursera.org/specializations/machine-learning-introduction",
#     "AWS": "https://www.coursera.org/learn/aws-fundamentals",
#     "Azure": "https://www.coursera.org/learn/microsoft-azure-fundamentals",
#     "React": "https://www.coursera.org/learn/react-basics",
#     "SQL": "https://www.coursera.org/learn/sql-for-data-science"
# }

# # --- Core Helper Functions ---

# def extract_text_from_pdf(pdf_path):
#     """Extracts text from a PDF file."""
#     try:
#         doc = fitz.open(pdf_path)
#         text = "".join(page.get_text() for page in doc)
#         return text
#     except Exception as e:
#         print(f"Error reading PDF: {e}")
#         return None

# def call_generative_api(api_key, prompt, is_json_output=False):
#     """Calls the Google Generative AI API."""
#     api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
#     headers = {"Content-Type": "application/json"}
#     payload = {"contents": [{"parts": [{"text": prompt}]}]}
#     if is_json_output:
#         payload["generationConfig"] = {"responseMimeType": "application/json"}

#     try:
#         response = requests.post(api_url, headers=headers, json=payload)
#         response.raise_for_status()
#         result = response.json()
#         content = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
#         return json.loads(content) if is_json_output else content
#     except Exception as e:
#         print(f"API call failed: {e}")
#         return None

# def parse_resume(api_key, resume_text):
#     """Uses AI to parse resume text into structured JSON."""
#     prompt = f"""
#         Extract the following from the resume and return it as a valid JSON object:
#         "name" (string), "skills" (object with categories as keys and lists of strings as values),
#         "projects" (list of objects with "title" and "description"), and "education" (list of objects
#         with "degree", "institution", and "year").

#         Resume text: --- {resume_text} ---
#     """
#     return call_generative_api(api_key, prompt, is_json_output=True)

# def calculate_match_score(resume_data, company_profile):
#     """Calculates a match score based on skills."""
#     if not resume_data or "skills" not in resume_data:
#         return 0
    
#     resume_skills = {skill.strip().lower() for category in resume_data["skills"].values() for skill in category}
    
#     # Ensure the column names from your Excel file are used here
#     tech_stack_str = company_profile.get("Major_Tech_Stack", "")
#     keywords_str = company_profile.get("Essential_Keywords", "")

#     company_tech = {s.strip().lower() for s in tech_stack_str.split(',')}
#     company_keywords = {k.strip().lower() for k in keywords_str.split(',')}

#     score = (len(resume_skills.intersection(company_tech)) * 5) + (len(resume_skills.intersection(company_keywords)) * 2)
#     return score

# def generate_report(api_key, resume_data, company_profile):
#     """Generates a personalized report using AI."""
#     prompt = f"""
#         You are a career counselor. Generate a structured report as a valid JSON object with keys:
#         "match_summary" (string), "strengths" (list of strings), "improvement_areas" (list of objects
#         with "text" and "skill" from {', '.join(COURSE_LINKS.keys())}), and "interview_tips" (list of strings).

#         Resume Data: {json.dumps(resume_data)}
#         Company Profile: {json.dumps(company_profile)}
#     """
#     return call_generative_api(api_key, prompt, is_json_output=True)


# # --- Flask Routes ---

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     """
#     Handles both displaying the form (GET) and processing the upload (POST).
#     """
#     if request.method == 'POST':
#         # Check if the required data is in the request
#         if 'resumeFile' not in request.files or 'apiKey' not in request.form:
#             return redirect(request.url)
        
#         file = request.files['resumeFile']
#         api_key = request.form['apiKey']

#         if file.filename == '' or not api_key:
#             return redirect(request.url) # Or show an error message

#         if file:
#             # 1. Save the uploaded file temporarily
#             filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
#             file.save(filepath)

#             # 2. Process the file
#             resume_text = extract_text_from_pdf(filepath)
#             if not resume_text:
#                 # Handle PDF read error
#                 return render_template('index.html', error="Could not read text from PDF.")

#             parsed_resume = parse_resume(api_key, resume_text)
#             if not parsed_resume:
#                 # Handle AI parsing error
#                 return render_template('index.html', error="AI failed to parse the resume.")

#             # 3. Perform matching
#             if not COMPANIES:
#                  return render_template('index.html', error="Company data could not be loaded. Check the Excel file.")

#             match_results = []
#             for company in COMPANIES:
#                 score = calculate_match_score(parsed_resume, company)
#                 match_results.append({
#                     "company_name": company.get("Company Name", "Unknown Company"),
#                     "match_score": score,
#                     "website_url": company.get("Website_URL", "#")
#                 })
            
#             top_matches = sorted(match_results, key=lambda x: x['match_score'], reverse=True)

#             # 4. Generate report for the top match
#             report = None
#             if top_matches and top_matches[0]['match_score'] > 0:
#                 top_company_name = top_matches[0]['company_name']
#                 top_company_profile = next((c for c in COMPANIES if c.get("Company Name") == top_company_name), None)
#                 if top_company_profile:
#                     report = generate_report(api_key, parsed_resume, top_company_profile)

#             # 5. Clean up the uploaded file
#             os.remove(filepath)

#             # 6. Render the results page
#             return render_template(
#                 'results.html',
#                 candidate_name=parsed_resume.get('name', 'Candidate'),
#                 top_matches=top_matches[:6], # Send top 6 to the template
#                 report=report,
#                 top_company_name=top_matches[0]['company_name'] if top_matches else "N/A",
#                 course_links=COURSE_LINKS
#             )

#     # For a GET request, just show the upload page
#     return render_template('index.html', error=None)

# if __name__ == '__main__':
#     # Runs the Flask application
#     app.run(debug=True)


# AI Resume Analyzer - Flask Web Application
# Description: A web application that analyzes a resume PDF against company data from an Excel file.

import os
import json
import requests
import fitz  # PyMuPDF
import pandas as pd
from flask import Flask, request, render_template, redirect, url_for

# --- Configuration ---
# Hardcode your API key here for convenience
API_KEY = "AIzaSyAAXHurf-6wUlcx3VyTfc-38C_3cdFcglA"

# --- Flask App Initialization ---
app = Flask(__name__)
# Configure a temporary upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --- Data Loading ---

def load_company_data(filepath="company_data_no_duplicates.xlsx"):
    """
    Loads company data from the specified Excel file.
    
    Args:
        filepath (str): The path to the .xlsx file.

    Returns:
        list: A list of dictionaries, where each dictionary represents a company.
              Returns an empty list if the file is not found or is empty.
    """
    try:
        df = pd.read_excel(filepath)
        # Convert NaN to empty strings to avoid errors during processing
        df = df.fillna('')
        # Convert the DataFrame to a list of dictionaries
        return df.to_dict('records')
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return []
    except Exception as e:
        print(f"Error reading or processing the Excel file: {e}")
        return []

# Load the company data once when the app starts
COMPANIES = load_company_data()

# --- Hardcoded Data (Links) ---
COURSE_LINKS = {
    "Python": "https://www.coursera.org/specializations/python",
    "Java": "https://www.coursera.org/specializations/java-programming",
    "C++": "https://www.coursera.org/learn/c-plus-plus-introduction",
    "Cloud": "https://www.coursera.org/professional-certificates/google-cloud-computing",
    "Data Science": "https://www.coursera.org/professional-certificates/ibm-data-science",
    "Machine Learning": "https://www.coursera.org/specializations/machine-learning-introduction",
    "AWS": "https://www.coursera.org/learn/aws-fundamentals",
    "Azure": "https://www.coursera.org/learn/microsoft-azure-fundamentals",
    "React": "https://www.coursera.org/learn/react-basics",
    "SQL": "https://www.coursera.org/learn/sql-for-data-science"
}

# --- Core Helper Functions ---

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = "".join(page.get_text() for page in doc)
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def call_generative_api(api_key, prompt, is_json_output=False):
    """Calls the Google Generative AI API."""
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    if is_json_output:
        payload["generationConfig"] = {"responseMimeType": "application/json"}

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        content = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return json.loads(content) if is_json_output else content
    except Exception as e:
        print(f"API call failed: {e}")
        return None

def parse_resume(api_key, resume_text):
    """Uses AI to parse resume text into structured JSON."""
    prompt = f"""
        Extract the following from the resume and return it as a valid JSON object:
        "name" (string), "skills" (object with categories as keys and lists of strings as values),
        "projects" (list of objects with "title" and "description"), and "education" (list of objects
        with "degree", "institution", and "year").

        Resume text: --- {resume_text} ---
    """
    return call_generative_api(api_key, prompt, is_json_output=True)

def calculate_match_score(resume_data, company_profile):
    """Calculates a match score based on skills."""
    if not resume_data or "skills" not in resume_data:
        return 0
    
    resume_skills = {skill.strip().lower() for category in resume_data["skills"].values() for skill in category}
    
    # Ensure the column names from your Excel file are used here
    tech_stack_str = company_profile.get("Major_Tech_Stack", "")
    keywords_str = company_profile.get("Essential_Keywords", "")

    company_tech = {s.strip().lower() for s in tech_stack_str.split(',')}
    company_keywords = {k.strip().lower() for k in keywords_str.split(',')}

    score = (len(resume_skills.intersection(company_tech)) * 5) + (len(resume_skills.intersection(company_keywords)) * 2)
    return score

def generate_report(api_key, resume_data, company_profile):
    """Generates a personalized report using AI."""
    prompt = f"""
        You are a career counselor. Generate a structured report as a valid JSON object with keys:
        "match_summary" (string), "strengths" (list of strings), "improvement_areas" (list of objects
        with "text" and "skill" from {', '.join(COURSE_LINKS.keys())}), and "interview_tips" (list of strings).

        Resume Data: {json.dumps(resume_data)}
        Company Profile: {json.dumps(company_profile)}
    """
    return call_generative_api(api_key, prompt, is_json_output=True)


# --- Flask Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Handles both displaying the form (GET) and processing the upload (POST).
    """
    if request.method == 'POST':
        # Check if the file is in the request
        if 'resumeFile' not in request.files:
            return redirect(request.url)
        
        file = request.files['resumeFile']

        if file.filename == '':
            return redirect(request.url) # Or show an error message

        if file:
            # 1. Save the uploaded file temporarily
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            # 2. Process the file
            resume_text = extract_text_from_pdf(filepath)
            if not resume_text:
                return render_template('index.html', error="Could not read text from PDF.")

            # Use the hardcoded API_KEY
            parsed_resume = parse_resume(API_KEY, resume_text)
            if not parsed_resume:
                return render_template('index.html', error="AI failed to parse the resume.")

            # 3. Perform matching
            if not COMPANIES:
                 return render_template('index.html', error="Company data could not be loaded. Check the Excel file.")

            match_results = []
            for company in COMPANIES:
                score = calculate_match_score(parsed_resume, company)
                match_results.append({
                    "company_name": company.get("Company Name", "Unknown Company"),
                    "match_score": score,
                    "website_url": company.get("Website_URL", "#")
                })
            
            top_matches = sorted(match_results, key=lambda x: x['match_score'], reverse=True)

            # 4. Generate report for the top match
            report = None
            if top_matches and top_matches[0]['match_score'] > 0:
                top_company_name = top_matches[0]['company_name']
                top_company_profile = next((c for c in COMPANIES if c.get("Company Name") == top_company_name), None)
                if top_company_profile:
                    # Use the hardcoded API_KEY
                    report = generate_report(API_KEY, parsed_resume, top_company_profile)

            # 5. Clean up the uploaded file
            os.remove(filepath)

            # 6. Render the results page
            return render_template(
                'results.html',
                candidate_name=parsed_resume.get('name', 'Candidate'),
                top_matches=top_matches[:6],
                report=report,
                top_company_name=top_matches[0]['company_name'] if top_matches else "N/A",
                course_links=COURSE_LINKS
            )

    # For a GET request, just show the upload page
    return render_template('index.html', error=None)

if __name__ == '__main__':
    # Runs the Flask application
    app.run(debug=True)