// frontend/audio.js


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

// // Reset silence timer
// function resetSilenceTimer() {
//     clearTimeout(silenceTimeout);
//     silenceTimeout = setTimeout(() => {
//         if (isRunning) submitAnswer();
//     }, 10000);
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
//         if (!isRunning) return; // Stop processing after stop

//         if (typeof event.data === "string") {
//             const data = JSON.parse(event.data);

//             switch (data.type) {
//                 case "QUESTION":
//                     transcriptDiv.textContent += "\n\n Question: " + data.text + "\n";
//                     transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
//                     resetSilenceTimer();
//                     break;

//                 case "FINAL_TRANSCRIPT":
//                     transcriptDiv.textContent += "\n" + data.text;
//                     transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
//                     break;

//                 case "END":
//                     displaySummary(data.summary, transcriptDiv);
//                     stopInterview(); // Ensure cleanup
//                     break;

//                 case "ERROR":
//                     alert(data.text);
//                     stopInterview();
//                     break;
//             }
//         } else if (event.data instanceof Blob) {
//             const reader = new FileReader();
//             reader.onload = function () {
//                 const arrayBuffer = reader.result;
//                 playAudioBytes(arrayBuffer);
//             };
//             reader.readAsArrayBuffer(event.data);
//         }
//     };

//     ws.onclose = () => {
//         console.log("WebSocket closed");
//         isRunning = false;
//     };

//     // Audio setup
//     audioContext = new AudioContext({ sampleRate: 16000 });
//     stream = await navigator.mediaDevices.getUserMedia({ audio: true });

//     source = audioContext.createMediaStreamSource(stream);
//     processor = audioContext.createScriptProcessor(4096, 1, 1);

//     processor.onaudioprocess = (e) => {
//         if (!isRunning) return;
//         const input = e.inputBuffer.getChannelData(0);

//         if (ws && ws.readyState === WebSocket.OPEN) {
//             // Convert Float32Array to ArrayBuffer for sending
//             ws.send(input.buffer);
//         }

//         resetSilenceTimer();
//     };

//     source.connect(processor);
//     processor.connect(audioContext.destination);

//     stopBtn.disabled = false;
//     submitBtn.disabled = false;
// }

// // Stop interview safely
// function stopInterview() {
//     if (!isRunning) return;

//     isRunning = false;

//     // Stop audio capture
//     if (processor) processor.disconnect();
//     if (source) source.disconnect();
//     if (audioContext) audioContext.close();
//     if (stream) stream.getTracks().forEach(track => track.stop());

//     // Close WebSocket safely
//     if (ws && ws.readyState === WebSocket.OPEN) {
//         try {
//             ws.send(JSON.stringify({ text: "SUBMIT_ANSWER" }));
//             ws.close();
//         } catch (e) {
//             console.log("WebSocket already closing/closed");
//         }
//     }

//     startBtn.disabled = false;
//     stopBtn.disabled = true;
//     submitBtn.disabled = true;
// }

// // Submit answer manually
// function submitAnswer() {
//     if (!isRunning) return;
//     if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ text: "SUBMIT_ANSWER" }));
//     resetSilenceTimer();
// }

// // Display interview summary
// function displaySummary(summary, container) {
//     if (!summary) return;

//     const summaryDiv = document.createElement("div");
//     summaryDiv.style.background = "#f3f4f6";
//     summaryDiv.style.border = "1px solid #d1d5db";
//     summaryDiv.style.borderRadius = "8px";
//     summaryDiv.style.padding = "10px";
//     summaryDiv.style.marginTop = "15px";

//     let summaryText = `Final Interview Summary:\n\nAverage Score: ${summary.average_score}\nResult: ${summary.result}\n\n`;

//     summary.questions.forEach((q, i) => {
//         summaryText += `Q${i + 1}: ${q}\nAnswer: ${summary.answers[i]}\nScores → Correctness: ${summary.scores[i].correctness}, Depth: ${summary.scores[i].depth}, Clarity: ${summary.scores[i].clarity}, Final: ${summary.scores[i].final_score}\n\n`;
//     });

//     if (summary.feedback) {
//         summaryText += `Feedback:\n${summary.feedback}\n`;
//     }

//     summaryDiv.textContent = summaryText;
//     container.appendChild(summaryDiv);
// }

// // Button event listeners
// startBtn.addEventListener("click", async () => {
//     startBtn.disabled = true;
//     stopBtn.disabled = false;
//     submitBtn.disabled = false;
//     await startInterview();
// });

// stopBtn.addEventListener("click", stopInterview);
// submitBtn.addEventListener("click", submitAnswer);


// let audioContext = null;
// let processor = null;
// let source = null;
// let stream = null;
// let isRunning = false;
// let sessionId = null;
// let silenceTimeout;
// let ws;

// // Mic + TTS state
// let micEnabled = false;
// let isAISpeaking = false;

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

// // Play WAV audio from server in chunks
// async function playAudioBytes(bytes) {
//     if (!bytes || !audioContext) return;

//     isAISpeaking = true;
//     micEnabled = false;
//     submitBtn.disabled = true;

//     const chunkSize = 1024 * 1024; // 1MB per chunk
//     let offset = 0;

//     while (offset < bytes.byteLength) {
//         const chunk = bytes.slice(offset, offset + chunkSize);
//         await decodeAndPlayChunk(chunk);
//         offset += chunkSize;
//     }

//     isAISpeaking = false;
//     micEnabled = true;
//     submitBtn.disabled = false;
// }

// function decodeAndPlayChunk(chunk) {
//     return new Promise((resolve) => {
//         audioContext.decodeAudioData(chunk.slice(0), (buffer) => {
//             const sourceNode = audioContext.createBufferSource();
//             sourceNode.buffer = buffer;
//             sourceNode.connect(audioContext.destination);

//             sourceNode.onended = () => resolve();
//             sourceNode.start(0);
//         });
//     });
// }

// // Mic control
// function muteMic() {
//     if (processor) processor.disconnect();
//     micEnabled = false;
//     console.log(" Mic muted");
// }

// function unmuteMic() {
//     if (source && processor && audioContext) {
//         source.connect(processor);
//         processor.connect(audioContext.destination);
//     }
//     micEnabled = true;
//     console.log(" Mic unmuted");
// }

// // Reset silence timer
// function resetSilenceTimer() {
//     clearTimeout(silenceTimeout);
//     silenceTimeout = setTimeout(() => {
//         if (isRunning) submitAnswer();
//     }, 10000);
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

//     ws.onmessage = async (event) => {
//         if (!isRunning) return;

//         if (typeof event.data === "string") {
//             const data = JSON.parse(event.data);

//             switch (data.type) {
//                 case "QUESTION":
//                     transcriptDiv.textContent += "\n\n Question: " + data.text + "\n";
//                     transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
//                     resetSilenceTimer();
//                     break;

//                 case "FINAL_TRANSCRIPT":
//                     transcriptDiv.textContent += "\n" + data.text;
//                     transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
//                     break;

//                 case "END":
//                     displaySummary(data.summary, transcriptDiv);
//                     stopInterview();
//                     break;

//                 case "ERROR":
//                     alert(data.text);
//                     stopInterview();
//                     break;
//             }
//         } else if (event.data instanceof Blob) {
//             const reader = new FileReader();
//             reader.onload = async function () {
//                 const arrayBuffer = reader.result;
//                 await playAudioBytes(arrayBuffer);
//             };
//             reader.readAsArrayBuffer(event.data);
//         }
//     };

//     ws.onclose = () => {
//         console.log("WebSocket closed");
//         isRunning = false;
//     };

//     // Audio setup
//     audioContext = new AudioContext({ sampleRate: 16000 });
//     stream = await navigator.mediaDevices.getUserMedia({ audio: true });

//     source = audioContext.createMediaStreamSource(stream);
//     processor = audioContext.createScriptProcessor(4096, 1, 1);

//     processor.onaudioprocess = (e) => {
//         if (!isRunning || !micEnabled) return;

//         const input = e.inputBuffer.getChannelData(0);
//         if (ws && ws.readyState === WebSocket.OPEN) {
//             ws.send(input.buffer);
//         }

//         resetSilenceTimer();
//     };

//     // Connect mic initially
//     unmuteMic();

//     stopBtn.disabled = false;
// }

// // Stop interview safely
// function stopInterview() {
//     if (!isRunning) return;

//     isRunning = false;

//     if (processor) processor.disconnect();
//     if (source) source.disconnect();
//     if (audioContext) audioContext.close();
//     if (stream) stream.getTracks().forEach(track => track.stop());

//     if (ws && ws.readyState === WebSocket.OPEN) {
//         try {
//             ws.send(JSON.stringify({ text: "SUBMIT_ANSWER" }));
//             ws.close();
//         } catch (e) {
//             console.log("WebSocket already closing/closed");
//         }
//     }

//     startBtn.disabled = false;
//     stopBtn.disabled = true;
//     submitBtn.disabled = true;
// }

// // Submit answer manually
// function submitAnswer() {
//     if (!isRunning || isAISpeaking) return; // Prevent submission while AI is speaking
//     if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ text: "SUBMIT_ANSWER" }));
//     resetSilenceTimer();
// }

// // Display interview summary
// function displaySummary(summary, container) {
//     if (!summary) return;

//     const summaryDiv = document.createElement("div");
//     summaryDiv.style.background = "#f3f4f6";
//     summaryDiv.style.border = "1px solid #d1d5db";
//     summaryDiv.style.borderRadius = "8px";
//     summaryDiv.style.padding = "10px";
//     summaryDiv.style.marginTop = "15px";

//     let summaryText = `Final Interview Summary:\n\nAverage Score: ${summary.average_score}\nResult: ${summary.result}\n\n`;

//     summary.questions.forEach((q, i) => {
//         summaryText += `Q${i + 1}: ${q}\nAnswer: ${summary.answers[i]}\nScores → Correctness: ${summary.scores[i].correctness}, Depth: ${summary.scores[i].depth}, Clarity: ${summary.scores[i].clarity}, Final: ${summary.scores[i].final_score}\n\n`;
//     });

//     if (summary.feedback) {
//         summaryText += `Feedback:\n${summary.feedback}\n`;
//     }

//     summaryDiv.textContent = summaryText;
//     container.appendChild(summaryDiv);
// }

// // Button event listeners
// startBtn.addEventListener("click", async () => {
//     startBtn.disabled = true;
//     stopBtn.disabled = false;
//     submitBtn.disabled = true; // Disabled until first question finishes
//     await startInterview();
// });

// stopBtn.addEventListener("click", stopInterview);
// submitBtn.addEventListener("click", submitAnswer);




// // frontend/audio.js - WITH BUFFER TIME FIX

// /* =======================
//    TIMER STATE
// ======================= */

// let warned10Min = false;
// let warned5Min = false;
// let bufferWarningShown = false;

// let totalSeconds = 0;
// let mainTimeSeconds = 0;
// let bufferTimeSeconds = 0;
// let remainingSeconds = 0;
// let timerInterval = null;
// let isTimerPaused = false;
// let inBufferTime = false;

// /* =======================
//    AUDIO / WS STATE
// ======================= */

// let audioContext = null;
// let processor = null;
// let source = null;
// let stream = null;

// let isRunning = false;
// let sessionId = null;
// let silenceTimeout = null;
// let ws = null;

// let micEnabled = false;
// let isAISpeaking = false;

// /* =======================
//    UI ELEMENTS
// ======================= */

// const resumeInput = document.getElementById("resumeFile");
// const startBtn = document.getElementById("startBtn");
// const stopBtn = document.getElementById("stopBtn");
// const submitBtn = document.getElementById("submitBtn");

// resumeInput.addEventListener("change", () => {
//     startBtn.disabled = false;
// });

// /* =======================
//    LOGGING
// ======================= */

// function log(message, type = "info") {
//     const timestamp = new Date().toLocaleTimeString();
//     const prefix = {
//         "info": "ℹ️",
//         "success": "✅",
//         "error": "❌",
//         "warning": "⚠️"
//     }[type] || "ℹ️";
    
//     console.log(`[${timestamp}] ${prefix} ${message}`);
// }

// /* =======================
//    RESUME UPLOAD
// ======================= */

// async function uploadResume() {
//     const file = resumeInput.files[0];
//     if (!file) {
//         log("No resume file selected", "error");
//         return null;
//     }

//     log(`Uploading resume: ${file.name}`, "info");

//     const formData = new FormData();
//     formData.append("file", file);
//     formData.append("job_description", "Python Developer");

//     try {
//         const res = await fetch("http://localhost:8000/upload_resume", {
//             method: "POST",
//             body: formData
//         });

//         const data = await res.json();
        
//         if (!res.ok) {
//             throw new Error(data.error || await res.text());
//         }
        
//         log(`Resume uploaded. Session: ${data.session_id}`, "success");
//         return data.session_id;

//     } catch (err) {
//         log(`Upload failed: ${err.message}`, "error");
//         alert(`Resume upload failed: ${err.message}`);
//         return null;
//     }
// }

// /* =======================
//    TIMER HELPERS
// ======================= */

// function formatTime(seconds) {
//     if (typeof seconds !== "number" || isNaN(seconds) || seconds < 0) {
//         return "00:00";
//     }
//     const m = Math.floor(seconds / 60).toString().padStart(2, "0");
//     const s = Math.floor(seconds % 60).toString().padStart(2, "0");
//     return `${m}:${s}`;
// }

// function updateTimerUI(seconds, isBuffer = false) {
//     const timerEl = document.getElementById("timer");
//     if (!timerEl || typeof seconds !== "number" || isNaN(seconds)) return;

//     // Show different prefix for buffer time
//     const prefix = isBuffer ? "⏰ BUFFER TIME: " : "⏱️ ";
//     timerEl.textContent = `${prefix}${formatTime(seconds)}`;
    
//     timerEl.classList.remove("green", "yellow", "red");

//     if (isBuffer) {
//         // Buffer time is always red and pulsing
//         timerEl.classList.add("red");
//     } else {
//         // Normal time colors
//         if (seconds <= 300) {
//             timerEl.classList.add("red");
//             if (!warned5Min) {
//                 warned5Min = true;
//                 alert("⏰ 5 minutes remaining!");
//             }
//         } else if (seconds <= 600) {
//             timerEl.classList.add("yellow");
//             if (!warned10Min) {
//                 warned10Min = true;
//                 alert("⏰ 10 minutes remaining!");
//             }
//         } else {
//             timerEl.classList.add("green");
//         }
//     }
// }

// function startLocalCountdown() {
//     if (timerInterval) return;

//     timerInterval = setInterval(() => {
//         if (!isRunning || isTimerPaused || remainingSeconds <= 0) return;

//         remainingSeconds--;
//         updateTimerUI(remainingSeconds, inBufferTime);

//         if (remainingSeconds <= 0) {
//             stopTimer();
//         }
//     }, 1000);
// }

// function stopTimer() {
//     clearInterval(timerInterval);
//     timerInterval = null;
// }

// function pauseTimer() {
//     isTimerPaused = true;
// }

// function resumeTimer() {
//     isTimerPaused = false;
// }

// /* =======================
//    AUDIO HELPERS
// ======================= */

// function floatTo16BitPCM(float32Array) {
//     const buffer = new ArrayBuffer(float32Array.length * 2);
//     const view = new DataView(buffer);
//     for (let i = 0; i < float32Array.length; i++) {
//         let s = Math.max(-1, Math.min(1, float32Array[i]));
//         view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
//     }
//     return buffer;
// }

// async function playAudioBytes(arrayBuffer) {
//     if (!arrayBuffer || !audioContext) return;

//     isAISpeaking = true;
//     pauseTimer();
//     muteMic();
//     submitBtn.disabled = true;

//     try {
//         const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
//         const src = audioContext.createBufferSource();
//         src.buffer = audioBuffer;
//         src.connect(audioContext.destination);

//         await new Promise(resolve => {
//             src.onended = resolve;
//             src.start(0);
//         });

//     } catch (e) {
//         log(`TTS error: ${e.message}`, "error");
//     } finally {
//         isAISpeaking = false;
//         if (isRunning) {
//             resumeTimer();
//             unmuteMic();
//             submitBtn.disabled = false;
//             resetSilenceTimer();
//         }
//     }
// }

// /* =======================
//    MIC CONTROL
// ======================= */

// function muteMic() {
//     try {
//         processor?.disconnect();
//         source?.disconnect();
//     } catch {}
//     micEnabled = false;
// }

// function unmuteMic() {
//     try {
//         if (audioContext && processor && source && isRunning) {
//             source.connect(processor);
//             processor.connect(audioContext.destination);
//             micEnabled = true;
//         }
//     } catch {}
// }

// /* =======================
//    SILENCE TIMER
// ======================= */

// function resetSilenceTimer() {
//     clearTimeout(silenceTimeout);
//     if (isRunning && !isAISpeaking) {
//         silenceTimeout = setTimeout(() => {
//             if (isRunning && !isAISpeaking) {
//                 log("10s silence - auto-submitting", "info");
//                 submitAnswer();
//             }
//         }, 10000);
//     }
// }

// /* =======================
//    SCORE FORMATTING
// ======================= */

// function getScoreEmoji(score) {
//     if (score >= 0.75) return "🟢";
//     if (score >= 0.50) return "🟡";
//     if (score >= 0.25) return "🟠";
//     return "🔴";
// }

// function getScoreGrade(score) {
//     if (score >= 0.90) return "Excellent";
//     if (score >= 0.75) return "Good";
//     if (score >= 0.60) return "Average";
//     if (score >= 0.40) return "Below Average";
//     return "Poor";
// }

// /* =======================
//    DISPLAY RESULTS
// ======================= */

// function displayResults(summary) {
//     const transcript = document.getElementById("transcript");
//     transcript.textContent = "";
    
//     transcript.textContent += "\n";
//     transcript.textContent += "╔═══════════════════════════════════════════════════════════════════╗\n";
//     transcript.textContent += "║                     📊 INTERVIEW RESULTS                          ║\n";
//     transcript.textContent += "╚═══════════════════════════════════════════════════════════════════╝\n";
//     transcript.textContent += "\n\n";
    
//     // QUESTION-WISE SCORES
//     transcript.textContent += "┌─────────────────────────────────────────────────────────────────┐\n";
//     transcript.textContent += "│                    QUESTION-WISE SCORES                         │\n";
//     transcript.textContent += "└─────────────────────────────────────────────────────────────────┘\n\n";
    
//     summary.questions.forEach((question, index) => {
//         const score = summary.scores[index];
//         const duration = summary.time_per_answer_seconds ? summary.time_per_answer_seconds[index] : 0;
        
//         const emoji = getScoreEmoji(score.final_score);
//         const grade = getScoreGrade(score.final_score);
        
//         transcript.textContent += `${emoji} Question ${index + 1}:\n`;
//         transcript.textContent += `   ${question}\n`;
//         transcript.textContent += `   Score: ${score.final_score.toFixed(2)} (${grade}) | Time: ${Math.floor(duration)}s\n\n`;
//     });
    
//     // OVERALL SUMMARY
//     transcript.textContent += "\n┌─────────────────────────────────────────────────────────────────┐\n";
//     transcript.textContent += "│                      OVERALL SUMMARY                            │\n";
//     transcript.textContent += "└─────────────────────────────────────────────────────────────────┘\n\n";
    
//     const resultIcon = summary.result === 'PASS' ? '✅' : '❌';
//     const resultText = summary.result === 'PASS' ? 'PASS' : 'FAIL';
    
//     transcript.textContent += `${resultIcon} Final Result:       ${resultText}\n`;
//     transcript.textContent += `📈 Average Score:      ${summary.average_score.toFixed(2)} / 1.00\n`;
//     transcript.textContent += `📝 Questions Answered: ${summary.questions_answered} / ${summary.questions_asked}\n`;
//     transcript.textContent += `⏱️  Total Duration:     ${Math.floor(summary.total_duration_seconds / 60)}m ${Math.floor(summary.total_duration_seconds % 60)}s\n`;
//     transcript.textContent += `🏁 Completion:         ${summary.completion_reason.replace(/_/g, ' ')}\n`;
    
//     if (summary.covered_projects && summary.covered_projects.length > 0) {
//         transcript.textContent += `💼 Projects Covered:   ${summary.covered_projects.join(', ')}\n`;
//     }
    
//     // FEEDBACK
//     transcript.textContent += "\n\n┌─────────────────────────────────────────────────────────────────┐\n";
//     transcript.textContent += "│                         FEEDBACK                                │\n";
//     transcript.textContent += "└─────────────────────────────────────────────────────────────────┘\n\n";
    
//     if (summary.feedback && summary.feedback.trim()) {
//         transcript.textContent += summary.feedback + "\n";
//     } else {
//         transcript.textContent += "⏳ Generating feedback...\n";
//     }
    
//     transcript.textContent += "\n\n";
//     transcript.textContent += "╔═══════════════════════════════════════════════════════════════════╗\n";
//     transcript.textContent += "║          Thank you for completing the interview! 🎉              ║\n";
//     transcript.textContent += "╚═══════════════════════════════════════════════════════════════════╝\n";
    
//     transcript.scrollTop = 0;
// }

// /* =======================
//    START INTERVIEW
// ======================= */

// async function startInterview() {
//     if (isRunning) {
//         log("Already running", "warning");
//         return;
//     }

//     log("Starting interview...", "info");
//     isRunning = true;
//     warned10Min = false;
//     warned5Min = false;
//     bufferWarningShown = false;
//     inBufferTime = false;

//     sessionId = await uploadResume();
//     if (!sessionId) {
//         isRunning = false;
//         return;
//     }

//     const transcript = document.getElementById("transcript");
//     transcript.textContent = "Interview starting...\n";

//     const wsUrl = `ws://localhost:8000/ws/interview?session_id=${sessionId}`;
//     log(`Connecting to WebSocket`, "info");

//     ws = new WebSocket(wsUrl);
//     ws.binaryType = "arraybuffer";

//     ws.onopen = () => {
//         log("WebSocket connected", "success");
//         transcript.textContent += "✅ Connected\n";
//     };

//     ws.onmessage = async (event) => {
//         if (typeof event.data === "string") {
//             const data = JSON.parse(event.data);
//             log(`Message: ${data.type}`, "info");

//             switch (data.type) {
//                 case "TIMER_INIT":
//                     mainTimeSeconds = data.main_time_seconds;
//                     bufferTimeSeconds = data.buffer_time_seconds;
//                     // Start with ONLY main time (45 minutes)
//                     remainingSeconds = mainTimeSeconds;
//                     updateTimerUI(remainingSeconds, false);
//                     startLocalCountdown();
//                     log(`Timer started: ${mainTimeSeconds}s main + ${bufferTimeSeconds}s buffer`, "success");
//                     break;

//                 case "TIMER_UPDATE":
//                     const newRemaining = data.remaining_seconds;
//                     const nowInBuffer = data.in_buffer_time || false;
                    
//                     // Check if we just entered buffer time
//                     if (nowInBuffer && !inBufferTime) {
//                         // Transition to buffer time
//                         inBufferTime = true;
//                         remainingSeconds = bufferTimeSeconds;
//                         updateTimerUI(remainingSeconds, true);
                        
//                         if (!bufferWarningShown) {
//                             bufferWarningShown = true;
//                             alert("⚠️ Main time expired! You have 2 minutes buffer time remaining.");
//                             log("Entered buffer time", "warning");
//                         }
//                     } else {
//                         remainingSeconds = newRemaining;
//                         updateTimerUI(remainingSeconds, inBufferTime);
//                     }
//                     break;

//                 case "BUFFER_TIME_WARNING":
//                     if (!bufferWarningShown && !inBufferTime) {
//                         inBufferTime = true;
//                         remainingSeconds = bufferTimeSeconds;
//                         bufferWarningShown = true;
//                         alert(data.message);
//                         updateTimerUI(remainingSeconds, true);
//                         log("Entered buffer time", "warning");
//                     }
//                     break;

//                 case "QUESTION":
//                     transcript.textContent += `\n❓ ${data.text}\n`;
//                     transcript.scrollTop = transcript.scrollHeight;
//                     resetSilenceTimer();
//                     break;

//                 case "FINAL_TRANSCRIPT":
//                     transcript.textContent += `\nYou: ${data.text}\n`;
//                     transcript.scrollTop = transcript.scrollHeight;
//                     break;

//                 case "END":
//                     log("Interview ended", "success");
//                     displayResults(data.summary);
//                     stopInterview(false);
//                     break;

//                 case "ERROR":
//                     log(`Error: ${data.text}`, "error");
//                     alert(`Error: ${data.text}`);
//                     stopInterview(false);
//                     break;

//                 case "TTS_START":
//                 case "TTS_END":
//                     break;
//             }
//         } else {
//             await playAudioBytes(event.data);
//         }
//     };

//     ws.onerror = (error) => {
//         log(`WebSocket error`, "error");
//         console.error(error);
//         alert("Connection error. Check backend server.");
//         stopInterview(false);
//     };

//     ws.onclose = (event) => {
//         log(`WebSocket closed: ${event.code}`, "warning");
//         if (isRunning) {
//             stopInterview(false);
//         }
//     };

//     try {
//         log("Requesting microphone...", "info");
//         audioContext = new AudioContext({ sampleRate: 16000 });
//         stream = await navigator.mediaDevices.getUserMedia({ audio: true });
//         log("Microphone granted", "success");

//         source = audioContext.createMediaStreamSource(stream);
//         processor = audioContext.createScriptProcessor(4096, 1, 1);

//         processor.onaudioprocess = (e) => {
//             if (!isRunning || !micEnabled || isAISpeaking) return;
//             if (ws?.readyState === WebSocket.OPEN) {
//                 ws.send(floatTo16BitPCM(e.inputBuffer.getChannelData(0)));
//                 resetSilenceTimer();
//             }
//         };

//         unmuteMic();
//         log("Audio processing started", "success");

//         stopBtn.disabled = false;
//         submitBtn.disabled = false;

//     } catch (err) {
//         log(`Microphone failed: ${err.message}`, "error");
//         alert(`Microphone access denied: ${err.message}`);
//         stopInterview(false);
//     }
// }

// /* =======================
//    STOP INTERVIEW
// ======================= */

// function stopInterview(reset = true) {
//     log("Stopping...", "info");
    
//     isRunning = false;
//     pauseTimer();
//     stopTimer();
//     clearTimeout(silenceTimeout);

//     try {
//         muteMic();
//         processor?.disconnect();
//         source?.disconnect();
//         audioContext?.close();
//         stream?.getTracks().forEach(t => t.stop());
//         ws?.close();
//         log("Stopped", "success");
//     } catch (e) {
//         log(`Cleanup error: ${e.message}`, "error");
//     }

//     if (reset) {
//         startBtn.disabled = false;
//         stopBtn.disabled = true;
//         submitBtn.disabled = true;
//     }
// }

// /* =======================
//    SUBMIT ANSWER
// ======================= */

// function submitAnswer() {
//     if (ws?.readyState === WebSocket.OPEN && isRunning) {
//         log("Submitting answer", "info");
//         ws.send(JSON.stringify({ action: "SUBMIT_ANSWER" }));
//         clearTimeout(silenceTimeout);
//     } else {
//         log(`Cannot submit: WS=${ws?.readyState}`, "warning");
//     }
// }

// /* =======================
//    EVENTS
// ======================= */

// startBtn.addEventListener("click", async () => {
//     startBtn.disabled = true;
//     await startInterview();
// });

// stopBtn.addEventListener("click", () => {
//     stopInterview(true);
// });

// submitBtn.addEventListener("click", submitAnswer);

// log("Loaded successfully", "success");

// frontend/audio.js - SINGLE SCREEN NO SCROLL UI

// ─── TIMER STATE ───
let warned10Min = false;
let warned5Min = false;
let bufferWarningShown = false;
let remainingSeconds = 0;
let timerInterval = null;
let inBufferTime = false;

// ─── AUDIO / WS STATE ───
let audioContext = null;
let processor = null;
let source = null;
let stream = null;
let isRunning = false;
let sessionId = null;
let silenceTimeout = null;
let ws = null;
let micEnabled = false;
let isAISpeaking = false;

// ─── INTERVIEW STATE ───
let currentQuestionNumber = 0;
let currentQuestion = null;

// ─── UI ELEMENTS ───
const resumeInput = document.getElementById("resumeFile");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const submitBtn = document.getElementById("submitBtn");
const skipBtn = document.getElementById("skipBtn");

resumeInput.addEventListener("change", () => {
    startBtn.disabled = false;
});

// ─── LOGGING ───
function log(message, type = "info") {
    const timestamp = new Date().toLocaleTimeString();
    const prefix = {
        "info": "ℹ️",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️"
    }[type] || "ℹ️";
    console.log(`[${timestamp}] ${prefix} ${message}`);
}

// ─── RESUME UPLOAD ───
async function uploadResume() {
    const file = resumeInput.files[0];
    if (!file) {
        log("No resume file selected", "error");
        return null;
    }

    log(`Uploading resume: ${file.name}`, "info");

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("http://localhost:8000/upload_resume", {
            method: "POST",
            body: formData
        });

        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.error || await res.text());
        }
        
        log(`Resume uploaded. Session: ${data.session_id}`, "success");
        return data.session_id;

    } catch (err) {
        log(`Upload failed: ${err.message}`, "error");
        alert(`Resume upload failed: ${err.message}`);
        return null;
    }
}

// ─── TIMER HELPERS ───
function formatTime(seconds) {
    if (typeof seconds !== "number" || isNaN(seconds) || seconds < 0) {
        return "00:00";
    }
    const m = Math.floor(seconds / 60).toString().padStart(2, "0");
    const s = Math.floor(seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
}

function updateTimerUI(seconds, isBuffer = false) {
    const timerEl = document.getElementById("timer");
    if (!timerEl || typeof seconds !== "number" || isNaN(seconds)) return;

    const prefix = isBuffer ? "⏰ BUFFER: " : "⏱️ ";
    timerEl.textContent = `${prefix}${formatTime(seconds)}`;
    
    timerEl.classList.remove("green", "yellow", "red");

    if (isBuffer) {
        timerEl.classList.add("red");
    } else {
        if (seconds <= 300) {
            timerEl.classList.add("red");
            if (!warned5Min) {
                warned5Min = true;
                alert("⏰ 5 minutes remaining!");
            }
        } else if (seconds <= 600) {
            timerEl.classList.add("yellow");
            if (!warned10Min) {
                warned10Min = true;
                alert("⏰ 10 minutes remaining!");
            }
        } else {
            timerEl.classList.add("green");
        }
    }
}

function startLocalCountdown() {
    if (timerInterval) return;

    log("Starting continuous timer", "info");
    
    timerInterval = setInterval(() => {
        if (!isRunning || remainingSeconds <= 0) return;

        remainingSeconds--;
        updateTimerUI(remainingSeconds, inBufferTime);

        if (remainingSeconds <= 0) {
            stopTimer();
        }
    }, 1000);
}

function stopTimer() {
    log("Stopping timer", "info");
    clearInterval(timerInterval);
    timerInterval = null;
}

// ─── COMPACT SINGLE-SCREEN UI ───

function showCurrentQuestion(questionText, questionNum) {
    const transcript = document.getElementById("transcript");
    
    transcript.innerHTML = `
        <div style="
            display: flex;
            flex-direction: column;
            height: 100%;
            animation: fadeIn 0.4s ease-in;
        ">
            <!-- Question Header - Compact -->
            <div style="
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px 15px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
                margin-bottom: 12px;
            ">
                <div style="
                    background: white;
                    color: #667eea;
                    width: 35px;
                    height: 35px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 16px;
                    font-weight: bold;
                ">
                    ${questionNum}
                </div>
                <div style="flex: 1; color: white;">
                    <div style="font-weight: 600; font-size: 13px;">Question ${questionNum}/10</div>
                    <div style="font-size: 11px; opacity: 0.9;">Active</div>
                </div>
                <div style="
                    background: rgba(255,255,255,0.2);
                    padding: 5px 12px;
                    border-radius: 20px;
                    font-size: 11px;
                    color: white;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 5px;
                ">
                    <div style="
                        width: 8px;
                        height: 8px;
                        background: #f44336;
                        border-radius: 50%;
                        animation: blink 1s infinite;
                    "></div>
                    REC
                </div>
            </div>
            
            <!-- Question Content - Scrollable if needed -->
            <div style="
                flex: 1;
                background: linear-gradient(to bottom, #e3f2fd 0%, #f3e5f5 100%);
                padding: 20px;
                border-radius: 10px;
                border-left: 4px solid #2196F3;
                overflow-y: auto;
                margin-bottom: 12px;
            ">
                <div style="
                    color: #1976D2;
                    font-size: 12px;
                    font-weight: 600;
                    margin-bottom: 10px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                ">
                    ❓ Your Question
                </div>
                <div style="
                    color: #333;
                    font-size: 16px;
                    line-height: 1.6;
                    font-weight: 500;
                ">
                    ${questionText}
                </div>
            </div>
            
            <!-- Status Bar - Compact -->
            <div style="
                background: #fff3e0;
                padding: 12px 15px;
                border-radius: 8px;
                border: 2px solid #FF9800;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            ">
                <span style="font-size: 18px;">🎤</span>
                <span style="color: #f57c00; font-weight: 600; font-size: 14px;">
                    Listening...
                </span>
            </div>
        </div>
        
        <style>
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes blink {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.3; }
            }
        </style>
    `;
}

function showAnswerRecorded() {
    const transcript = document.getElementById("transcript");
    
    transcript.innerHTML = `
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            animation: fadeIn 0.4s ease-in;
        ">
            <div style="
                width: 70px;
                height: 70px;
                background: #4CAF50;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 20px;
                box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);
            ">
                <span style="font-size: 35px; color: white;">✓</span>
            </div>
            <div style="
                color: #2E7D32;
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 8px;
            ">
                Answer Recorded!
            </div>
            <div style="color: #666; font-size: 14px;">
                Preparing next question...
            </div>
        </div>
    `;
}

function showQuestionSkipped() {
    const transcript = document.getElementById("transcript");
    
    transcript.innerHTML = `
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            animation: fadeIn 0.4s ease-in;
        ">
            <div style="
                width: 70px;
                height: 70px;
                background: #FF9800;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 20px;
                box-shadow: 0 4px 15px rgba(255, 152, 0, 0.4);
            ">
                <span style="font-size: 35px;">⏭️</span>
            </div>
            <div style="
                color: #F57C00;
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 8px;
            ">
                Question Skipped
            </div>
            <div style="color: #666; font-size: 14px; margin-bottom: 10px;">
                Moving to next question...
            </div>
            <div style="
                color: #999;
                font-size: 12px;
                padding: 8px 12px;
                background: rgba(255, 152, 0, 0.1);
                border-radius: 6px;
            ">
                Score: 0 points
            </div>
        </div>
    `;
}

// ─── AUDIO HELPERS ───
function floatTo16BitPCM(float32Array) {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view = new DataView(buffer);
    let offset = 0;
    for (let i = 0; i < float32Array.length; i++, offset += 2) {
        let s = Math.max(-1, Math.min(1, float32Array[i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
    return buffer;
}

async function playAudioBytes(arrayBuffer) {
    if (!arrayBuffer || !audioContext) return;

    log("Playing TTS audio", "info");
    
    isAISpeaking = true;
    muteMic();
    submitBtn.disabled = true;
    skipBtn.disabled = true;

    try {
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        const src = audioContext.createBufferSource();
        src.buffer = audioBuffer;
        src.connect(audioContext.destination);

        await new Promise(resolve => {
            src.onended = resolve;
            src.start(0);
        });

        log("TTS playback complete", "success");

    } catch (e) {
        log(`TTS error: ${e.message}`, "error");
    } finally {
        isAISpeaking = false;

        if (isRunning) {
            unmuteMic();
            submitBtn.disabled = false;
            skipBtn.disabled = false;
            resetSilenceTimer();
        }
    }
}

// ─── MIC CONTROL ───
function muteMic() {
    try {
        processor?.disconnect();
        source?.disconnect();
    } catch {}
    micEnabled = false;
}

function unmuteMic() {
    try {
        if (audioContext && processor && source && isRunning) {
            source.connect(processor);
            processor.connect(audioContext.destination);
            micEnabled = true;
        }
    } catch {}
}

// ─── SILENCE TIMER ───
function resetSilenceTimer() {
    clearTimeout(silenceTimeout);
    if (isRunning && !isAISpeaking) {
        silenceTimeout = setTimeout(() => {
            if (isRunning && !isAISpeaking) {
                log("10s silence - auto-submitting", "info");
                submitAnswer();
            }
        }, 10000);
    }
}

// ─── SCORE FORMATTING ───
function getScoreEmoji(score) {
    if (score >= 0.75) return "🟢";
    if (score >= 0.50) return "🟡";
    if (score >= 0.25) return "🟠";
    return "🔴";
}

function getScoreGrade(score) {
    if (score >= 0.90) return "Excellent";
    if (score >= 0.75) return "Good";
    if (score >= 0.60) return "Average";
    if (score >= 0.40) return "Below Average";
    return "Poor";
}

// ─── DISPLAY RESULTS ───
function displayResults(summary) {
    const transcript = document.getElementById("transcript");
    transcript.textContent = "";
    
    transcript.textContent += "\n";
    transcript.textContent += "╔═══════════════════════════════════════════════════════════════════╗\n";
    transcript.textContent += "║                     📊 INTERVIEW RESULTS                          ║\n";
    transcript.textContent += "╚═══════════════════════════════════════════════════════════════════╝\n";
    transcript.textContent += "\n\n";
    
    transcript.textContent += "┌─────────────────────────────────────────────────────────────────┐\n";
    transcript.textContent += "│                    INTERVIEW TRANSCRIPT                         │\n";
    transcript.textContent += "└─────────────────────────────────────────────────────────────────┘\n\n";
    
    summary.questions.forEach((question, index) => {
        const answer = summary.answers[index] || "No answer";
        const score = summary.scores[index];
        const duration = summary.time_per_answer_seconds ? summary.time_per_answer_seconds[index] : 0;
        
        const emoji = getScoreEmoji(score.final_score);
        const grade = getScoreGrade(score.final_score);
        
        transcript.textContent += `${emoji} Question ${index + 1}:\n`;
        transcript.textContent += `   Q: ${question}\n`;
        transcript.textContent += `   A: ${answer}\n`;
        transcript.textContent += `   Score: ${score.final_score.toFixed(2)} (${grade}) | Time: ${Math.floor(duration)}s\n\n`;
    });
    
    transcript.textContent += "\n┌─────────────────────────────────────────────────────────────────┐\n";
    transcript.textContent += "│                      OVERALL SUMMARY                            │\n";
    transcript.textContent += "└─────────────────────────────────────────────────────────────────┘\n\n";
    
    const resultIcon = summary.result === 'PASS' ? '✅' : '❌';
    const resultText = summary.result === 'PASS' ? 'PASS' : 'FAIL';
    
    transcript.textContent += `${resultIcon} Final Result:       ${resultText}\n`;
    transcript.textContent += `📈 Average Score:      ${summary.average_score.toFixed(2)} / 1.00\n`;
    transcript.textContent += `📝 Questions Answered: ${summary.questions_answered} / ${summary.questions_asked}\n`;
    transcript.textContent += `⏱️  Total Duration:     ${Math.floor(summary.total_duration_seconds / 60)}m ${Math.floor(summary.total_duration_seconds % 60)}s\n`;
    transcript.textContent += `🏁 Completion:         ${summary.completion_reason.replace(/_/g, ' ')}\n`;
    
    if (summary.covered_projects && summary.covered_projects.length > 0) {
        transcript.textContent += `💼 Projects Covered:   ${summary.covered_projects.join(', ')}\n`;
    }
    
    transcript.textContent += "\n\n┌─────────────────────────────────────────────────────────────────┐\n";
    transcript.textContent += "│                         FEEDBACK                                │\n";
    transcript.textContent += "└─────────────────────────────────────────────────────────────────┘\n\n";
    
    if (summary.feedback && summary.feedback.trim()) {
        transcript.textContent += summary.feedback + "\n";
    } else {
        transcript.textContent += "⏳ Generating feedback...\n";
    }
    
    transcript.textContent += "\n\n";
    transcript.textContent += "╔═══════════════════════════════════════════════════════════════════╗\n";
    transcript.textContent += "║          Thank you for completing the interview! 🎉              ║\n";
    transcript.textContent += "╚═══════════════════════════════════════════════════════════════════╝\n";
    
    transcript.scrollTop = 0;
}

// ─── START INTERVIEW ───
async function startInterview() {
    if (isRunning) {
        log("Already running", "warning");
        return;
    }

    log("Starting interview...", "info");
    isRunning = true;
    warned10Min = false;
    warned5Min = false;
    bufferWarningShown = false;
    inBufferTime = false;
    currentQuestionNumber = 0;

    sessionId = await uploadResume();
    if (!sessionId) {
        isRunning = false;
        startBtn.disabled = false;
        return;
    }

    const transcript = document.getElementById("transcript");
    transcript.innerHTML = `
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
        ">
            <div style="
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 20px;
                animation: pulse 2s infinite;
            ">
                <span style="font-size: 40px;">🚀</span>
            </div>
            <div style="font-size: 22px; font-weight: bold; color: #667eea; margin-bottom: 10px;">
                Starting Interview
            </div>
            <div style="color: #666; font-size: 14px;">
                Connecting...
            </div>
        </div>
        <style>
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
        </style>
    `;

    // Initialize audio
    try {
        log("Requesting microphone...", "info");

        audioContext = new AudioContext({ sampleRate: 16000 });
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        log("Microphone granted", "success");

        source = audioContext.createMediaStreamSource(stream);
        processor = audioContext.createScriptProcessor(4096, 1, 1);

        processor.onaudioprocess = function (e) {
            if (!isRunning || !micEnabled) return;
            if (!ws || ws.readyState !== WebSocket.OPEN) return;

            const input = e.inputBuffer.getChannelData(0);
            const pcmBuffer = floatTo16BitPCM(input);
            ws.send(pcmBuffer);
        };

        source.connect(processor);
        processor.connect(audioContext.destination);
        micEnabled = true;

        log("Audio processing started", "success");

    } catch (err) {
        log(`Microphone failed: ${err.message}`, "error");
        alert(`Microphone access denied: ${err.message}`);
        stopInterview(true);
        return;
    }

    // Create WebSocket
    const wsUrl = `ws://localhost:8000/ws/interview?session_id=${sessionId}`;
    log(`Connecting to WebSocket`, "info");

    ws = new WebSocket(wsUrl);
    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
        log("WebSocket connected", "success");
        transcript.innerHTML = `
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100%;
            ">
                <div style="
                    width: 80px;
                    height: 80px;
                    background: #4CAF50;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-bottom: 20px;
                ">
                    <span style="font-size: 40px; color: white;">✓</span>
                </div>
                <div style="font-size: 22px; font-weight: bold; color: #4CAF50; margin-bottom: 10px;">
                    Connected!
                </div>
                <div style="color: #666; font-size: 14px;">
                    Loading question...
                </div>
            </div>
        `;
        stopBtn.disabled = false;
        submitBtn.disabled = false;
        skipBtn.disabled = false;
    };

    ws.onmessage = async (event) => {
        if (typeof event.data === "string") {
            const data = JSON.parse(event.data);
            
            if (data.type !== "TIMER_UPDATE") {
                log(`← ${data.type}`, "info");
            }

            switch (data.type) {
                case "TIMER_UPDATE":
                    remainingSeconds = data.remaining_seconds;
                    const nowInBuffer = data.in_buffer_time || false;

                    if (nowInBuffer && !inBufferTime) {
                        inBufferTime = true;
                        
                        if (!bufferWarningShown) {
                            bufferWarningShown = true;
                            alert("⚠️ Main time expired! Buffer time remaining.");
                            log("Entered buffer time", "warning");
                        }
                    }
                    
                    updateTimerUI(remainingSeconds, inBufferTime);
                    
                    if (!timerInterval) {
                        startLocalCountdown();
                    }
                    break;

                case "BUFFER_TIME_WARNING":
                    if (!bufferWarningShown) {
                        inBufferTime = true;
                        bufferWarningShown = true;
                        alert(data.message);
                    }
                    break;

                case "QUESTION":
                    currentQuestionNumber++;
                    currentQuestion = data.text;
                    
                    log(`Question ${currentQuestionNumber} received`, "info");
                    showCurrentQuestion(data.text, currentQuestionNumber);
                    resetSilenceTimer();
                    break;

                case "FINAL_TRANSCRIPT":
                    log(`Answer recorded`, "info");
                    
                    if (data.text.includes("skipped")) {
                        showQuestionSkipped();
                    } else {
                        showAnswerRecorded();
                    }
                    break;

                case "END":
                    log("Interview ended", "success");
                    displayResults(data.summary);
                    stopInterview(false);
                    break;

                case "ERROR":
                    log(`Error: ${data.text}`, "error");
                    alert(`Error: ${data.text}`);
                    stopInterview(false);
                    break;

                case "TTS_START":
                case "TTS_END":
                    break;
            }
        } else {
            await playAudioBytes(event.data);
        }
    };

    ws.onerror = (error) => {
        log(`WebSocket error`, "error");
        console.error(error);
        stopInterview(false);
    };

    ws.onclose = (event) => {
        log(`WebSocket closed: ${event.code}`, "warning");
        if (isRunning) {
            stopInterview(false);
        }
    };
}

// ─── STOP INTERVIEW ───
function stopInterview(reset = true) {
    log("Stopping...", "info");
    
    isRunning = false;
    stopTimer();
    clearTimeout(silenceTimeout);

    try {
        muteMic();
        processor?.disconnect();
        source?.disconnect();
        audioContext?.close();
        stream?.getTracks().forEach(t => t.stop());
        ws?.close();
        log("Stopped", "success");
    } catch (e) {
        log(`Cleanup error: ${e.message}`, "error");
    }

    if (reset) {
        startBtn.disabled = false;
        stopBtn.disabled = true;
        submitBtn.disabled = true;
        skipBtn.disabled = true;
    }
}

// ─── SUBMIT ANSWER ───
function submitAnswer() {
    if (ws?.readyState === WebSocket.OPEN && isRunning) {
        log("→ Submitting answer", "info");
        ws.send(JSON.stringify({ action: "SUBMIT_ANSWER" }));
        clearTimeout(silenceTimeout);
    } else {
        log(`Cannot submit: WS=${ws?.readyState}`, "warning");
    }
}

// ─── SKIP QUESTION ───
function skipQuestion() {
    if (ws?.readyState === WebSocket.OPEN && isRunning) {
        log("→ Skipping question", "warning");
        ws.send(JSON.stringify({ action: "SKIP_QUESTION" }));
        clearTimeout(silenceTimeout);
    } else {
        log(`Cannot skip: WS=${ws?.readyState}`, "warning");
    }
}

// ─── EVENT LISTENERS ───
startBtn.addEventListener("click", async (e) => {
    e.preventDefault();
    startBtn.disabled = true;
    await startInterview();
});

stopBtn.addEventListener("click", (e) => {
    e.preventDefault();
    stopInterview(true);
});

submitBtn.addEventListener("click", (e) => {
    e.preventDefault();
    submitAnswer();
});

skipBtn.addEventListener("click", (e) => {
    e.preventDefault();
    skipQuestion();
});

log("Audio.js loaded", "success");