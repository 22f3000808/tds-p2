// p2.jsx
import React, { useState } from 'react';
import './App.css'; // Assuming you have a CSS file for styling

const P2 = () => {
  const [inputText, setInputText] = useState('');
  const [outputText, setOutputText] = useState('');

//   const handleAnalyse = async () => {
//     try {
//       const response = await fetch('http://localhost:8000/api/', {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({ query: inputText }),
//       });
//       const data = await response.json();
//       setOutputText(data.result || 'No output');
//     } catch (err) {
//       console.error(err);
//       setOutputText('Error connecting to backend');
//     }
//   };


const handleAnalyse = async () => {
  try {
    const formData = new FormData();
    formData.append("query", inputText);

    const response = await fetch('https://tds-p2-xn6o.onrender.com/api/', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    // Display structured output or error message
    if (data.topic || data.summary || data.sources) {
      setOutputText(JSON.stringify(data, null, 2));
    } else if (data.error) {
      setOutputText("Error: " + data.error + "\n" + JSON.stringify(data.raw, null, 2));
    } else {
      setOutputText('Unexpected response from backend');
    }

  } catch (err) {
    console.error(err);
    setOutputText('Error connecting to backend');
  }
};


  return (
    <div className="container">
      <h1>Data Analyst Agent</h1>
      <label>input txt box</label>
      <textarea
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        className="textbox"
        rows="5"
      ></textarea>

      <label>output textbox</label>
      <textarea
        value={outputText}
        readOnly
        className="textbox"
        rows="5"
      ></textarea>

      <button onClick={handleAnalyse}>analyse</button>
    </div>
  );
};

export default P2;
