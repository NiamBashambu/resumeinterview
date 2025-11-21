# Resume interviewer — Spec Sheet

**Spec Version:** v0.2  
**Date:** 2025-01-XX  
**Owner:** GROUP 1
**Status:** Final Project Presentation (AI-Enhanced)

---

# Part A — Business Context & Problem Statement

## A1. Strategy / Context (Simplified)

Companies want to streamline their interview process by asking candidates about certain skills on their resumes. Instead of having virtual interviews, the candidate will go through a hirevue style interview where they will be asked about technical skills on their resume.
This product that companies can use will auto interview candidates asking questions specific to their resume and jobs to ensure the candidates are actually qualified based on what is written on their resume.

---

## A2. Problem Statement (S–C–Q)

**Situation:** Companies regularly face candidates not being able to back up their skills listed in resume.
**Complication:** Results in waste of time/effort in recruiting.
**Question:** How can we ensure candidates are actually compentent in the skills on resume.

---

## A3. SMART Goals (Workshop-Scope)

- Demonstrate at least **one working API** returning JSON within 2 seconds (local). OCR library that reads the text in the resume and analyzes it.
- Display 3-5 personalized interview questions for each resume scanned.


---

## A4. One-Line Scope

Build a lightweight demo app that takes a `job resume`, reads a the content, and returns 3–5 personalized/technical questions to ask in an interview.

---

# Part B — Build Plan (Solution Architecture & Design)

## B1. Overview

A React frontend calls a small backend API (FastAPI).
The backend accepts a resume PDF upload (and optional job role), extracts text, and uses AI (Ollama) to dynamically detect skills, infer proficiency levels, and generate personalized technical interview questions. The system uses a local JSON skill–question bank as reference examples and fallback, but primarily relies on AI for dynamic, context-aware analysis.

### B1.1. AI Architecture

The system implements a three-stage AI pipeline:

1. **Skill Detection**: Ollama analyzes resume text to identify technical skills, considering context, job role relevance, and available skills from the question bank.

2. **Level Inference**: Ollama determines proficiency levels (beginner/intermediate/advanced) by analyzing experience descriptions, project complexity, years of experience, and technical language used.

3. **Question Generation**: Ollama generates personalized interview questions based on:
   - Detected skills and their inferred levels
   - Resume context and specific experiences mentioned
   - Reference examples from question bank (for style consistency)
   - Job role requirements (if provided)

All stages include graceful fallback to manual/keyword-based methods if Ollama is unavailable.

---

## B2. Inputs

### UserPrefs

// Conceptual shape (not literal JSON because of the file)
{
  resumeFile: File;     // PDF resume uploaded by user
  jobRole?: string;     // Optional, e.g., "Data Science", "Software Engineer"
}
resumeFile: Required. A single PDF file.

jobRole: Optional string to slightly bias which skills/questions are prioritized.
### Inventory JSON (Local)

File: '/data/skill_question_bank.json'

Example:

{
  "skill": "python",
  "displayName": "Python",
  "levels": {
    "beginner": [
      "Explain the difference between a list and a tuple in Python."
    ],
    "intermediate": [
      "How would you use list comprehensions to transform a dataset in Python?"
    ],
    "advanced": [
      "Describe how you would optimize a slow Python data pipeline that processes large files."
    ]
  }
}
Each entry represents one skill.

levels contains arrays of questions for "beginner", "intermediate", and "advanced".

The backend also maintains a skills vocabulary, e.g. ["python", "git", "html", "css", "sql", ...], to match resume text to skill keys in this JSON. This vocabulary is used for:
- Fallback skill detection when AI is unavailable
- Validating AI-detected skills
- Mapping skill variations to canonical keys
---

## B3. Outputs

DetectedSkill Object

```ts
{
  name: string;          // e.g., "Python"
  key: string;           // canonical key used in JSON, e.g., "python"
  level: "beginner" | "intermediate" | "advanced";
}

InterviewQuestion Object

```ts
{
  skill: string;         // canonical key, e.g., "python"
  level: "beginner" | "intermediate" | "advanced";
  question: string;      // one interview question string
}
```

API Response
```ts
{
  skills: DetectedSkill[];
  questions: InterviewQuestion[];
  qa_summary?: {
    total: number;       // number of questions reviewed by judge
    passed: number;      // number considered valid / on-target
  };
}
skills: All skills the backend detected from the resume (and possibly weighted by jobRole).

questions: 3–5 final interview questions to show in the UI.

qa_summary: Optional; present only if the judge module is enabled.

---
B4. Core Logic / Modules

Parse Request

Accept multipart/form-data with:

resumeFile (PDF)

optional jobRole string

Extract Text from Resume (OCR/Text Pipeline)

Use a Python PDF library (e.g., pdfplumber or PyPDF2) to get raw text.

Normalize:

lowercase

strip extra whitespace/punctuation where helpful.

Detect Skills (AI-Enhanced)

**Primary Method (AI):**
- Use Ollama LLM to analyze resume text and dynamically identify technical skills
- AI receives available skills from question bank as reference
- AI extracts skills with context and initial proficiency assessment
- Skills are validated against the question bank to ensure they exist
- Fallback to manual keyword matching if Ollama is unavailable or fails

**Fallback Method (Manual):**
- Maintain a skills vocabulary that maps surface phrases → canonical keys (e.g., "Python", "python 3" → "python")
- For each skill in the vocabulary, check if it appears in the text
- Optionally prioritize skills relevant to the provided jobRole (e.g., Data Science → Python, SQL, Pandas)

Infer Skill Level (AI-Enhanced)

**Primary Method (AI):**
- Use Ollama LLM to analyze context around skill mentions in the resume
- AI considers: years of experience, project complexity, role descriptions, technical language used
- AI determines proficiency level: "beginner", "intermediate", or "advanced"
- More nuanced than keyword matching - understands context and implications
- Fallback to keyword-based inference if Ollama is unavailable or fails

**Fallback Method (Manual):**
- Look at surrounding text for keywords like "beginner", "intermediate", "advanced", "proficient", "expert", "3+ years", etc.
- Map terms to normalized levels:
  - "familiar", "some experience" → "beginner"
  - "proficient", "2+ years" → "intermediate"
  - "advanced", "expert", "lead", "5+ years" → "advanced"
- If no signal found, default to "intermediate".

Load Skill–Question Bank

Read /data/skill_question_bank.json into memory.

For each detected skill, check if it exists in the bank.

If not found, skip that skill for question generation (still can appear in skills list or be omitted, depending on design).

Generate Question Set (AI-Enhanced)

**Primary Method (AI):**
- Use Ollama LLM to dynamically generate personalized interview questions
- AI receives:
  - Detected skills with proficiency levels
  - Resume context/excerpts
  - Reference examples from question bank (for style and difficulty guidance)
- AI generates questions that:
  - Match the detected skill and proficiency level
  - Are personalized based on resume content
  - Are appropriate for the stated proficiency level (beginner/intermediate/advanced)
  - Are specific and technical (not generic)
- Questions are validated against question bank to ensure skill exists
- If AI generates fewer than 3 questions, backfill from question bank

**Fallback Method (Question Bank):**
- For each DetectedSkill, select 1+ questions from levels[level] in the JSON
- Enforce 3–5 total questions:
  - If too many → truncate with a simple strategy (e.g., prioritize jobRole-relevant skills)
  - If too few → backfill using intermediate questions or related skills if available

**Hybrid Approach:**
- System attempts AI generation first
- Uses AI-generated questions even if fewer than 5
- Backfills from question bank to ensure 3–5 total questions
- Falls back entirely to question bank if AI generation fails

(Optional) Judge / QA Module

For each candidate question, optionally send a lightweight payload to a local LLM judge:

Input: { skill, level, question, resumeSnippet }

Output: { pass: boolean, reasons?: string[] }

Filter out or flag questions that:

Don’t clearly relate to the skill.

Are obviously not at the claimed difficulty level.

Summarize into qa_summary.

Return JSON to UI

Build the canonical response:

{
  "skills": [...],
  "questions": [...],
  "qa_summary": { ... } // optional
}


Return within the performance budget.
---

B5. Design & Behavior Rules (Minimal)

R-SCHEMA-01:
All responses from the main endpoint must follow:

{ skills: DetectedSkill[]; questions: InterviewQuestion[]; qa_summary?: {...} }


R-QUESTION-01:
Each InterviewQuestion.question must be clearly about the associated skill.
(No generic “tell me about yourself” style questions.)

R-COUNT-01:
If at least one skill is detected and present in the question bank, the backend must return between 3 and 5 questions.

R-FILTER-01:
The backend must not fabricate skills that are not actually present in the resume text.
Only generate questions for:

skills detected from the resume, and

skills that exist in skill_question_bank.json.

R-PERF-01:
For local runs, the API should respond in < 2 seconds for a typical 1–3 page resume (when using manual fallback). AI-based analysis may take longer (5-10 seconds) depending on Ollama model and hardware, but should still be reasonable for demo purposes.

R-AI-01:
The system must gracefully handle Ollama unavailability:
- Automatically detect if Ollama is running
- Fall back to manual detection/inference if AI is unavailable
- Log warnings but continue operation
- Never fail completely due to AI unavailability

R-CLAR-01:
If no skills are detected:

Backend returns:

{ "skills": [], "questions": [] }


Frontend must prompt the user to:

Confirm the correct file type, or

Optionally select a target job role or top skill manually.

---

B6. Schemas (Authoritative)

Input concepts: ResumePayload (file + optional jobRole)

Data source: skill_question_bank.json

Output objects:

DetectedSkill

InterviewQuestion

API response { skills, questions, qa_summary? }

(Definitions are in B2 and B3 and must be treated as authoritative.)

---
B7. Mini I/O Example
Input

POST /api/analyze_resume
Content-Type: multipart/form-data

resumeFile: A PDF that contains lines such as:

Skills: Python (advanced), Git, HTML, CSS
Experience building data pipelines in Python and using Git for version control.

jobRole: "Data Science"


Output
{
  "skills": [
    {
      "name": "Python",
      "key": "python",
      "level": "advanced"
    },
    {
      "name": "Git",
      "key": "git",
      "level": "intermediate"
    },
    {
      "name": "HTML",
      "key": "html",
      "level": "intermediate"
    },
    {
      "name": "CSS",
      "key": "css",
      "level": "intermediate"
    }
  ],
  "questions": [
    {
      "skill": "python",
      "level": "advanced",
      "question": "Based on your experience building data pipelines mentioned in your resume, how would you optimize a Python pipeline that processes large CSV files while maintaining data integrity?"
    },
    {
      "skill": "python",
      "level": "advanced",
      "question": "Given your advanced Python experience, explain how generators work and when you would choose them over lists for processing large datasets."
    },
    {
      "skill": "git",
      "level": "intermediate",
      "question": "In your version control workflow, what is the difference between git merge and git rebase, and when would you use each approach?"
    },
    {
      "skill": "html",
      "level": "intermediate",
      "question": "How would you structure a semantic HTML page for a portfolio site, considering accessibility and SEO best practices?"
    }
  ]
}


---

B8. Metrics (Simplified)

Functional

API responds successfully with a valid JSON body.

At least one resume test returns 3–5 questions.

UI displays detected skills and questions clearly.

Quality (Optional, if judge enabled)

% of questions that pass judge validation (e.g., >80%).

Number of times judge flags “wrong skill” or “wrong level.”

Performance

Average latency for /api/analyze_resume on a typical resume (target: < 2 seconds).
----

B9. Assumptions & Dependencies

A local JSON file exists at /data/skill_question_bank.json with at least:

core programming/web skills (e.g., Python, Git, HTML, CSS, SQL).

1–3 questions per level per skill.

Resumes are provided as PDF files, mostly text-based (not purely scanned images).

No external network calls are required to:

- extract text, or
- retrieve interview questions, or
- run AI analysis (uses local Ollama instance)

**Setup Requirements:**
- Ollama must be installed locally (download from ollama.ai)
- Required model must be pulled: `ollama pull llama3.2`
- Ollama service must be running (typically runs automatically on install)

Backend uses:

- FastAPI (Python) for the main API
- Python PDF text extraction library (pdfplumber)
- Ollama Python client for AI-based analysis (ollama package)
- Local Ollama installation with LLM model (default: llama3.2)

Frontend uses:

- Vite + React for UI

AI Integration:

- Ollama must be installed and running locally (see setup instructions)
- Default model: llama3.2 (can be configured)
- System automatically detects Ollama availability
- Graceful fallback to manual methods if Ollama is unavailable
- All AI operations are local - no external cloud dependencies

LLM judge (if used) is local or stubbed (no external cloud dependency required for the workshop demo).
----
# Part C — Testing Plan

Part C — Testing Plan
C1. Positive Tests
TC-01 — Basic Resume with Clear Skills

Input:

Resume text includes:
"Skills: Python (advanced), Git, HTML, CSS"

Request: POST /api/analyze_resume with that PDF and jobRole="Data Science".

Expected:

skills contains at least the four skills.

Python level detected as "advanced".

questions array length between 3 and 5.

At least one question clearly about Python at an advanced level.
TC-02 — Multiple Skills but No Levels Specified

Input:

Resume lists: "Skills: Python, SQL, Git", but no words like “advanced/proficient.”

jobRole omitted.

Expected:

All three skills appear in skills.

Levels default to "intermediate" (or the chosen default rule).

3–5 questions returned.

Questions focus on those three skills.
TC-03 — No Detectable Skills

Input:

Resume mostly about a non-technical job (e.g., “Barista at coffee shop”) with no matching skill keywords in the vocabulary.

jobRole="Data Science".

Expected:

skills: []

questions: []

Frontend shows a message like: “We couldn’t detect technical skills from your resume; please upload a different file or specify a skill manually.”
C2. Optional Judge Test
TC-04 — Judge Endpoint

If a judge module is implemented:

Call POST /agents/judge with a sample payload:
---json
{
  "skill": "python",
  "level": "advanced",
  "question": "Explain the difference between a list and a tuple in Python."
}
Expected:

Response:

{
  "passes": false,
  "violations": ["question_too_basic_for_level"]
}


or similar.

Judge correctly identifies mismatches between declared level and actual difficulty.

Part D — Trace / Prompt Retention

If the judge is enabled, append its verdicts to:

/trace/judge.jsonl

Each line may include:

{
  "timestamp": "2025-11-21T12:00:00Z",
  "skill": "python",
  "level": "advanced",
  "question": "Explain the difference between a list and a tuple in Python.",
  "passes": false,
  "violations": ["question_too_basic_for_level"]
}


If the judge is disabled, this file can be ignored.

(Optionally, a similar trace file could be used to log anonymized resume analysis runs, but that is out-of-scope for the minimal workshop.)


Part E - School assignment requirements
Evaluation Rubric
Category	Weight	Criteria
Business Logic & Value	30%	Clarity of problem, use case relevance, value created
Agentic Execution	30%	Use of LLMs for reasoning, chaining, and explanation
Technical Functionality	25%	Working system, integration of tools, clean interface
Creativity & UX	15%	Innovative interactions, thoughtful interface

---

## Part F — Setup & Installation

### F1. Prerequisites

1. **Python 3.8+** installed
2. **Node.js and npm** for frontend
3. **Ollama** installed and running locally
   - Download from: https://ollama.ai
   - Install following platform-specific instructions
   - Verify installation: `ollama --version`

### F2. Ollama Setup

1. **Install Ollama** (if not already installed):
   ```bash
   # macOS/Linux - download from ollama.ai or use:
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Pull required model**:
   ```bash
   ollama pull llama3.2
   ```
   (Or use another model by configuring `ollama_model` parameter in `ResumeAnalyzer`)

3. **Verify Ollama is running**:
   ```bash
   ollama list
   ```
   Should show the installed model(s).

4. **Note**: Ollama runs as a local service. The backend will automatically detect if it's available and use it. If Ollama is not running, the system will gracefully fall back to manual detection methods.

### F3. Backend Setup

1. **Install Python dependencies**:
   ```bash
   cd backend
   pip install -r ../requirements.txt
   ```

2. **Verify dependencies**:
   - `fastapi`, `uvicorn`, `pdfplumber`, `pydantic`, `ollama` should all be installed

3. **Run backend**:
   ```bash
   python main.py
   # Or use the provided script:
   ../run_backend.sh
   ```

### F4. Frontend Setup

1. **Install Node dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Run frontend**:
   ```bash
   npm run dev
   ```

### F5. Testing AI Integration

1. **Test Ollama connection**:
   ```python
   import ollama
   response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': 'Hello'}])
   print(response)
   ```

2. **Test resume analysis**:
   - Upload a resume PDF via the frontend
   - Verify skills are detected using AI
   - Check that questions are generated dynamically
   - If Ollama is unavailable, verify fallback to question bank works

### F6. Troubleshooting

**Ollama not detected:**
- Ensure Ollama service is running: `ollama serve` (usually runs automatically)
- Check if model is installed: `ollama list`
- Verify Python can connect: Check for connection errors in backend logs

**Slow performance:**
- AI analysis takes longer than manual methods (5-10 seconds typical)
- Consider using a smaller/faster model if needed
- Manual fallback is faster but less accurate

**Questions not personalized:**
- Ensure resume text is being extracted correctly
- Check that AI is actually being used (not falling back)
- Verify Ollama is generating responses (check backend logs)


## Part G — System Prompt for Cursor

Paste this into Cursor before attaching this `spec.md`:

Part G — System Prompt for Cursor

Paste this into Cursor before attaching this spec.md:
"""
SYSTEM
You are an experienced Software Engineer with 5+ years of building rapid prototypes, internal tools, and lightweight product experiences.

Your job is to turn the attached spec (`spec.md`) into a small, functional web app school project. Focus on clarity, simplicity, and fast iteration—not production-grade complexity.

Follow these expectations:

- Treat the spec as the single source of truth.
- Use modern, conventional patterns for both frontend and backend.
- Prefer minimal, readable implementations over generic boilerplate.
- Ask clarifying questions before making assumptions.
- Keep all code easy for students to read and understand.

Build goals:
- Frontend: React.js, 3d.js(would make it really cool)
- Backend: FastAPI (Python)
- AI Integration: Ollama for dynamic skill detection, level inference, and question generation
- Data source: local JSON skill–question bank (`/data/skill_question_bank.json`) - used as reference and fallback
- Required endpoints:
    - GET /api/health
    - POST /api/analyze_resume
- Optional endpoint:
    - POST /agents/judge (may be stubbed or return hard-coded results)

**AI Integration Requirements:**
- System uses Ollama (local LLM) for:
  - Dynamic skill detection from resume text
  - Context-aware proficiency level inference
  - Personalized question generation based on resume content
- Graceful fallback to manual methods if Ollama unavailable
- Question bank serves as reference examples for AI and fallback source

Workflow:
1. Read the spec fully.
2. Summarize and confirm the architecture in simple bullets.
3. Scaffold the project folder structure.
4. Implement the required APIs and a simple React UI:
    - Upload a resume PDF.
    - Optional text input for job role.
    - Display detected skills and 3–5 generated interview questions.
5. (Optional) Add a judge endpoint and trace logging to `/trace/judge.jsonl`.

6. After each major step, output exactly two sections:
   WHAT I DID
   WHAT I NEED NEXT


   END OF SPEC
  """