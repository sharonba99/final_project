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
    
    let cleanUrl = url.trim();
    if (!/^https?:\/\//i.test(cleanUrl)) {
      cleanUrl = `https://${cleanUrl}`;
    }

    setLoading(true)

    try {
    const res = await fetch(`${API_BASE}/shorten`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ long_url: cleanUrl })
    });

    // Handle different response scenarios
    if (!res.ok) {
      const errorData = await res.json();
      
      // Send error if the URL format is invalid
      if (res.status === 400) {
        throw new Error("Invalid URL. Please check the format.");
      }
      
      throw new Error(errorData.error || 'Something went wrong');
    }

    const data = await res.json();
    setCode(data.short_code);
    
  } catch (err) {
    console.error(err);
    // If the error message is specifically from our logic, show it.
    // Otherwise, assume the backend is down.
    if (err.message === "Invalid URL. Please check the format.") {
        setError(err.message);
    } else {
        setError('Service unavailable. Is the backend running?');
    }
  } finally {
    setLoading(false);
  }
};

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
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="google.com"
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
              <span className="short-link">{code}</span>
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