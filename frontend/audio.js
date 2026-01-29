// // frontend/audio.js
// let audioContext = null;
// let processor = null;
// let source = null;
// let stream = null;
// let isRunning = false;
// let sessionId = null;
// let silenceTimeout;

// // Buttons
// const resumeInput = document.getElementById("resumeFile");
// const startBtn = document.getElementById("startBtn");
// const stopBtn = document.getElementById("stopBtn");
// const submitBtn = document.getElementById("submitBtn");

// // Enable start button after file selection
// resumeInput.addEventListener("change", () => {
//   startBtn.disabled = false;
// });

// // Upload resume & create session
// async function uploadResume() {
//   const file = resumeInput.files[0];
//   if (!file) return null;

//   const formData = new FormData();
//   formData.append("file", file);

//   // JD manually set
//   const job_description = "Python Developer"; 
//   formData.append("job_description", job_description);

//   const response = await fetch("http://localhost:8000/upload_resume", {
//     method: "POST",
//     body: formData
//   });

//   if (response.ok) {
//     const data = await response.json();
//     return data.session_id;
//   } else {
//     alert("Resume upload failed!");
//     return null;
//   }
// }

// // Start interview
// async function startInterview() {
//   if (isRunning) return;
//   isRunning = true;

//   sessionId = await uploadResume();
//   if (!sessionId) { isRunning = false; return; }

//   const transcriptDiv = document.getElementById("transcript");
//   const feedbackDiv = document.getElementById("feedback");

//   // Clear previous content
//   transcriptDiv.textContent = "";
//   feedbackDiv.textContent = "Feedback will appear here after the interview.";

//   // WebSocket
//   ws = new WebSocket(`ws://localhost:8000/ws/interview?session_id=${sessionId}`);

//   ws.onopen = () => console.log("WebSocket connected");

//   ws.onmessage = (event) => {
//     const data = JSON.parse(event.data);

//     if (data.type === "PARTIAL_TRANSCRIPT") {
//       transcriptDiv.textContent += data.text + " ";
//       transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
//       resetSilenceTimer();
//     }

//     if (data.type === "FINAL_TRANSCRIPT") {
//       transcriptDiv.textContent += "\n" + data.text;
//       transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
//     }

//     if (data.type === "FEEDBACK") {
//       try {
//         const fb = JSON.parse(data.text);
//         feedbackDiv.innerHTML = `
//         <b>Overall Score:</b> ${fb.overall}<br/>
//         <b>Content:</b> ${fb.content_score} | 
//         <b>Communication:</b> ${fb.communication_score} | 
//         <b>Technical:</b> ${fb.technical_depth} | 
//         <b>Confidence:</b> ${fb.confidence}<br/>
//         <b>Strengths:</b> ${fb.strengths.join(", ")}<br/>
//         <b>Improvements:</b> ${fb.improvements.join(", ")}
//         `;
//       } catch {
//         feedbackDiv.textContent = data.text; // fallback
//       }
//     }

//     if (data.type === "QUESTION") {
//       transcriptDiv.textContent += "\n\n Question: " + data.text + "\n";
//       transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
//       resetSilenceTimer();
//     }

//     if (data.type === "END") {
//       transcriptDiv.textContent += "\n\n" + data.text;
//       transcriptDiv.scrollTop = transcriptDiv.scrollHeight;

//       // Display final summary if provided
//       if (data.summary) {
//         const summaryDiv = document.createElement("div");
//         summaryDiv.style.background = "#f3f4f6";
//         summaryDiv.style.border = "1px solid #d1d5db";
//         summaryDiv.style.borderRadius = "8px";
//         summaryDiv.style.padding = "10px";
//         summaryDiv.style.marginTop = "15px";

//         let summaryText = "Final Interview Summary:\n\n";
//         data.summary.answers.forEach((ans, i) => {
//           summaryText += `Q${i + 1}: ${ans.question}\n`;
//           summaryText += `Answer: ${ans.answer}\n`;
//           summaryText += `Scores → Correctness: ${ans.scores.correctness}, Depth: ${ans.scores.depth}, Clarity: ${ans.scores.clarity}, Final: ${ans.scores.final_score}\n\n`;
//         });
//         summaryText += `Average Score: ${data.summary.average_score} \n`;
//         summaryText += `Result: ${data.summary.result}`;

//         summaryDiv.textContent = summaryText;
//         transcriptDiv.appendChild(summaryDiv);
//       }

//       startBtn.disabled = false;
//       stopBtn.disabled = true;
//       submitBtn.disabled = true;
//       isRunning = false;
//     }

//     if (data.type === "ERROR") {
//       alert(data.text);
//       isRunning = false;
//     }
//   };

//   ws.onclose = () => { console.log("WebSocket closed"); isRunning = false; };

//   // Audio setup
//   audioContext = new AudioContext({ sampleRate: 16000 });
//   stream = await navigator.mediaDevices.getUserMedia({ audio: true });

//   source = audioContext.createMediaStreamSource(stream);
//   processor = audioContext.createScriptProcessor(4096, 1, 1);

//   processor.onaudioprocess = (e) => {
//     if (!isRunning) return;
//     const input = e.inputBuffer.getChannelData(0);
//     if (ws && ws.readyState === WebSocket.OPEN) ws.send(input.buffer);
//     resetSilenceTimer();
//   };

//   source.connect(processor);
//   processor.connect(audioContext.destination);

//   stopBtn.disabled = false;
//   submitBtn.disabled = false;
// }

// // Stop interview
// function stopInterview() {
//   if (!isRunning) return;
//   isRunning = false;

//   if (ws && ws.readyState === WebSocket.OPEN) {
//     ws.send(JSON.stringify({ text: "STOP_INTERVIEW" }));
//     ws.close();
//   }

//   if (processor) processor.disconnect();
//   if (source) source.disconnect();
//   if (audioContext) audioContext.close();
//   if (stream) stream.getTracks().forEach(track => track.stop());

//   startBtn.disabled = false;
//   stopBtn.disabled = true;
//   submitBtn.disabled = true;
// }

// // Submit current answer manually
// function submitAnswer() {
//   if (!isRunning) return;
//   if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ text: "SUBMIT_ANSWER" }));
//   resetSilenceTimer();
// }

// // Silence detection (10s)
// function resetSilenceTimer() {
//   clearTimeout(silenceTimeout);
//   silenceTimeout = setTimeout(() => {
//     if (isRunning) submitAnswer();
//   }, 10000);
// }

// // Event listeners
// startBtn.addEventListener("click", async () => {
//   startBtn.disabled = true;
//   stopBtn.disabled = false;
//   submitBtn.disabled = false;
//   await startInterview();
// });

// stopBtn.addEventListener("click", stopInterview);
// submitBtn.addEventListener("click", submitAnswer);



// let audioContext = null;
// let processor = null;
// let source = null;
// let stream = null;
// let ws = null;
// let isRunning = false;
// let sessionId = null;
// let silenceTimeout;

// // Buttons
// const resumeInput = document.getElementById("resumeFile");
// const startBtn = document.getElementById("startBtn");
// const stopBtn = document.getElementById("stopBtn");
// const submitBtn = document.getElementById("submitBtn");

// // Enable start button after resume selection
// resumeInput.addEventListener("change", () => { startBtn.disabled = false; });

// // Upload resume & create session
// async function uploadResume() {
//   const file = resumeInput.files[0];
//   if (!file) return null;

//   const formData = new FormData();
//   formData.append("file", file);
//   formData.append("job_description", "Python Developer"); // set job description

//   const response = await fetch("http://localhost:8000/upload_resume", {
//     method: "POST",
//     body: formData
//   });

//   if (response.ok) {
//     const data = await response.json();
//     return data.session_id;
//   } else {
//     alert("Resume upload failed!");
//     return null;
//   }
// }

// // Start interview
// async function startInterview() {
//   if (isRunning) return;
//   isRunning = true;

//   sessionId = await uploadResume();
//   if (!sessionId) { isRunning = false; return; }

//   const transcriptDiv = document.getElementById("transcript");
//   const feedbackDiv = document.getElementById("feedback");

//   transcriptDiv.textContent = "";
//   feedbackDiv.textContent = "Feedback will appear here after the interview.";

//   // Connect WebSocket
//   ws = new WebSocket(`ws://localhost:8000/ws/interview?session_id=${sessionId}`);

//   ws.onopen = () => console.log("WebSocket connected");

//   ws.onmessage = (event) => {
//     const data = JSON.parse(event.data);

//     if (data.type === "PARTIAL_TRANSCRIPT") {
//       transcriptDiv.textContent += data.text + " ";
//       transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
//       resetSilenceTimer();
//     }

//     if (data.type === "FINAL_TRANSCRIPT") {
//       transcriptDiv.textContent += "\n" + data.text;
//       transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
//     }

//     if (data.type === "FEEDBACK") {
//       try {
//         const fb = JSON.parse(data.text);
//         feedbackDiv.innerHTML = `
//           <b>Overall Score:</b> ${fb.overall}<br/>
//           <b>Content:</b> ${fb.content_score} | 
//           <b>Technical:</b> ${fb.technical_depth} | 
//           <b>Communication:</b> ${fb.communication_score}<br/>
//           <b>Strengths:</b> ${fb.strengths.join(", ")}<br/>
//           <b>Improvements:</b> ${fb.improvements.join(", ")}
//         `;
//       } catch {
//         feedbackDiv.textContent = data.text;
//       }
//     }

//     if (data.type === "QUESTION") {
//       transcriptDiv.textContent += "\n\n Question: " + data.text + "\n";
//       transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
//       resetSilenceTimer();
//     }

//     if (data.type === "END") {
//       transcriptDiv.textContent += "\n\n" + data.text;
//       transcriptDiv.scrollTop = transcriptDiv.scrollHeight;

//       // Display final summary
//       if (data.summary) {
//         const summaryDiv = document.createElement("div");
//         summaryDiv.style.background = "#f3f4f6";
//         summaryDiv.style.border = "1px solid #d1d5db";
//         summaryDiv.style.borderRadius = "8px";
//         summaryDiv.style.padding = "10px";
//         summaryDiv.style.marginTop = "15px";

//         let summaryText = "Final Interview Summary:\n\n";
//         data.summary.answers.forEach((ans, i) => {
//           summaryText += `Q${i + 1}: ${ans}\n`;
//           summaryText += `Answer: ${ans}\n`;
//           summaryText += `Scores → Correctness: ${ans.scores.correctness}, Depth: ${ans.scores.depth}, Clarity: ${ans.scores.clarity}, Final: ${ans.scores.final_score}\n\n`;
//         });
//         summaryText += `Average Score: ${data.summary.average_score} \n`;
//         summaryText += `Result: ${data.summary.result}`;

//         summaryDiv.textContent = summaryText;
//         transcriptDiv.appendChild(summaryDiv);
//       }

//       startBtn.disabled = false;
//       stopBtn.disabled = true;
//       submitBtn.disabled = true;
//       isRunning = false;
//     }

//     if (data.type === "ERROR") {
//       alert(data.text);
//       isRunning = false;
//     }
//   };

//   ws.onclose = () => { console.log("WebSocket closed"); isRunning = false; };

//   // Audio setup
//   audioContext = new AudioContext({ sampleRate: 16000 });
//   stream = await navigator.mediaDevices.getUserMedia({ audio: true });

//   source = audioContext.createMediaStreamSource(stream);
//   processor = audioContext.createScriptProcessor(4096, 1, 1);

//   processor.onaudioprocess = (e) => {
//     if (!isRunning) return;
//     const input = e.inputBuffer.getChannelData(0);
//     if (ws && ws.readyState === WebSocket.OPEN) ws.send(input.buffer);
//     resetSilenceTimer();
//   };

//   source.connect(processor);
//   processor.connect(audioContext.destination);

//   stopBtn.disabled = false;
//   submitBtn.disabled = false;
// }

// // Stop interview
// function stopInterview() {
//   if (!isRunning) return;
//   isRunning = false;

//   if (ws && ws.readyState === WebSocket.OPEN) {
//     ws.send(JSON.stringify({ text: "STOP_INTERVIEW" }));
//     ws.close();
//   }

//   if (processor) processor.disconnect();
//   if (source) source.disconnect();
//   if (audioContext) audioContext.close();
//   if (stream) stream.getTracks().forEach(track => track.stop());

//   startBtn.disabled = false;
//   stopBtn.disabled = true;
//   submitBtn.disabled = true;
// }

// // Submit current answer
// function submitAnswer() {
//   if (!isRunning) return;
//   if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ text: "SUBMIT_ANSWER" }));
//   resetSilenceTimer();
// }

// // Auto-submit on silence (10s)
// function resetSilenceTimer() {
//   clearTimeout(silenceTimeout);
//   silenceTimeout = setTimeout(() => {
//     if (isRunning) submitAnswer();
//   }, 10000);
// }

// // Button listeners
// startBtn.addEventListener("click", async () => {
//   startBtn.disabled = true;
//   stopBtn.disabled = false;
//   submitBtn.disabled = false;
//   await startInterview();
// });

// stopBtn.addEventListener("click", stopInterview);
// submitBtn.addEventListener("click", submitAnswer);









// // frontend/audio.js
// let audioContext = null;
// let processor = null;
// let source = null;
// let stream = null;
// let isRunning = false;
// let sessionId = null;
// let silenceTimeout;
// let ws;

// // Buttons
// const resumeInput = document.getElementById("resumeFile");
// const startBtn = document.getElementById("startBtn");
// const stopBtn = document.getElementById("stopBtn");
// const submitBtn = document.getElementById("submitBtn");

// // Enable start button after file selection
// resumeInput.addEventListener("change", () => {
//   startBtn.disabled = false;
// });

// // Upload resume & create session
// async function uploadResume() {
//   const file = resumeInput.files[0];
//   if (!file) return null;

//   const formData = new FormData();
//   formData.append("file", file);
//   formData.append("job_description", "Python Developer");

//   const response = await fetch("http://localhost:8000/upload_resume", {
//     method: "POST",
//     body: formData
//   });

//   if (response.ok) {
//     const data = await response.json();
//     return data.session_id;
//   } else {
//     alert("Resume upload failed!");
//     return null;
//   }
// }

// // Start interview
// async function startInterview() {
//   if (isRunning) return;
//   isRunning = true;

//   sessionId = await uploadResume();
//   if (!sessionId) { isRunning = false; return; }

//   const transcriptDiv = document.getElementById("transcript");
//   const feedbackDiv = document.getElementById("feedback");

//   transcriptDiv.textContent = "";
//   feedbackDiv.textContent = "Feedback will appear here after the interview.";

//   ws = new WebSocket(`ws://localhost:8000/ws/interview?session_id=${sessionId}`);

//   ws.onopen = () => console.log("WebSocket connected");

//   ws.onmessage = (event) => {
//     const data = JSON.parse(event.data);

//     if (data.type === "QUESTION") {
//       transcriptDiv.textContent += "\n\n Question: " + data.text + "\n";
//       transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
//       resetSilenceTimer();
//     }

//     if (data.type === "FINAL_TRANSCRIPT") {
//       transcriptDiv.textContent += "\n" + data.text;
//       transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
//     }

//     if (data.type === "END" && data.summary) {
//       const summaryDiv = document.createElement("div");
//       summaryDiv.style.background = "#f3f4f6";
//       summaryDiv.style.border = "1px solid #d1d5db";
//       summaryDiv.style.borderRadius = "8px";
//       summaryDiv.style.padding = "10px";
//       summaryDiv.style.marginTop = "15px";

//       let summaryText = `Final Interview Summary:\n\nAverage Score: ${data.summary.average_score}\nResult: ${data.summary.result}\n\n`;

//       data.summary.questions.forEach((q, i) => {
//         summaryText += `Q${i + 1}: ${q}\nAnswer: ${data.summary.answers[i]}\nScores → Correctness: ${data.summary.scores[i].correctness}, Depth: ${data.summary.scores[i].depth}, Clarity: ${data.summary.scores[i].clarity}, Final: ${data.summary.scores[i].final_score}\n\n`;
//       });

//       // LLM-generated feedback
//       if (data.summary.feedback) {
//         summaryText += `Feedback:\n${data.summary.feedback}\n`;
//       }

//       summaryDiv.textContent = summaryText;
//       transcriptDiv.appendChild(summaryDiv);

//       startBtn.disabled = false;
//       stopBtn.disabled = true;
//       submitBtn.disabled = true;
//       isRunning = false;
//     }

//     if (data.type === "ERROR") {
//       alert(data.text);
//       isRunning = false;
//     }
//   };

//   ws.onclose = () => { console.log("WebSocket closed"); isRunning = false; };

//   // Audio setup
//   audioContext = new AudioContext({ sampleRate: 16000 });
//   stream = await navigator.mediaDevices.getUserMedia({ audio: true });

//   source = audioContext.createMediaStreamSource(stream);
//   processor = audioContext.createScriptProcessor(4096, 1, 1);

//   processor.onaudioprocess = (e) => {
//     if (!isRunning) return;
//     const input = e.inputBuffer.getChannelData(0);
//     if (ws && ws.readyState === WebSocket.OPEN) ws.send(input.buffer);
//     resetSilenceTimer();
//   };

//   source.connect(processor);
//   processor.connect(audioContext.destination);

//   stopBtn.disabled = false;
//   submitBtn.disabled = false;
// }

// // Stop interview
// function stopInterview() {
//   if (!isRunning) return;
//   isRunning = false;

//   if (ws && ws.readyState === WebSocket.OPEN) {
//     ws.send(JSON.stringify({ text: "SUBMIT_ANSWER" }));
//     ws.close();
//   }

//   if (processor) processor.disconnect();
//   if (source) source.disconnect();
//   if (audioContext) audioContext.close();
//   if (stream) stream.getTracks().forEach(track => track.stop());

//   startBtn.disabled = false;
//   stopBtn.disabled = true;
//   submitBtn.disabled = true;
// }

// // Submit answer manually
// function submitAnswer() {
//   if (!isRunning) return;
//   if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ text: "SUBMIT_ANSWER" }));
//   resetSilenceTimer();
// }

// // Silence detection
// function resetSilenceTimer() {
//   clearTimeout(silenceTimeout);
//   silenceTimeout = setTimeout(() => {
//     if (isRunning) submitAnswer();
//   }, 10000);
// }

// startBtn.addEventListener("click", async () => {
//   startBtn.disabled = true;
//   stopBtn.disabled = false;
//   submitBtn.disabled = false;
//   await startInterview();
// });

// stopBtn.addEventListener("click", stopInterview);
// submitBtn.addEventListener("click", submitAnswer);

// // frontend/audio.js

// let audioContext = null;
// let processor = null;
// let source = null;
// let stream = null;
// let isRunning = false;
// let sessionId = null;
// let silenceTimeout;
// let ws;

// // Buttons
// const resumeInput = document.getElementById("resumeFile");
// const startBtn = document.getElementById("startBtn");
// const stopBtn = document.getElementById("stopBtn");
// const submitBtn = document.getElementById("submitBtn");

// // Enable start button after file selection
// resumeInput.addEventListener("change", () => startBtn.disabled = false);

// // Upload resume & create session
// async function uploadResume() {
//     const file = resumeInput.files[0];
//     if (!file) return null;

//     const formData = new FormData();
//     formData.append("file", file);
//     formData.append("job_description", "Python Developer");

//     const response = await fetch("http://localhost:8000/upload_resume", {
//         method: "POST",
//         body: formData
//     });

//     if (response.ok) {
//         const data = await response.json();
//         return data.session_id;
//     } else {
//         alert("Resume upload failed!");
//         return null;
//     }
// }

// // Play WAV audio from server
// function playAudioBytes(bytes) {
//     const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
//     audioCtx.decodeAudioData(bytes.slice(0), (buffer) => {
//         const source = audioCtx.createBufferSource();
//         source.buffer = buffer;
//         source.connect(audioCtx.destination);
//         source.start(0);
//     });
// }

// // Start interview
// async function startInterview() {
//     if (isRunning) return;
//     isRunning = true;

//     sessionId = await uploadResume();
//     if (!sessionId) { isRunning = false; return; }

//     const transcriptDiv = document.getElementById("transcript");
//     const feedbackDiv = document.getElementById("feedback");

//     transcriptDiv.textContent = "";
//     feedbackDiv.textContent = "Feedback will appear here after the interview.";

//     ws = new WebSocket(`ws://localhost:8000/ws/interview?session_id=${sessionId}`);

//     ws.onopen = () => console.log("WebSocket connected");

//     ws.onmessage = (event) => {
//         if (typeof event.data === "string") {
//             const data = JSON.parse(event.data);

//             if (data.type === "QUESTION") {
//                 transcriptDiv.textContent += "\n\n Question: " + data.text + "\n";
//                 transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
//                 resetSilenceTimer();
//             }

//             if (data.type === "FINAL_TRANSCRIPT") {
//                 transcriptDiv.textContent += "\n" + data.text;
//                 transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
//             }

//             if (data.type === "END" && data.summary) {
//                 const summaryDiv = document.createElement("div");
//                 summaryDiv.style.background = "#f3f4f6";
//                 summaryDiv.style.border = "1px solid #d1d5db";
//                 summaryDiv.style.borderRadius = "8px";
//                 summaryDiv.style.padding = "10px";
//                 summaryDiv.style.marginTop = "15px";

//                 let summaryText = `Final Interview Summary:\n\nAverage Score: ${data.summary.average_score}\nResult: ${data.summary.result}\n\n`;

//                 data.summary.questions.forEach((q, i) => {
//                     summaryText += `Q${i + 1}: ${q}\nAnswer: ${data.summary.answers[i]}\nScores → Correctness: ${data.summary.scores[i].correctness}, Depth: ${data.summary.scores[i].depth}, Clarity: ${data.summary.scores[i].clarity}, Final: ${data.summary.scores[i].final_score}\n\n`;
//                 });

//                 if (data.summary.feedback) {
//                     summaryText += `Feedback:\n${data.summary.feedback}\n`;
//                 }

//                 summaryDiv.textContent = summaryText;
//                 transcriptDiv.appendChild(summaryDiv);

//                 startBtn.disabled = false;
//                 stopBtn.disabled = true;
//                 submitBtn.disabled = true;
//                 isRunning = false;
//             }

//             if (data.type === "ERROR") {
//                 alert(data.text);
//                 isRunning = false;
//             }
//         } else if (event.data instanceof Blob) {
//             // Play audio bytes
//             const reader = new FileReader();
//             reader.onload = function() {
//                 const arrayBuffer = reader.result;
//                 playAudioBytes(arrayBuffer);
//             };
//             reader.readAsArrayBuffer(event.data);
//         }
//     };

//     ws.onclose = () => { console.log("WebSocket closed"); isRunning = false; };

//     // Audio setup
//     audioContext = new AudioContext({ sampleRate: 16000 });
//     stream = await navigator.mediaDevices.getUserMedia({ audio: true });

//     source = audioContext.createMediaStreamSource(stream);
//     processor = audioContext.createScriptProcessor(4096, 1, 1);

//     processor.onaudioprocess = (e) => {
//         if (!isRunning) return;
//         const input = e.inputBuffer.getChannelData(0);
//         if (ws && ws.readyState === WebSocket.OPEN) ws.send(input.buffer);
//         resetSilenceTimer();
//     };

//     source.connect(processor);
//     processor.connect(audioContext.destination);

//     stopBtn.disabled = false;
//     submitBtn.disabled = false;
// }

// // Stop interview
// // Stop interview
// function stopInterview() {
//     if (!isRunning) return;
//     isRunning = false;

//     if (ws && ws.readyState === WebSocket.OPEN) {
//         try {
//             ws.send(JSON.stringify({ text: "SUBMIT_ANSWER" }));
//         } catch (err) {
//             console.log("WebSocket already closing:", err);
//         }
//         ws.close();
//     }

//     if (processor) processor.disconnect();
//     if (source) source.disconnect();
//     if (audioContext) audioContext.close();
//     if (stream) stream.getTracks().forEach(track => track.stop());

//     startBtn.disabled = false;
//     stopBtn.disabled = true;
//     submitBtn.disabled = true;
// }

// // Submit answer manually
// function submitAnswer() {
//     if (!isRunning) return;
//     if (ws && ws.readyState === WebSocket.OPEN) {
//         try {
//             ws.send(JSON.stringify({ text: "SUBMIT_ANSWER" }));
//         } catch (err) {
//             console.log("WebSocket closed, cannot submit:", err);
//         }
//     }
//     resetSilenceTimer();
// }


// // Silence detection
// function resetSilenceTimer() {
//     clearTimeout(silenceTimeout);
//     silenceTimeout = setTimeout(() => {
//         if (isRunning) submitAnswer();
//     }, 10000);
// }

// startBtn.addEventListener("click", async () => {
//     startBtn.disabled = true;
//     stopBtn.disabled = false;
//     submitBtn.disabled = false;
//     await startInterview();
// });

// stopBtn.addEventListener("click", stopInterview);
// submitBtn.addEventListener("click", submitAnswer);




let audioContext = null;
let processor = null;
let source = null;
let stream = null;
let isRunning = false;
let sessionId = null;
let silenceTimeout;
let ws;

// Buttons
const resumeInput = document.getElementById("resumeFile");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const submitBtn = document.getElementById("submitBtn");

// Enable start button after file selection
resumeInput.addEventListener("change", () => startBtn.disabled = false);

// Upload resume & create session
async function uploadResume() {
    const file = resumeInput.files[0];
    if (!file) return null;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("job_description", "Python Developer");

    const response = await fetch("http://localhost:8000/upload_resume", {
        method: "POST",
        body: formData
    });

    if (response.ok) {
        const data = await response.json();
        return data.session_id;
    } else {
        alert("Resume upload failed!");
        return null;
    }
}

// Play WAV audio from server
function playAudioBytes(bytes) {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    audioCtx.decodeAudioData(bytes.slice(0), (buffer) => {
        const source = audioCtx.createBufferSource();
        source.buffer = buffer;
        source.connect(audioCtx.destination);
        source.start(0);
    });
}

// Reset silence timer
function resetSilenceTimer() {
    clearTimeout(silenceTimeout);
    silenceTimeout = setTimeout(() => {
        if (isRunning) submitAnswer();
    }, 10000);
}

// Start interview
async function startInterview() {
    if (isRunning) return;
    isRunning = true;

    sessionId = await uploadResume();
    if (!sessionId) { isRunning = false; return; }

    const transcriptDiv = document.getElementById("transcript");
    const feedbackDiv = document.getElementById("feedback");

    transcriptDiv.textContent = "";
    feedbackDiv.textContent = "Feedback will appear here after the interview.";

    ws = new WebSocket(`ws://localhost:8000/ws/interview?session_id=${sessionId}`);

    ws.onopen = () => console.log("WebSocket connected");

    ws.onmessage = (event) => {
        if (!isRunning) return; // Stop processing after stop

        if (typeof event.data === "string") {
            const data = JSON.parse(event.data);

            switch (data.type) {
                case "QUESTION":
                    transcriptDiv.textContent += "\n\n Question: " + data.text + "\n";
                    transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
                    resetSilenceTimer();
                    break;

                case "FINAL_TRANSCRIPT":
                    transcriptDiv.textContent += "\n" + data.text;
                    transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
                    break;

                case "END":
                    displaySummary(data.summary, transcriptDiv);
                    stopInterview(); // Ensure cleanup
                    break;

                case "ERROR":
                    alert(data.text);
                    stopInterview();
                    break;
            }
        } else if (event.data instanceof Blob) {
            const reader = new FileReader();
            reader.onload = function () {
                const arrayBuffer = reader.result;
                playAudioBytes(arrayBuffer);
            };
            reader.readAsArrayBuffer(event.data);
        }
    };

    ws.onclose = () => {
        console.log("WebSocket closed");
        isRunning = false;
    };

    // Audio setup
    audioContext = new AudioContext({ sampleRate: 16000 });
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    source = audioContext.createMediaStreamSource(stream);
    processor = audioContext.createScriptProcessor(4096, 1, 1);

    processor.onaudioprocess = (e) => {
        if (!isRunning) return;
        const input = e.inputBuffer.getChannelData(0);

        if (ws && ws.readyState === WebSocket.OPEN) {
            // Convert Float32Array to ArrayBuffer for sending
            ws.send(input.buffer);
        }

        resetSilenceTimer();
    };

    source.connect(processor);
    processor.connect(audioContext.destination);

    stopBtn.disabled = false;
    submitBtn.disabled = false;
}

// Stop interview safely
function stopInterview() {
    if (!isRunning) return;

    isRunning = false;

    // Stop audio capture
    if (processor) processor.disconnect();
    if (source) source.disconnect();
    if (audioContext) audioContext.close();
    if (stream) stream.getTracks().forEach(track => track.stop());

    // Close WebSocket safely
    if (ws && ws.readyState === WebSocket.OPEN) {
        try {
            ws.send(JSON.stringify({ text: "SUBMIT_ANSWER" }));
            ws.close();
        } catch (e) {
            console.log("WebSocket already closing/closed");
        }
    }

    startBtn.disabled = false;
    stopBtn.disabled = true;
    submitBtn.disabled = true;
}

// Submit answer manually
function submitAnswer() {
    if (!isRunning) return;
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ text: "SUBMIT_ANSWER" }));
    resetSilenceTimer();
}

// Display interview summary
function displaySummary(summary, container) {
    if (!summary) return;

    const summaryDiv = document.createElement("div");
    summaryDiv.style.background = "#f3f4f6";
    summaryDiv.style.border = "1px solid #d1d5db";
    summaryDiv.style.borderRadius = "8px";
    summaryDiv.style.padding = "10px";
    summaryDiv.style.marginTop = "15px";

    let summaryText = `Final Interview Summary:\n\nAverage Score: ${summary.average_score}\nResult: ${summary.result}\n\n`;

    summary.questions.forEach((q, i) => {
        summaryText += `Q${i + 1}: ${q}\nAnswer: ${summary.answers[i]}\nScores → Correctness: ${summary.scores[i].correctness}, Depth: ${summary.scores[i].depth}, Clarity: ${summary.scores[i].clarity}, Final: ${summary.scores[i].final_score}\n\n`;
    });

    if (summary.feedback) {
        summaryText += `Feedback:\n${summary.feedback}\n`;
    }

    summaryDiv.textContent = summaryText;
    container.appendChild(summaryDiv);
}

// Button event listeners
startBtn.addEventListener("click", async () => {
    startBtn.disabled = true;
    stopBtn.disabled = false;
    submitBtn.disabled = false;
    await startInterview();
});

stopBtn.addEventListener("click", stopInterview);
submitBtn.addEventListener("click", submitAnswer);
