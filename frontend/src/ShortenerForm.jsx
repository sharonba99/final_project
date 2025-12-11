// frontend/src/ShortenerForm.jsx
import React, { useState } from 'react';
import axios from 'axios';

// CRITICAL: Use the Vite environment variable name
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

function ShortenerForm() {
  const [longUrl, setLongUrl] = useState('');
  const [shortCode, setShortCode] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setShortCode('');

    try {
      const fullUrl = `${API_BASE_URL}/api/shorten`;
      
      const response = await axios.post(fullUrl, { url: longUrl });
      
      // Assuming successful return is the short code
      // Adjust the host URL to your external access point (localhost:80 or domain)
      setShortCode(`http://localhost/${response.data.short_code}`);
    } catch (error) {
      console.error('Error shortening URL:', error);
      setShortCode('Error: Failed to shorten URL.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ marginTop: '20px' }}>
      <form onSubmit={handleSubmit} style={{ display: 'flex', justifyContent: 'center', gap: '10px' }}>
        <input 
          type="url" 
          value={longUrl} 
          onChange={(e) => setLongUrl(e.target.value)} 
          placeholder="Enter a long URL here"
          required 
          disabled={loading}
          style={{ padding: '10px', width: '400px', border: '1px solid #ccc' }}
        />
        <button type="submit" disabled={loading} style={{ padding: '10px 20px', cursor: 'pointer' }}>
          {loading ? 'Shortening...' : 'Shorten'}
        </button>
      </form>

      {shortCode && (
        <div style={{ marginTop: '20px', color: shortCode.startsWith('Error') ? 'red' : 'green' }}>
          <p>
            **Result:** <a href={shortCode} target="_blank" rel="noopener noreferrer">
              {shortCode}
            </a>
          </p>
        </div>
      )}
    </div>
  );
}

export default ShortenerForm;