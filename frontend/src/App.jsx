import { useState } from 'react'
import './App.css'
import ResumeUploader from './components/ResumeUploader'
import ResultsDisplay from './components/ResultsDisplay'
import SkillVisualization from './components/SkillVisualization'

function App() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleAnalysis = async (formData) => {
    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const response = await fetch('http://localhost:8000/api/analyze_resume', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to analyze resume')
      }

      const data = await response.json()
      setResults(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRefreshQuestion = async (questionIndex, skill, level, currentQuestion) => {
    try {
      const response = await fetch('http://localhost:8000/api/refresh_question', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          skill,
          level,
          exclude_question: currentQuestion,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to refresh question')
      }

      const newQuestion = await response.json()
      
      // Update the specific question in results
      setResults((prevResults) => {
        if (!prevResults || !prevResults.questions) return prevResults
        
        const updatedQuestions = [...prevResults.questions]
        updatedQuestions[questionIndex] = newQuestion
        
        return {
          ...prevResults,
          questions: updatedQuestions,
        }
      })
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Resume Interviewer</h1>
        <p>Upload your resume to get personalized interview questions</p>
      </header>

      <main className="app-main">
        <div className="upload-section">
          <ResumeUploader 
            onAnalyze={handleAnalysis} 
            loading={loading}
          />
        </div>

        {error && (
          <div className="error-message">
            <p>Error: {error}</p>
          </div>
        )}

        {results && (
          <div className="results-section">
            <SkillVisualization skills={results.skills} />
            <ResultsDisplay 
              results={results} 
              onRefreshQuestion={handleRefreshQuestion}
            />
          </div>
        )}
      </main>
    </div>
  )
}

export default App

