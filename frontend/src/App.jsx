import { useState } from 'react'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('query')
  
  // Query state
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  
  // Compliance state
  const [sopText, setSopText] = useState('')
  const [complianceLoading, setComplianceLoading] = useState(false)
  const [complianceResult, setComplianceResult] = useState(null)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const response = await fetch('http://localhost:8080/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: query })
      })
      const data = await response.json()
      setResult(data)
    } catch (error) {
      setResult({ answer: "Failed to connect to backend. Make sure FastAPI is running on port 8080." })
    }
    setLoading(false)
  }

  const handleCompliance = async (e) => {
    e.preventDefault()
    if (!sopText.trim()) return
    setComplianceLoading(true)
    setComplianceResult(null)
    try {
      const response = await fetch('http://localhost:8080/compliance-check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sop_text: sopText })
      })
      const data = await response.json()
      setComplianceResult(data)
    } catch (error) {
      setComplianceResult({ status: "ERROR", explanation: "Failed to connect to backend." })
    }
    setComplianceLoading(false)
  }

  return (
    <div className="dashboard-container">
      <header className="header">
        <h1>Unified Asset & Operations Brain</h1>
        <p className="subtitle">Industrial Knowledge Intelligence Platform</p>
      </header>

      <nav className="tab-nav glass-panel">
        <button 
          className={`tab-btn ${activeTab === 'query' ? 'active' : ''}`}
          onClick={() => setActiveTab('query')}
        >
          <span className="tab-icon">🔍</span> Knowledge Query
        </button>
        <button 
          className={`tab-btn ${activeTab === 'compliance' ? 'active' : ''}`}
          onClick={() => setActiveTab('compliance')}
        >
          <span className="tab-icon">✅</span> Compliance Check
        </button>
      </nav>

      <main className="main-content">
        {activeTab === 'query' && (
          <>
            <div className="search-section glass-panel fade-in">
              <h2 className="section-title">Ask the Knowledge Base</h2>
              <p className="section-desc">Query equipment specs, OISD regulations, or SOP procedures</p>
              <form onSubmit={handleSearch} className="search-form">
                <input 
                  type="text" 
                  id="search-input"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="e.g. What is the H2S limit for confined space entry?"
                  className="search-input"
                />
                <button type="submit" id="search-btn" className="search-button" disabled={loading}>
                  {loading ? (
                    <span className="spinner"></span>
                  ) : 'Search'}
                </button>
              </form>
            </div>

            {result && (
              <div className="result-section glass-panel fade-in">
                <h2>Results</h2>
                {result.answer.split('---').map((section, i) => (
                  <div key={i} className="answer-box" style={{ marginBottom: '0.8rem' }}>
                    {section.trim().split('\n').map((line, j) => (
                      <p key={j} style={{ margin: '0.3rem 0' }}>{line}</p>
                    ))}
                  </div>
                ))}
                {result.citations && result.citations.length > 0 && (
                  <div className="citations">
                    <h3>📄 Sources</h3>
                    <div className="citation-chips">
                      {result.citations.map((c, i) => (
                        <span key={i} className="citation-chip">{c.source || c}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {activeTab === 'compliance' && (
          <>
            <div className="search-section glass-panel fade-in">
              <h2 className="section-title">SOP Compliance Checker</h2>
              <p className="section-desc">Paste an SOP excerpt to check against OISD regulations</p>
              <form onSubmit={handleCompliance} className="compliance-form">
                <textarea 
                  id="sop-input"
                  value={sopText}
                  onChange={(e) => setSopText(e.target.value)}
                  placeholder="Paste SOP text here... e.g. 'Confined space H2S limit is set to 15 ppm TWA for entry procedures'"
                  className="sop-textarea"
                  rows={5}
                />
                <button type="submit" id="compliance-btn" className="search-button" disabled={complianceLoading}>
                  {complianceLoading ? (
                    <span className="spinner"></span>
                  ) : 'Check Compliance'}
                </button>
              </form>
            </div>

            {complianceResult && (
              <div className={`result-section glass-panel fade-in ${complianceResult.status === 'COMPLIANT' ? 'compliant' : 'non-compliant'}`}>
                <div className="compliance-header">
                  <span className={`status-badge ${complianceResult.status === 'COMPLIANT' ? 'badge-green' : 'badge-red'}`}>
                    {complianceResult.status === 'COMPLIANT' ? '✅' : '🚨'} {complianceResult.status}
                  </span>
                </div>
                <div className="answer-box">
                  <p>{complianceResult.explanation}</p>
                </div>
              </div>
            )}
          </>
        )}
      </main>
      
      <footer className="footer">
        <p>Powered by ChromaDB · HuggingFace · spaCy · FastAPI</p>
      </footer>

      <div className="background-decorations">
        <div className="blob blob-1"></div>
        <div className="blob blob-2"></div>
      </div>
    </div>
  )
}

export default App
