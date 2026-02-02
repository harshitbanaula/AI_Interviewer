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





let audioContext = null;
let processor = null;
let source = null;
let stream = null;
let isRunning = false;
let sessionId = null;
let silenceTimeout;
let ws;

// Mic + TTS state
let micEnabled = false;
let isAISpeaking = false;

// Buttons
const resumeInput = document.getElementById("resumeFile");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const submitBtn = document.getElementById("submitBtn");

// Enable start button after file selection
resumeInput.addEventListener("change", () => {
    startBtn.disabled = false;
    console.log(" Resume file selected");
});

// Upload resume & create session
async function uploadResume() {
    const file = resumeInput.files[0];
    if (!file) {
        console.error(" No file selected");
        return null;
    }

    console.log(` Uploading resume: ${file.name}`);
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("job_description", "Python Developer");

    try {
        const response = await fetch("http://localhost:8000/upload_resume", {
            method: "POST",
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            console.log(`Session created: ${data.session_id}`);
            return data.session_id;
        } else {
            const errorText = await response.text();
            console.error(" Resume upload failed:", errorText);
            alert("Resume upload failed! Check console for details.");
            return null;
        }
    } catch (error) {
        console.error(" Upload error:", error);
        alert("Network error during upload!");
        return null;
    }
}

// Play WAV audio from server - FIXED VERSION
async function playAudioBytes(arrayBuffer) {
    if (!arrayBuffer || arrayBuffer.byteLength === 0) {
        console.warn(" Empty audio buffer received");
        return;
    }
    
    if (!audioContext) {
        console.error(" AudioContext not initialized");
        return;
    }

    console.log(`🔊 Playing audio (${arrayBuffer.byteLength} bytes)...`);
    
    isAISpeaking = true;
    micEnabled = false;
    muteMic();
    submitBtn.disabled = true;

    try {
        // Decode the entire WAV audio buffer
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        
        console.log(`   Duration: ${audioBuffer.duration.toFixed(2)}s, Sample rate: ${audioBuffer.sampleRate}Hz`);
        
        // Create and configure audio source
        const sourceNode = audioContext.createBufferSource();
        sourceNode.buffer = audioBuffer;
        sourceNode.connect(audioContext.destination);
        
        // Wait for playback to complete
        await new Promise((resolve, reject) => {
            sourceNode.onended = () => {
                console.log(" Audio playback finished");
                resolve();
            };
            
            sourceNode.onerror = (error) => {
                console.error(" Audio playback error:", error);
                reject(error);
            };
            
            sourceNode.start(0);
        });

    } catch (error) {
        console.error(" Audio decode/playback error:", error);
        alert("Audio playback failed! Check console for details.");
    } finally {
        // Re-enable mic after playback
        isAISpeaking = false;
        micEnabled = true;
        unmuteMic();
        submitBtn.disabled = false;
        console.log("Mic re-enabled");
    }
}

// Mic control - FIXED
function muteMic() {
    if (processor && source) {
        try {
            processor.disconnect();
            source.disconnect();
            console.log(" Mic muted");
        } catch (e) {
            console.log(" Mic already disconnected");
        }
    }
    micEnabled = false;
}

function unmuteMic() {
    if (source && processor && audioContext && isRunning) {
        try {
            source.connect(processor);
            processor.connect(audioContext.destination);
            console.log(" Mic unmuted");
        } catch (e) {
            console.error(" Could not reconnect mic:", e);
        }
    }
    micEnabled = true;
}

// Reset silence timer
function resetSilenceTimer() {
    clearTimeout(silenceTimeout);
    silenceTimeout = setTimeout(() => {
        if (isRunning && !isAISpeaking) {
            console.log(" Silence timeout - auto-submitting answer");
            submitAnswer();
        }
    }, 10000); // 10 seconds of silence
}

// Start interview
async function startInterview() {
    if (isRunning) {
        console.warn(" Interview already running");
        return;
    }
    
    console.log(" Starting interview...");
    isRunning = true;

    // Upload resume and get session ID
    sessionId = await uploadResume();
    if (!sessionId) {
        console.error(" Failed to get session ID");
        isRunning = false;
        return;
    }

    const transcriptDiv = document.getElementById("transcript");
    const feedbackDiv = document.getElementById("feedback");

    transcriptDiv.textContent = "Interview starting...\n";
    feedbackDiv.textContent = "Feedback will appear here after the interview.";

    // Create WebSocket connection
    const wsUrl = `ws://localhost:8000/ws/interview?session_id=${sessionId}`;
    console.log(`🔌 Connecting to: ${wsUrl}`);
    
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log("✓ WebSocket connected");
        transcriptDiv.textContent += "✓ Connected to server\n";
    };

    ws.onmessage = async (event) => {
        if (!isRunning) return;

        // Handle JSON messages
        if (typeof event.data === "string") {
            try {
                const data = JSON.parse(event.data);
                console.log(" Received message:", data.type);

                switch (data.type) {
                    case "QUESTION":
                        transcriptDiv.textContent += `\n\n❓ Question: ${data.text}\n`;
                        transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
                        resetSilenceTimer();
                        break;

                    case "FINAL_TRANSCRIPT":
                        transcriptDiv.textContent += `\n You: ${data.text}`;
                        transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
                        break;

                    case "END":
                        console.log("🏁 Interview ended");
                        displaySummary(data.summary, transcriptDiv);
                        stopInterview();
                        break;

                    case "ERROR":
                        console.error(" Server error:", data.text);
                        alert(`Error: ${data.text}`);
                        stopInterview();
                        break;
                    
                    default:
                        console.warn(" Unknown message type:", data.type);
                }
            } catch (error) {
                console.error(" Failed to parse JSON message:", error);
            }
        }
        // Handle binary audio data (Blob)
        else if (event.data instanceof Blob) {
            console.log(`🎵 Received audio blob (${event.data.size} bytes)`);
            try {
                const arrayBuffer = await event.data.arrayBuffer();
                await playAudioBytes(arrayBuffer);
            } catch (error) {
                console.error(" Failed to process audio blob:", error);
            }
        }
    };

    ws.onerror = (error) => {
        console.error(" WebSocket error:", error);
        alert("WebSocket connection error! Check if server is running.");
    };

    ws.onclose = (event) => {
        console.log(`🔌 WebSocket closed (code: ${event.code}, reason: ${event.reason})`);
        isRunning = false;
    };

    // Initialize audio context and microphone
    try {
        console.log(" Initializing audio...");
        audioContext = new AudioContext({ sampleRate: 16000 });
        stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: 16000
            }
        });

        source = audioContext.createMediaStreamSource(stream);
        processor = audioContext.createScriptProcessor(4096, 1, 1);

        processor.onaudioprocess = (e) => {
            if (!isRunning || !micEnabled || isAISpeaking) return;

            const input = e.inputBuffer.getChannelData(0);
            
            // Send audio data to server
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(input.buffer);
            }

            resetSilenceTimer();
        };

        // Connect mic initially
        unmuteMic();
        
        console.log("Audio initialized");
        stopBtn.disabled = false;
        submitBtn.disabled = false;
        
    } catch (error) {
        console.error(" Failed to initialize audio:", error);
        alert("Microphone access denied or not available!");
        stopInterview();
    }
}

// Stop interview safely
function stopInterview() {
    if (!isRunning) return;

    console.log(" Stopping interview...");
    isRunning = false;
    clearTimeout(silenceTimeout);

    // Disconnect audio processor
    if (processor) {
        try {
            processor.disconnect();
        } catch (e) {}
        processor = null;
    }
    
    // Disconnect audio source
    if (source) {
        try {
            source.disconnect();
        } catch (e) {}
        source = null;
    }
    
    // Close audio context
    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
    
    // Stop media stream
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }

    // Close WebSocket
    if (ws && ws.readyState === WebSocket.OPEN) {
        try {
            ws.send(JSON.stringify({ text: "SUBMIT_ANSWER" }));
            ws.close();
        } catch (e) {
            console.log(" WebSocket already closing/closed");
        }
    }

    startBtn.disabled = false;
    stopBtn.disabled = true;
    submitBtn.disabled = true;
    
    console.log(" Interview stopped");
}

// Submit answer manually
function submitAnswer() {
    if (!isRunning || isAISpeaking) {
        console.warn(" Cannot submit: interview not running or AI is speaking");
        return;
    }
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        console.log("📤 Submitting answer...");
        ws.send(JSON.stringify({ text: "SUBMIT_ANSWER" }));
        resetSilenceTimer();
    } else {
        console.error("WebSocket not open");
    }
}

// Display interview summary
function displaySummary(summary, container) {
    if (!summary) {
        console.warn(" No summary data received");
        return;
    }

    console.log(" Displaying interview summary");

    const summaryDiv = document.createElement("div");
    summaryDiv.style.background = "#f3f4f6";
    summaryDiv.style.border = "1px solid #d1d5db";
    summaryDiv.style.borderRadius = "8px";
    summaryDiv.style.padding = "15px";
    summaryDiv.style.marginTop = "20px";
    summaryDiv.style.fontFamily = "monospace";
    summaryDiv.style.whiteSpace = "pre-wrap";

    let summaryText = `\n${"=".repeat(60)}\n`;
    summaryText += ` FINAL INTERVIEW SUMMARY\n`;
    summaryText += `${"=".repeat(60)}\n\n`;
    summaryText += `Average Score: ${summary.average_score}/10\n`;
    summaryText += `Result: ${summary.result}\n\n`;

    if (summary.questions && summary.questions.length > 0) {
        summary.questions.forEach((q, i) => {
            summaryText += `${"-".repeat(60)}\n`;
            summaryText += `Q${i + 1}: ${q}\n\n`;
            summaryText += `Your Answer:\n${summary.answers[i]}\n\n`;
            
            if (summary.scores && summary.scores[i]) {
                const scores = summary.scores[i];
                summaryText += `Scores:\n`;
                summaryText += `  • Correctness: ${scores.correctness}/10\n`;
                summaryText += `  • Depth: ${scores.depth}/10\n`;
                summaryText += `  • Clarity: ${scores.clarity}/10\n`;
                summaryText += `  • Final Score: ${scores.final_score}/10\n\n`;
            }
        });
    }

    if (summary.feedback) {
        summaryText += `${"-".repeat(60)}\n`;
        summaryText += `Overall Feedback:\n${summary.feedback}\n`;
    }

    summaryText += `${"=".repeat(60)}\n`;

    summaryDiv.textContent = summaryText;
    container.appendChild(summaryDiv);
    container.scrollTop = container.scrollHeight;
}

// Button event listeners
startBtn.addEventListener("click", async () => {
    console.log("Start button clicked");
    startBtn.disabled = true;
    await startInterview();
});

stopBtn.addEventListener("click", () => {
    console.log("Stop button clicked");
    stopInterview();
});

submitBtn.addEventListener("click", () => {
    console.log("Submit button clicked");
    submitAnswer();
});

// Log initial state
console.log("✓ Audio.js loaded successfully");