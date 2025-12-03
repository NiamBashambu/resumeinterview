import { useState } from 'react'
import './LandingPage.css'

function LandingPage({ onSelectPersona }) {
  const [selectedPersona, setSelectedPersona] = useState(null)

  const personas = [
    {
      id: 'employers',
      title: 'Employers',
      description: 'Upload resumes to analyze candidate skills and generate interview questions',
      icon: '👔',
      color: '#667eea'
    },
    {
      id: 'job-seekers',
      title: 'Job Seekers',
      description: 'Upload your resume to get personalized interview questions and skill analysis',
      icon: '👤',
      color: '#764ba2'
    }
  ]

  const handlePersonaSelect = (personaId) => {
    setSelectedPersona(personaId)
    setTimeout(() => {
      onSelectPersona(personaId)
    }, 300) // Small delay for smooth transition
  }

  return (
    <div className="landing-page">
      <div className="landing-content">
        <div className="landing-header">
          <h1 className="landing-title">Resume Interviewer</h1>
          <p className="landing-subtitle">Choose your role to get started</p>
        </div>

        <div className="platform-description">
          <p className="description-text">
            Resume Interviewer uses AI to analyze resumes, detect technical skills, and generate 
            personalized interview questions tailored to each candidate's experience level. 
            Whether you're preparing for interviews or evaluating candidates, get intelligent 
            insights to make better hiring decisions.
          </p>
        </div>

        <div className="personas-grid">
          {personas.map((persona) => (
            <div
              key={persona.id}
              className={`persona-card ${selectedPersona === persona.id ? 'selected' : ''}`}
              onClick={() => handlePersonaSelect(persona.id)}
              style={{ '--persona-color': persona.color }}
            >
              <div className="persona-icon">{persona.icon}</div>
              <h2 className="persona-title">{persona.title}</h2>
              <p className="persona-description">{persona.description}</p>
              <div className="persona-arrow">→</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default LandingPage

