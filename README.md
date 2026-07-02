# CareerCompass - AI Resume Analyzer

CareerCompass is an AI-powered resume analyzer and company matching Flask web application. Users upload a PDF resume, the app extracts the resume text, uses Google Gemini to parse candidate details, and matches the candidate against a local company dataset.

## Category

- Career-tech / HR-tech
- AI resume analysis
- Company recommendation system
- Flask web application

## Features

- PDF resume upload
- Resume text extraction with PyMuPDF
- AI-powered resume parsing with Google Gemini
- Company matching based on skills, tech stack, and keywords
- Match scores for top companies
- Personalized strengths, improvement areas, and interview tips
- Friendly handling for missing API keys, invalid API keys, and quota errors

## Tech Stack

- Python
- Flask
- Google Gemini API via `google-genai`
- Pandas
- OpenPyXL
- PyMuPDF
- Tenacity
- python-dotenv
- Tailwind CSS CDN

## Project Structure

```text
careercompassog/
├── app.py
├── requirements.txt
├── .env.example
├── company_data_no_duplicates.xlsx
├── templates/
│   ├── index.html
│   └── results.html
└── uploads/
```

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create your local environment file:

```powershell
copy .env.example .env
```

Add your Google AI Studio API key in `.env`:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
GEMINI_MODEL=gemini-flash-lite-latest
```

## Run

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Important GitHub Note

Do not commit your real `.env` file or API key. Commit `.env.example` instead.

The `.venv/`, uploaded resumes, logs, and `__pycache__/` files should not be uploaded.

## Current Status

This is a local development and portfolio project. It is not production-ready yet because it does not include authentication, persistent database storage, production hosting configuration, or full automated test coverage.
