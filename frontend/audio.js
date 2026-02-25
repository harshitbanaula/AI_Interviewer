// frontend/audio.js
// ─── TIMER STATE ───
let warned10Min = false;
let warned5Min = false;
let bufferWarningShown = false;
let remainingSeconds = 0;
let timerInterval = null;
let inBufferTime = false;

// ─── AUDIO / WS STATE ───
let isUserSpeaking = false;
const SILENCE_THRESHOLD = 0.02;

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
let pingInterval = null;
let interviewEnded = false;

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
    const prefix = { "info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️" }[type] || "ℹ️";
    console.log(`[${timestamp}] ${prefix} ${message}`);
}

// ─── RESUME UPLOAD ───
async function uploadResume() {
    const file = resumeInput.files[0];
    if (!file) { log("No resume file selected", "error"); return null; }

    log(`Uploading resume: ${file.name}`, "info");
    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("http://localhost:8000/upload_resume", {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || await res.text());
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
    if (typeof seconds !== "number" || isNaN(seconds) || seconds < 0) return "00:00";
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
            if (!warned5Min) { warned5Min = true; alert("⏰ 5 minutes remaining!"); }
        } else if (seconds <= 600) {
            timerEl.classList.add("yellow");
            if (!warned10Min) { warned10Min = true; alert("⏰ 10 minutes remaining!"); }
        } else {
            timerEl.classList.add("green");
        }
    }
}

function startLocalCountdown() {
    if (timerInterval) return;
    timerInterval = setInterval(() => {
        if (!isRunning || remainingSeconds <= 0) return;
        remainingSeconds--;
        updateTimerUI(remainingSeconds, inBufferTime);
        if (remainingSeconds <= 0) stopTimer();
    }, 1000);
}

function stopTimer() {
    clearInterval(timerInterval);
    timerInterval = null;
}

// ─── COMPACT SINGLE-SCREEN UI ───

function showCurrentQuestion(questionText, questionNum) {
    const transcript = document.getElementById("transcript");
    transcript.innerHTML = `
        <div style="display:flex;flex-direction:column;height:100%;animation:fadeIn 0.4s ease-in;">
            <div style="display:flex;align-items:center;gap:12px;padding:12px 15px;
                        background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
                        border-radius:10px;margin-bottom:12px;">
                <div style="background:white;color:#667eea;width:35px;height:35px;border-radius:50%;
                            display:flex;align-items:center;justify-content:center;
                            font-size:16px;font-weight:bold;">${questionNum}</div>
                <div style="flex:1;color:white;">
                    <div style="font-weight:600;font-size:13px;">Question ${questionNum}/10</div>
                    <div style="font-size:11px;opacity:0.9;">Active</div>
                </div>
                <div style="background:rgba(255,255,255,0.2);padding:5px 12px;border-radius:20px;
                            font-size:11px;color:white;font-weight:600;display:flex;align-items:center;gap:5px;">
                    <div style="width:8px;height:8px;background:#f44336;border-radius:50%;animation:blink 1s infinite;"></div>
                    REC
                </div>
            </div>
            <div style="flex:1;background:linear-gradient(to bottom,#e3f2fd 0%,#f3e5f5 100%);
                        padding:20px;border-radius:10px;border-left:4px solid #2196F3;
                        overflow-y:auto;margin-bottom:12px;">
                <div style="color:#1976D2;font-size:12px;font-weight:600;margin-bottom:10px;
                            text-transform:uppercase;letter-spacing:0.5px;">❓ Your Question</div>
                <div style="color:#333;font-size:16px;line-height:1.6;font-weight:500;">${questionText}</div>
            </div>
            <div style="background:#fff3e0;padding:12px 15px;border-radius:8px;border:2px solid #FF9800;
                        display:flex;align-items:center;justify-content:center;gap:10px;">
                <span style="font-size:18px;">🎤</span>
                <span style="color:#f57c00;font-weight:600;font-size:14px;">Listening...</span>
            </div>
        </div>
        <style>
            @keyframes fadeIn { from{opacity:0} to{opacity:1} }
            @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
        </style>`;
}

function showProcessing(message = "Processing your answer...") {
    const transcript = document.getElementById("transcript");
    transcript.innerHTML = `
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;">
            <div style="width:60px;height:60px;border:4px solid #667eea;border-top:4px solid transparent;
                        border-radius:50%;animation:spin 1s linear infinite;margin-bottom:20px;"></div>
            <div style="color:#667eea;font-size:18px;font-weight:bold;margin-bottom:8px;">${message}</div>
            <div style="color:#999;font-size:13px;">Please wait...</div>
        </div>
        <style>@keyframes spin { to{transform:rotate(360deg)} }</style>`;
}

function showAnswerRecorded() {
    const transcript = document.getElementById("transcript");
    transcript.innerHTML = `
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;animation:fadeIn 0.4s ease-in;">
            <div style="width:70px;height:70px;background:#4CAF50;border-radius:50%;
                        display:flex;align-items:center;justify-content:center;margin-bottom:20px;
                        box-shadow:0 4px 15px rgba(76,175,80,0.4);">
                <span style="font-size:35px;color:white;">✓</span>
            </div>
            <div style="color:#2E7D32;font-size:20px;font-weight:bold;margin-bottom:8px;">Answer Recorded!</div>
            <div style="color:#666;font-size:14px;">Preparing next question...</div>
        </div>`;
}

function showQuestionSkipped() {
    const transcript = document.getElementById("transcript");
    transcript.innerHTML = `
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;animation:fadeIn 0.4s ease-in;">
            <div style="width:70px;height:70px;background:#FF9800;border-radius:50%;
                        display:flex;align-items:center;justify-content:center;margin-bottom:20px;
                        box-shadow:0 4px 15px rgba(255,152,0,0.4);">
                <span style="font-size:35px;">⏭️</span>
            </div>
            <div style="color:#F57C00;font-size:20px;font-weight:bold;margin-bottom:8px;">Question Skipped</div>
            <div style="color:#666;font-size:14px;margin-bottom:10px;">Moving to next question...</div>
            <div style="color:#999;font-size:12px;padding:8px 12px;background:rgba(255,152,0,0.1);border-radius:6px;">Score: 0 points</div>
        </div>`;
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
        await new Promise(resolve => { src.onended = resolve; src.start(0); });
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
    try { processor?.disconnect(); source?.disconnect(); } catch {}
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
    if (!isRunning || isAISpeaking) return;
    silenceTimeout = setTimeout(() => {
        if (isRunning && !isAISpeaking) {
            log("10s silence — auto submitting", "info");
            submitAnswer();
        }
    }, 10000);
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
    transcript.textContent += "╚═══════════════════════════════════════════════════════════════════╝\n\n";

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
    transcript.textContent += `${resultIcon} Final Result:       ${summary.result}\n`;
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
    transcript.textContent += (summary.feedback && summary.feedback.trim())
        ? summary.feedback + "\n"
        : "⏳ Feedback unavailable.\n";

    transcript.textContent += "\n\n╔═══════════════════════════════════════════════════════════════════╗\n";
    transcript.textContent += "║          Thank you for completing the interview! 🎉              ║\n";
    transcript.textContent += "╚═══════════════════════════════════════════════════════════════════╝\n";
    transcript.scrollTop = 0;
}

// ─── START INTERVIEW ───
async function startInterview() {
    // FIX 5: Guard against duplicate calls
    if (isRunning) { log("Already running", "warning"); return; }

    log("Starting interview...", "info");
    isRunning = true;
    interviewEnded = false;   // FIX 4: reset end flag
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
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;">
            <div style="width:80px;height:80px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
                        border-radius:50%;display:flex;align-items:center;justify-content:center;
                        margin-bottom:20px;animation:pulse 2s infinite;">
                <span style="font-size:40px;">🚀</span>
            </div>
            <div style="font-size:22px;font-weight:bold;color:#667eea;margin-bottom:10px;">Starting Interview</div>
            <div style="color:#666;font-size:14px;">Connecting...</div>
        </div>
        <style>@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}</style>`;

    // Initialize audio
    try {
        log("Requesting microphone...", "info");
        audioContext = new AudioContext({ sampleRate: 16000 });
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        log("Microphone granted", "success");

        source = audioContext.createMediaStreamSource(stream);
        processor = audioContext.createScriptProcessor(4096, 1, 1);

        processor.onaudioprocess = function(e) {
            if (!isRunning || !micEnabled) return;
            if (!ws || ws.readyState !== WebSocket.OPEN) return;

            const floatData = e.inputBuffer.getChannelData(0);
            let sum = 0;
            for (let i = 0; i < floatData.length; i++) sum += Math.abs(floatData[i]);
            const avg = sum / floatData.length;
            const speakingNow = avg > SILENCE_THRESHOLD;

            if (speakingNow && !isUserSpeaking) {
                isUserSpeaking = true;
                resetSilenceTimer();
            }
            if (!speakingNow && isUserSpeaking) {
                isUserSpeaking = false;
            }

            ws.send(floatTo16BitPCM(floatData));
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
    log("Connecting to WebSocket", "info");
    ws = new WebSocket(wsUrl);
    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
        log("WebSocket connected", "success");

        stopBtn.disabled = false;
        submitBtn.disabled = false;
        skipBtn.disabled = false;

        // FIX 2: Send PING every 5s to keep connection alive through proxy/browser timeouts
        // This is the client-side complement to server-side KEEPALIVE
        pingInterval = setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ action: "PING" }));
            } else {
                clearInterval(pingInterval);
                pingInterval = null;
            }
        }, 5000);

        transcript.innerHTML = `
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;">
                <div style="width:80px;height:80px;background:#4CAF50;border-radius:50%;
                            display:flex;align-items:center;justify-content:center;margin-bottom:20px;">
                    <span style="font-size:40px;color:white;">✓</span>
                </div>
                <div style="font-size:22px;font-weight:bold;color:#4CAF50;margin-bottom:10px;">Connected!</div>
                <div style="color:#666;font-size:14px;">Loading question...</div>
            </div>`;
    };

    ws.onmessage = async (event) => {
        if (typeof event.data === "string") {
            const data = JSON.parse(event.data);

            if (data.type !== "TIMER_UPDATE" && data.type !== "KEEPALIVE") {
                log(`← ${data.type}`, "info");
            }

            switch (data.type) {

                case "KEEPALIVE":
                    // FIX 1: Handle KEEPALIVE — server is alive, just processing
                    // No action needed, receiving it is enough to reset browser timeout
                    break;

                case "TIMER_UPDATE":
                    remainingSeconds = data.remaining_seconds;
                    const nowInBuffer = data.in_buffer_time || false;
                    if (nowInBuffer && !inBufferTime) {
                        inBufferTime = true;
                        if (!bufferWarningShown) {
                            bufferWarningShown = true;
                            alert("⏰ Main time expired! Buffer time remaining.");
                        }
                    }
                    updateTimerUI(remainingSeconds, inBufferTime);
                    if (!timerInterval) startLocalCountdown();
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
                    break;

                case "FINAL_TRANSCRIPT":
                    log("Answer recorded", "info");
                    if (data.text && data.text.includes("skipped")) {
                        showQuestionSkipped();
                    } else {
                        showAnswerRecorded();
                    }
                    break;

                case "END":
                    log("Interview ended cleanly", "success");
                    interviewEnded = true;   // FIX 4: mark clean end
                    displayResults(data.summary);
                    stopInterview(false);
                    break;

                case "ERROR":
                    log(`Server error: ${data.text}`, "error");
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
        log("WebSocket error", "error");
        console.error(error);
    };

    ws.onclose = (event) => {
        log(`WebSocket closed: code=${event.code}`, "warning");

        // FIX 2: Clear ping interval when connection closes
        if (pingInterval) {
            clearInterval(pingInterval);
            pingInterval = null;
        }

        // FIX 4: Only show error UI if we didn't get a clean END
        if (isRunning && !interviewEnded) {
            log("Unexpected close — interview was still running", "error");
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

    // FIX 3: Always clear ping interval on stop
    if (pingInterval) {
        clearInterval(pingInterval);
        pingInterval = null;
    }

    try {
        muteMic();
        processor?.disconnect();
        source?.disconnect();
        audioContext?.close();
        stream?.getTracks().forEach(t => t.stop());
        ws?.close();
        log("Stopped cleanly", "success");
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
        log(`Cannot submit: WS state=${ws?.readyState}`, "warning");
    }
}

// ─── SKIP QUESTION ───
function skipQuestion() {
    if (ws?.readyState === WebSocket.OPEN && isRunning) {
        log("→ Skipping question", "warning");
        ws.send(JSON.stringify({ action: "SKIP_QUESTION" }));
        clearTimeout(silenceTimeout);
    } else {
        log(`Cannot skip: WS state=${ws?.readyState}`, "warning");
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