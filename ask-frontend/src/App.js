import { useState } from 'react';
import './App.css';

const serverUrl = 'http://127.0.0.1:5000/api';

function App() {
  const [chatMessages, setChatMessages] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) {
      setError('Please select a PDF file to upload.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setChatMessages([]); // Clear chat when new document is uploaded

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
      setSessionId(data.session_id);
      // Add initial message about document upload
      setChatMessages([{
        role: 'assistant',
        content: `I've analyzed your document "${file.name}". You can now ask me questions about it!`
      }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!currentQuestion.trim() || !sessionId) return;

    setIsLoading(true);
    const userMessage = currentQuestion.trim();
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setCurrentQuestion('');

    try {
      const response = await fetch(`${serverUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          question: userMessage
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get response from chatbot');
      }

      const data = await response.json();
      setChatMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <div className="container">
        <h1>ASK - Chat with Your Document</h1>
        
        {!sessionId && (
          <div className="upload-section">
            <h2>Upload a PDF to start chatting</h2>
            <input 
              type="file" 
              id="pdf-file" 
              accept=".pdf"
              onChange={handleFileUpload}
              disabled={isLoading}
            />
          </div>
        )}

        {error && <div className="error-message">{error}</div>}
        
        {isLoading && <div className="loading">Processing...</div>}

        {sessionId && (
          <div className="chat-section">
            <div className="chat-messages">
              {chatMessages.map((message, index) => (
                <div key={index} className={`message ${message.role}`}>
                  {message.content}
                </div>
              ))}
              {isLoading && <div className="loading">Thinking...</div>}
            </div>
            <form onSubmit={handleChatSubmit} className="chat-input-form">
              <input
                type="text"
                value={currentQuestion}
                onChange={(e) => setCurrentQuestion(e.target.value)}
                placeholder="Ask a question about the document..."
                disabled={isLoading}
              />
              <button type="submit" disabled={isLoading}>Send</button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
