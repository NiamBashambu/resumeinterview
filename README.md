# Resume Interviewer

A web application that analyzes resumes and generates personalized interview questions based on detected technical skills.

## Features

- 📄 **PDF Resume Upload**: Upload and analyze PDF resumes
- 🔍 **Skill Detection**: Automatically detects technical skills from resume text
- 📊 **Skill Level Inference**: Determines proficiency levels (beginner/intermediate/advanced)
- ❓ **Question Generation**: Generates 3-5 personalized interview questions
- 🎨 **3D Visualization**: Interactive 3D visualization of detected skills using Three.js
- 🎯 **Job Role Filtering**: Optional job role input to prioritize relevant skills

## Project Structure

```
resumeinterview/
├── backend/           # FastAPI backend
│   ├── main.py       # API endpoints
│   └── resume_analyzer.py  # Core analysis logic
├── frontend/         # React frontend
│   └── src/
│       ├── components/
│       │   ├── ResumeUploader.jsx
│       │   ├── ResultsDisplay.jsx
│       │   └── SkillVisualization.jsx
│       └── App.jsx
├── data/
│   └── skill_question_bank.json  # Question bank
└── trace/            # Judge trace logs (optional)
```

## Setup Instructions

### Backend Setup

1. Navigate to the project root directory:
   ```bash
   cd resumeinterview
   ```

2. Create a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the backend server (from project root):
   ```bash
   python -m uvicorn backend.main:app --reload --port 8000
   ```

   Or use the provided script:
   ```bash
   ./run_backend.sh
   ```

   The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

## API Endpoints

### GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "Resume Interviewer API is running"
}
```

### POST /api/analyze_resume
Analyze a resume PDF and generate interview questions.

**Request:**
- `resumeFile`: PDF file (multipart/form-data)
- `jobRole`: Optional string (e.g., "Data Science")

**Response:**
```json
{
  "skills": [
    {
      "name": "Python",
      "key": "python",
      "level": "advanced"
    }
  ],
  "questions": [
    {
      "skill": "python",
      "level": "advanced",
      "question": "Describe how you would optimize a slow Python data pipeline..."
    }
  ]
}
```

### POST /agents/judge
Judge whether a question is appropriate (optional endpoint).

**Request:**
```json
{
  "skill": "python",
  "level": "advanced",
  "question": "...",
  "resumeSnippet": "..."
}
```

## Usage

1. Start both backend and frontend servers (see Setup Instructions above)
2. Open `http://localhost:5173` in your browser
3. Upload a PDF resume
4. Optionally enter a job role
5. Click "Analyze Resume"
6. View detected skills and generated interview questions

## Technologies

- **Backend**: FastAPI, pdfplumber, Python
- **Frontend**: React, Vite, Three.js, @react-three/fiber
- **Data**: JSON-based skill-question bank

## Notes

- The application expects PDF files with extractable text (not scanned images)
- Skills are detected using a vocabulary-based matching system
- Question generation uses a local JSON question bank
- The judge endpoint uses heuristic-based validation (can be extended with LLM)

## Development

To modify the skill-question bank, edit `data/skill_question_bank.json`. The format is:

```json
[
  {
    "skill": "python",
    "displayName": "Python",
    "levels": {
      "beginner": ["question 1", "question 2"],
      "intermediate": ["question 1", "question 2"],
      "advanced": ["question 1", "question 2"]
    }
  }
]
```

