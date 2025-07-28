// // p2.jsx
// import React, { useState } from 'react';
// import './App.css'; // Assuming you have a CSS file for styling

// const P2 = () => {
//   const [inputText, setInputText] = useState('');
//   const [outputText, setOutputText] = useState('');

// //   const handleAnalyse = async () => {
// //     try {
// //       const response = await fetch('http://localhost:8000/api/', {
// //         method: 'POST',
// //         headers: {
// //           'Content-Type': 'application/json',
// //         },
// //         body: JSON.stringify({ query: inputText }),
// //       });
// //       const data = await response.json();
// //       setOutputText(data.result || 'No output');
// //     } catch (err) {
// //       console.error(err);
// //       setOutputText('Error connecting to backend');
// //     }
// //   };


// const handleAnalyse = async () => {
//   try {
//     const formData = new FormData();
//     formData.append("query", inputText);

//     const response = await fetch('https://tds-p2-xn6o.onrender.com/api/', {
//       method: 'POST',
//       body: formData
//     });

//     const data = await response.json();

//     // Display structured output or error message
//     if (data.topic || data.summary || data.sources) {
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


//   return (
//     <div className="container">
//       <h1>Data Analyst Agent</h1>
//       <label>input txt box</label>
//       <textarea
//         value={inputText}
//         onChange={(e) => setInputText(e.target.value)}
//         className="textbox"
//         rows="5"
//       ></textarea>

//       <label>output textbox</label>
//       <textarea
//         value={outputText}
//         readOnly
//         className="textbox"
//         rows="5"
//       ></textarea>

//       <button onClick={handleAnalyse}>analyse</button>
//     </div>
//   );
// };

// export default P2;




// import React, { useState, useRef, useEffect } from 'react';
// import './App.css'; // Ensure styles below are added to App.css

// const P2 = () => {
//   const [inputText, setInputText] = useState('');
//   const [outputText, setOutputText] = useState('');
//   const textareaRef = useRef(null);

//   // Auto expand input textarea
//   useEffect(() => {
//     if (textareaRef.current) {
//       textareaRef.current.style.height = "auto";
//       textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
//     }
//   }, [inputText]);

//   const handleAnalyse = async () => {
//     try {
//       const formData = new FormData();
//       formData.append("query", inputText);

//       const response = await fetch('https://tds-p2-xn6o.onrender.com/api/', {
//         method: 'POST',
//         body: formData
//       });

//       const data = await response.json();

//       if (data.topic || data.summary || data.sources) {
//         setOutputText(JSON.stringify(data, null, 2));
//       } else if (data.error) {
//         setOutputText("Error: " + data.error + "\n" + JSON.stringify(data.raw, null, 2));
//       } else {
//         setOutputText('Unexpected response from backend');
//       }

//     } catch (err) {
//       console.error(err);
//       setOutputText('Error connecting to backend');
//     }
//   };

//   return (
//     <div className="main-container">
//       <h1 className="heading">
//         Data 
//         Analyst 
//         Agent
//         </h1>
//       <div className="content-box">
//         <div className="input-section">
//           <label>Enter your query</label>
//           <textarea
//             ref={textareaRef}
//             value={inputText}
//             onChange={(e) => setInputText(e.target.value)}
//             className="input-textarea"
//             rows="3"
//             placeholder="Type your question here..."
//           ></textarea>
//           <button onClick={handleAnalyse} className="analyze-button">Analyze</button>
//         </div>

//         <div className="output-section">
//           <label>Output</label>
//           <textarea
//             value={outputText}
//             readOnly
//             className="output-textarea"
//             rows="5"
//           ></textarea>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default P2;


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

  const handleAnalyse = async () => {
    try {
      const formData = new FormData();
      formData.append("query", inputText);

      const response = await fetch('https://tds-p2-xn6o.onrender.com/api/', {
      // const response = await fetch('http://0.0.0.0:8000/api/', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

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
