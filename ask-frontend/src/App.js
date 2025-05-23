import { useState } from 'react';
import './App.css';

const serverUrl = 'http://127.0.0.1:5000/api';

function App() {
  const [summary, setSummary] = useState('');
  const [keywords, setKeywords] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) {
      setError('Please select a PDF file to upload.');
      return;
    }

    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${serverUrl}/analyze_pdf`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Failed to analyze PDF');
      }

      const data = await response.json();
      setSummary(data.summary);
      setKeywords(data.keywords);
      setQuestions(data.questions);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <div className="container">
        <h1>ASK - Your Scholar AI Assistant</h1>
        
        <div className="input-container">
          <input 
            type="file" 
            id="pdf-file" 
            accept=".pdf"
            onChange={handleFileUpload}
            disabled={isLoading}
          />
        </div>

        {error && <div className="error-message">{error}</div>}
        
        {isLoading && <div className="loading">Analyzing your document...</div>}

        <div className="output-container">
          {summary && (
            <div className="summary-section">
              <h2>Summary</h2>
              <p>{summary}</p>
            </div>
          )}

          {keywords.length > 0 && (
            <div className="keywords-section">
              <h2>Keywords</h2>
              <ul>
                {keywords.map((keyword, index) => (
                  <li key={index}>{keyword}</li>
                ))}
              </ul>
            </div>
          )}

          {questions.length > 0 && (
            <div className="questions-section">
              <h2>Questions</h2>
              <ul>
                {questions.map((question, index) => (
                  <li key={index}>{question}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
