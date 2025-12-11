// frontend/test-render.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';

// This is the simplest possible component
function TestApp() {
    return (
        <div style={{ padding: '50px', backgroundColor: 'tomato', color: 'white' }}>
            <h1>HELLO WORLD SUCCESS!</h1>
        </div>
    );
}

// Render the component
const container = document.getElementById('root');
if (container) {
    ReactDOM.createRoot(container).render(
        <TestApp />
    );
}