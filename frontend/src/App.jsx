// frontend/src/App.jsx
import React from 'react';
import ShortenerForm from './ShortenerForm.jsx'; // Assuming your form is here

function App() {
  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>⚡️ Dockerized URL Shortener</h1>
      <ShortenerForm />
    </div>
  );
}
export default App;