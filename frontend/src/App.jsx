import { useState } from 'react'
import './App.css'

const API_BASE = 'http://localhost:5000'

function App() {
  const [url, setUrl] = useState('')
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Reset state
    setError(null)
    setCode('')
    setCopied(false)
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/shorten`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ long_url: url })
      })

      if (!res.ok) throw new Error('API Error')

      const data = await res.json()
      
      // Store only the short code for display
      setCode(data.short_code)
      
    } catch (err) {
      console.error(err)
      setError('Service unavailable. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    if (!code) return
    
    // Construct the full URL only when copying
    const fullLink = `${API_BASE}/${code}`
    navigator.clipboard.writeText(fullLink)
    
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="container">
      <div className="card">
        <h1>Make it Short.</h1>
        <p className="subtitle">
          Paste your long, messy link below and we'll handle the rest.
        </p>
        
        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://..."
              required
            />
          </div>
          
          <button type="submit" className="primary-btn" disabled={loading}>
            {loading ? 'Processing...' : 'Shorten URL 🚀'}
          </button>
        </form>

        {error && <div className="error-msg">{error}</div>}

        {code && (
          <div className="result-card">
            <div className="label">Here's your new link:</div>
            
            <div className="link-display">
              {/* Display: Just the clean code */}
              <span className="short-link">{code}</span>
              
              {/* Action: Copies the full working URL */}
              <button onClick={handleCopy} className="copy-btn">
                {copied ? 'Copied!' : 'Copy Link'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App