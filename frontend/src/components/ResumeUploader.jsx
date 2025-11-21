import { useState } from 'react'
import './ResumeUploader.css'

function ResumeUploader({ onAnalyze, loading }) {
  const [file, setFile] = useState(null)
  const [jobRole, setJobRole] = useState('')
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile.type === 'application/pdf') {
        setFile(droppedFile)
      } else {
        alert('Please upload a PDF file')
      }
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    if (!file) {
      alert('Please select a PDF file')
      return
    }

    const formData = new FormData()
    formData.append('resumeFile', file)
    if (jobRole.trim()) {
      formData.append('jobRole', jobRole.trim())
    }

    onAnalyze(formData)
  }

  return (
    <form onSubmit={handleSubmit} className="uploader-form">
      <div
        className={`file-drop-zone ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-input"
          accept=".pdf"
          onChange={handleFileChange}
          className="file-input"
        />
        <label htmlFor="file-input" className="file-label">
          {file ? (
            <div className="file-selected">
              <span className="file-icon">📄</span>
              <span className="file-name">{file.name}</span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  setFile(null)
                }}
                className="remove-file"
              >
                ×
              </button>
            </div>
          ) : (
            <div className="file-placeholder">
              <span className="upload-icon">📤</span>
              <p>Drag & drop your resume PDF here</p>
              <p className="upload-hint">or click to browse</p>
            </div>
          )}
        </label>
      </div>

      <div className="job-role-input">
        <label htmlFor="job-role">Job Role (Optional)</label>
        <input
          type="text"
          id="job-role"
          value={jobRole}
          onChange={(e) => setJobRole(e.target.value)}
          placeholder="e.g., Data Science, Software Engineer"
          className="job-role-field"
        />
      </div>

      <button
        type="submit"
        disabled={!file || loading}
        className="analyze-button"
      >
        {loading ? 'Analyzing...' : 'Analyze Resume'}
      </button>
    </form>
  )
}

export default ResumeUploader

