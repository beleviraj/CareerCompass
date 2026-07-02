import os
import json
import pandas as pd
import fitz  # PyMuPDF
from google import genai
from flask import Flask, request, render_template, redirect
from dotenv import load_dotenv
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential
from werkzeug.utils import secure_filename


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
COMPANY_DATA_FILE = os.path.join(BASE_DIR, "company_data_no_duplicates.xlsx")
ALLOWED_EXTENSIONS = {"pdf"}

load_dotenv(os.path.join(BASE_DIR, ".env"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

app = Flask(__name__)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024


class GeminiConfigurationError(RuntimeError):
    pass

# ===============================
# DATA LOADING
# ===============================
def load_company_data(filepath=COMPANY_DATA_FILE):
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found.")
        return []
    try:
        df = pd.read_excel(filepath).fillna("")
        # Normalize column names to avoid KeyErrors later
        df.columns = [c.strip() for c in df.columns] 
        return df.to_dict("records")
    except Exception as e:
        print("Company file error:", e)
        return []

COMPANIES = load_company_data()

# ===============================
# AI PROCESSING (Using SDK)
# ===============================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(pdf_path):
    try:
        with fitz.open(pdf_path) as doc:
            text = "".join(page.get_text() for page in doc)
        return text[:10000]  # Limit context window if resume is huge
    except Exception as e:
        print("PDF Error:", e)
        return ""


def parse_json_response(response_text):
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("AI response did not contain JSON.")

    return json.loads(cleaned[start:end + 1])


def get_ai_client():
    if client is None:
        raise GeminiConfigurationError("GEMINI_API_KEY is missing. Add it to careercompassog/.env.")
    return client


def generate_gemini_content(prompt):
    try:
        return get_ai_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
    except Exception as e:
        error_text = str(e)
        if "API key not valid" in error_text or "API_KEY_INVALID" in error_text:
            raise GeminiConfigurationError(
                "Your Gemini API key is invalid. Replace GEMINI_API_KEY in careercompassog/.env with a valid Google AI Studio API key."
            ) from e
        if "RESOURCE_EXHAUSTED" in error_text or "quota" in error_text.lower():
            raise GeminiConfigurationError(
                f"Gemini quota is exhausted for {GEMINI_MODEL}. Wait for the quota window to reset, enable billing, or set GEMINI_MODEL=gemini-flash-lite-latest in careercompassog/.env."
            ) from e
        raise


@retry(
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=2, min=2, max=60),
    retry=retry_if_not_exception_type(GeminiConfigurationError),
    reraise=True
)
def parse_resume(resume_text):
    prompt = f"""
    Extract the following details from the resume text below.
    Return strictly JSON matching this schema:
    {{
      "name": "Full Name",
      "skills": {{
        "technical": ["list", "of", "skills"],
        "tools": [],
        "languages": []
      }},
      "projects": [ {{ "title": "Project Name", "description": "Short summary" }} ],
      "education": [ {{ "degree": "Degree Name", "institution": "College", "year": "Year" }} ]
    }}
    
    RESUME TEXT:
    {resume_text}
    """
    response = generate_gemini_content(prompt)
    return parse_json_response(response.text)

@retry(
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=2, min=2, max=60),
    retry=retry_if_not_exception_type(GeminiConfigurationError),
    reraise=True
)
def generate_report(resume_data, company):
    prompt = f"""
    Analyze the fit between this candidate and the company.
    Candidate: {json.dumps(resume_data)}
    Company: {json.dumps(company)}
    
    Return JSON:
    {{
      "match_summary": "2 sentence summary",
      "strengths": ["List of matching skills"],
      "improvement_areas": [ {{ "skill": "Missing Skill", "text": "Why it matters" }} ],
      "interview_tips": ["Specific technical question to prepare for"]
    }}
    """
    response = generate_gemini_content(prompt)
    return parse_json_response(response.text)

# ===============================
# LOGIC & ROUTES
# ===============================
def calculate_match_score(resume_data, company):
    if not resume_data or not isinstance(resume_data.get("skills"), dict):
        return 0
    
    # Flatten resume skills into a single set
    resume_skills = set()
    for category in resume_data["skills"].values():
        if not isinstance(category, list):
            continue
        for skill in category:
            resume_skills.add(str(skill).lower().strip())

    # Safely get company data
    tech_stack = {x.strip().lower() for x in str(company.get("Major_Tech_Stack", "")).split(",") if x.strip()}
    keywords = {x.strip().lower() for x in str(company.get("Essential_Keywords", "")).split(",") if x.strip()}

    # Weighted Scoring
    match_tech = len(resume_skills.intersection(tech_stack))
    match_keywords = len(resume_skills.intersection(keywords))
    
    return (match_tech * 10) + (match_keywords * 5)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "resumeFile" not in request.files:
            return redirect(request.url)
        
        file = request.files["resumeFile"]
        if file.filename == "":
            return redirect(request.url)
        if not allowed_file(file.filename):
            return render_template("index.html", error="Please upload a PDF file.")

        filename = secure_filename(file.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)

        # 1. Extract
        try:
            text = extract_text_from_pdf(path)
        finally:
            if os.path.exists(path):
                os.remove(path)

        if len(text) < 50:
            return render_template("index.html", error="Resume is empty or unreadable.")

        # 2. Parse with AI
        try:
            parsed_data = parse_resume(text)
        except GeminiConfigurationError as e:
            return render_template("index.html", error=str(e))
        except Exception as e:
            print("Resume parsing error:", e)
            return render_template("index.html", error="AI could not process the resume right now. Please try again in 1 minute.")
            
        if not parsed_data:
            return render_template("index.html", error="AI could not process the resume.")

        # 3. Match against Database
        results = []
        for company in COMPANIES:
            score = calculate_match_score(parsed_data, company)
            if score > 0: # Only show relevant matches
                results.append({
                    "company_name": company.get("Company Name", "Unknown"),
                    "match_score": score,
                    "website_url": company.get("Website_URL", "#"),
                    "tech_stack": company.get("Major_Tech_Stack", "")
                })

        results.sort(key=lambda x: x["match_score"], reverse=True)

        # 4. Generate Strategy for Top Match
        report = None
        top_company_name = ""
        if results:
            top_match = results[0]
            top_company_name = top_match["company_name"]
            # Find original company dict
            company_data = next((c for c in COMPANIES if c.get("Company Name") == top_company_name), {})
            try:
                report = generate_report(parsed_data, company_data)
            except Exception as e:
                print("Report generation error:", e)
                report = None # Fail gracefully for report if rate limited

        return render_template(
            "results.html",
            candidate_name=parsed_data.get("name", "Candidate"),
            matches=results[:5],
            report=report,
            top_company=top_company_name
        )

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
