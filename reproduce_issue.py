import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def parse_resume_simulation():
    # Simulated simple resume text
    resume_text = """
    John Doe
    Software Engineer
    Skills: Python, JavaScript, SQL
    Education: B.S. Computer Science, University of Examples, 2020
    """
    
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
    
    print("Sending prompt to Gemini...")
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        print("--- RAW RESPONSE START ---")
        print(response.text)
        print("--- RAW RESPONSE END ---")
        
        parsed = json.loads(response.text)
        print("JSON Parsed Successfully!")
        print(json.dumps(parsed, indent=2))
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    parse_resume_simulation()
