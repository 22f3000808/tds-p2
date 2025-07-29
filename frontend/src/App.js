


import React, { useState, useRef, useEffect } from 'react';
import './App.css';

const P2 = () => {
  const [inputText, setInputText] = useState('');
  const [outputText, setOutputText] = useState('');
  const inputRef = useRef(null);
  const outputRef = useRef(null);

  // Auto expand input textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = `${inputRef.current.scrollHeight}px`;
    }
  }, [inputText]);

  // Auto expand output textarea
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.style.height = "auto";
      outputRef.current.style.height = `${outputRef.current.scrollHeight}px`;
    }
  }, [outputText]);

  // const handleAnalyse = async () => {
  //   try {
  //     const formData = new FormData();
  //     formData.append("query", inputText);

  //     const response = await fetch('https://tds-p2-xn6o.onrender.com/api/', {
  //     // const response = await fetch('http://0.0.0.0:8000/api/', {
  //       method: 'POST',
  //       body: formData
  //     });

  //     const data = await response.json();

  //     // if (data.topic || data.summary || data.sources) {
  //     if (data) {
  //       setOutputText(JSON.stringify(data, null, 2));
  //     } else if (data.error) {
  //       setOutputText("Error: " + data.error + "\n" + JSON.stringify(data.raw, null, 2));
  //     } else {
  //       setOutputText('Unexpected response from backend');
  //     }

  //   } catch (err) {
  //     console.error(err);
  //     setOutputText('Error connecting to backend');
  //   }
  // };

  const handleAnalyse = async () => {
  try {
    const formData = new FormData();
    formData.append("query", inputText);

    const response = await fetch('https://tds-p2-xn6o.onrender.com/api/', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (data.error) {
      setOutputText("Error: " + data.error + "\n" + JSON.stringify(data.raw, null, 2));
    } else {
      const isString = typeof data === 'string';
      setOutputText(isString ? data : JSON.stringify(data, null, 2));
    }

  } catch (err) {
    console.error(err);
    setOutputText('Error connecting to backend');
  }
};


  return (
    <div className="main-container">
      <h1 className="top-heading">Data Analyst Agent</h1>
      <div className="content-box">
        <div className="input-section">
          <label className='input-label'>Enter your query</label>
          <textarea
            ref={inputRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className="input-textarea"
            rows="3"
            placeholder="Type your question here..."
          ></textarea>
          <button onClick={handleAnalyse} className="analyze-button">Analyze</button>
        </div>

        <div className="output-section">
          <label className='output-label'>Output</label>
          <textarea
            ref={outputRef}
            value={outputText}
            readOnly
            className="output-textarea"
            rows="3"
          ></textarea>
        </div>
      </div>
    </div>
  );
};

export default P2;
