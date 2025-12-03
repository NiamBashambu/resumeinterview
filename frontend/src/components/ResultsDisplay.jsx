import { useState } from 'react'
import './ResultsDisplay.css'

function ResultsDisplay({ results, onRefreshQuestion }) {
  const [refreshingIndex, setRefreshingIndex] = useState(null)
  const [showSolutions, setShowSolutions] = useState({})

  if (!results || (!results.skills?.length && !results.questions?.length)) {
    return (
      <div className="results-container">
        <div className="no-results">
          <p>No skills detected. Please upload a resume with technical skills listed.</p>
        </div>
      </div>
    )
  }

  const handleRefresh = async (index, question) => {
    setRefreshingIndex(index)
    try {
      await onRefreshQuestion(index, question.skill, question.level, question.question)
    } finally {
      setRefreshingIndex(null)
    }
  }

  return (
    <div className="results-container">
      <div className="skills-section">
        <h2>Detected Skills</h2>
        {results.skills && results.skills.length > 0 ? (
          <div className="skills-list">
            {results.skills.map((skill, index) => (
              <div key={index} className={`skill-badge skill-${skill.level}`}>
                <span className="skill-name">{skill.name}</span>
                <span className="skill-level">{skill.level}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="no-skills">No skills detected</p>
        )}
      </div>

      <div className="questions-section">
        <h2>Interview Questions</h2>
        {results.questions && results.questions.length > 0 ? (
          <div className="questions-list">
            {results.questions.map((question, index) => (
              <div key={index} className="question-card">
                <div className="question-header">
                  <span className="question-number">{index + 1}</span>
                  <span className="question-skill">{question.skill}</span>
                  <span className={`question-level question-level-${question.level}`}>
                    {question.level}
                  </span>
                  {onRefreshQuestion && (
                    <button
                      className="refresh-button"
                      onClick={() => handleRefresh(index, question)}
                      disabled={refreshingIndex === index}
                      title="Refresh question"
                      aria-label="Refresh question"
                    >
                      {refreshingIndex === index ? (
                        <span className="refresh-spinner">⟳</span>
                      ) : (
                        <span className="refresh-icon">⟳</span>
                      )}
                    </button>
                  )}
                </div>
                <p className="question-text">{question.question}</p>
                {question.solution && (
                  <div className="solution-section">
                    <button
                      className="solution-toggle"
                      onClick={() => setShowSolutions(prev => ({
                        ...prev,
                        [index]: !prev[index]
                      }))}
                      aria-expanded={showSolutions[index] || false}
                    >
                      {showSolutions[index] ? (
                        <>
                          <span className="solution-icon">▼</span>
                          <span>Hide Solution</span>
                        </>
                      ) : (
                        <>
                          <span className="solution-icon">▶</span>
                          <span>Show Solution</span>
                        </>
                      )}
                    </button>
                    {showSolutions[index] && (
                      <div className="solution-content">
                        <h4 className="solution-title">Sample Solution:</h4>
                        <div className="solution-text">
                          {question.solution.split('\n').map((line, idx) => 
                            line.trim() ? (
                              <p key={idx}>{line.trim()}</p>
                            ) : (
                              <br key={idx} />
                            )
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="no-questions">No questions generated</p>
        )}
      </div>

      {results.qa_summary && (
        <div className="qa-summary">
          <h3>Quality Assurance</h3>
          <p>Total Questions: {results.qa_summary.total}</p>
          <p>Passed: {results.qa_summary.passed}</p>
        </div>
      )}
    </div>
  )
}

export default ResultsDisplay

