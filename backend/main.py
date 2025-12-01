from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
import sys
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from resume_analyzer import ResumeAnalyzer

app = FastAPI(title="Resume Interviewer API")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analyzer
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
QUESTION_BANK_PATH = DATA_DIR / "skill_question_bank.json"

analyzer = ResumeAnalyzer(str(QUESTION_BANK_PATH))


class HealthResponse(BaseModel):
    status: str
    message: str


class DetectedSkill(BaseModel):
    name: str
    key: str
    level: str


class InterviewQuestion(BaseModel):
    skill: str
    level: str
    question: str


class AnalyzeResponse(BaseModel):
    skills: List[DetectedSkill]
    questions: List[InterviewQuestion]
    qa_summary: Optional[dict] = None


class RefreshQuestionRequest(BaseModel):
    skill: str
    level: str
    exclude_question: Optional[str] = None
    resume_text: Optional[str] = None


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Resume Interviewer API is running"}


@app.post("/api/analyze_resume", response_model=AnalyzeResponse)
async def analyze_resume(
    resumeFile: UploadFile = File(...),
    jobRole: Optional[str] = Form(None)
):
    """
    Analyze a resume PDF and generate interview questions.
    
    - **resumeFile**: PDF file containing the resume
    - **jobRole**: Optional job role to bias skill detection (e.g., "Data Science")
    """
    try:
        # Validate file type
        if not resumeFile.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Read file content
        file_content = await resumeFile.read()
        
        # Analyze resume
        result = analyzer.analyze(file_content, job_role=jobRole)
        
        return AnalyzeResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing resume: {str(e)}")


@app.post("/agents/judge")
async def judge_question(
    skill: str,
    level: str,
    question: str,
    resumeSnippet: Optional[str] = None
):
    """
    Judge whether a question is appropriate for the given skill and level.
    This is a simplified stub implementation.
    """
    # Simple heuristic-based judge (can be replaced with LLM)
    violations = []
    
    # Check if question mentions the skill
    skill_lower = skill.lower()
    question_lower = question.lower()
    
    if skill_lower not in question_lower and skill_lower.replace(" ", "") not in question_lower.replace(" ", ""):
        violations.append("question_does_not_mention_skill")
    
    # Check level appropriateness (simplified)
    beginner_keywords = ["what is", "explain", "difference between", "how do you"]
    advanced_keywords = ["optimize", "implement", "design", "architecture", "complex"]
    
    if level == "beginner" and any(kw in question_lower for kw in advanced_keywords):
        violations.append("question_too_advanced_for_level")
    elif level == "advanced" and all(kw not in question_lower for kw in advanced_keywords):
        if not any(kw in question_lower for kw in ["how would you", "describe how"]):
            violations.append("question_too_basic_for_level")
    
    passes = len(violations) == 0
    
    # Log to trace file
    trace_dir = BASE_DIR / "trace"
    trace_dir.mkdir(exist_ok=True)
    trace_file = trace_dir / "judge.jsonl"
    
    import datetime
    trace_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "skill": skill,
        "level": level,
        "question": question,
        "passes": passes,
        "violations": violations
    }
    
    with open(trace_file, "a") as f:
        f.write(json.dumps(trace_entry) + "\n")
    
    return {
        "passes": passes,
        "violations": violations
    }


@app.post("/api/refresh_question", response_model=InterviewQuestion)
async def refresh_question(request: RefreshQuestionRequest):
    """
    Generate a fresh question for a specific skill and level.
    
    - **skill**: The skill key (e.g., "python")
    - **level**: The proficiency level (beginner/intermediate/advanced)
    - **exclude_question**: Optional current question to exclude from results
    - **resume_text**: Optional resume text snippet for AI generation
    """
    try:
        fresh_question = analyzer.get_fresh_question(
            skill_key=request.skill,
            level=request.level,
            exclude_question=request.exclude_question,
            resume_text=request.resume_text
        )
        
        if not fresh_question:
            raise HTTPException(
                status_code=404,
                detail=f"No questions available for skill '{request.skill}' at level '{request.level}'"
            )
        
        return InterviewQuestion(**fresh_question)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing question: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

