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

// Play WAV audio from server in chunks
async function playAudioBytes(bytes) {
    if (!bytes || !audioContext) return;

    isAISpeaking = true;
    micEnabled = false;
    submitBtn.disabled = true;

    const chunkSize = 1024 * 1024; // 1MB per chunk
    let offset = 0;

    while (offset < bytes.byteLength) {
        const chunk = bytes.slice(offset, offset + chunkSize);
        await decodeAndPlayChunk(chunk);
        offset += chunkSize;
    }

    isAISpeaking = false;
    micEnabled = true;
    submitBtn.disabled = false;
}

function decodeAndPlayChunk(chunk) {
    return new Promise((resolve) => {
        audioContext.decodeAudioData(chunk.slice(0), (buffer) => {
            const sourceNode = audioContext.createBufferSource();
            sourceNode.buffer = buffer;
            sourceNode.connect(audioContext.destination);

            sourceNode.onended = () => resolve();
            sourceNode.start(0);
        });
    });
}

// Mic control
function muteMic() {
    if (processor) processor.disconnect();
    micEnabled = false;
    console.log(" Mic muted");
}

function unmuteMic() {
    if (source && processor && audioContext) {
        source.connect(processor);
        processor.connect(audioContext.destination);
    }
    micEnabled = true;
    console.log(" Mic unmuted");
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

    ws.onmessage = async (event) => {
        if (!isRunning) return;

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
                    stopInterview();
                    break;

                case "ERROR":
                    alert(data.text);
                    stopInterview();
                    break;
            }
        } else if (event.data instanceof Blob) {
            const reader = new FileReader();
            reader.onload = async function () {
                const arrayBuffer = reader.result;
                await playAudioBytes(arrayBuffer);
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
        if (!isRunning || !micEnabled) return;

        const input = e.inputBuffer.getChannelData(0);
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(input.buffer);
        }

        resetSilenceTimer();
    };

    // Connect mic initially
    unmuteMic();

    stopBtn.disabled = false;
}

// Stop interview safely
function stopInterview() {
    if (!isRunning) return;

    isRunning = false;

    if (processor) processor.disconnect();
    if (source) source.disconnect();
    if (audioContext) audioContext.close();
    if (stream) stream.getTracks().forEach(track => track.stop());

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
    if (!isRunning || isAISpeaking) return; // Prevent submission while AI is speaking
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
    submitBtn.disabled = true; // Disabled until first question finishes
    await startInterview();
});

stopBtn.addEventListener("click", stopInterview);
submitBtn.addEventListener("click", submitAnswer);
