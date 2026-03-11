// CONSTANTS

const WS_URL_BASE       = "ws://localhost:8000/ws/interview";
const API_URL_BASE      = "http://localhost:8000";
const STORAGE_KEY       = "ai_interview_session";
const SILENCE_THRESHOLD = 0.02;
const SILENCE_DELAY_MS  = 10_000;
const RECONNECT_FAST_MS = 2_000;
const RECONNECT_PROC_MS = 6_000;
const MAX_RECONNECT     = 5;

 // STATE
 
let sessionId      = null;
let interviewEnded = false;
let isDiscarding   = false;

let ws                = null;
let pingInterval      = null;
let reconnectTimer    = null;
let reconnectAttempts = 0;

let audioContext = null;
let processor    = null;
let source       = null;
let stream       = null;
let isRunning    = false;
let micEnabled   = false;
let isAISpeaking = false;

let isProcessing     = false;
let isUserSpeaking   = false;
let silenceTimeout   = null;
let audioChunksReady = false;

let remainingSeconds   = 0;
let inBufferTime       = false;
let timerInterval      = null;
let warned10Min        = false;
let warned5Min         = false;
let bufferWarningShown = false;

let currentQuestionNumber = 0;
let currentQuestion       = null;

 // UI ELEMENT REFS
 
const resumeInput = document.getElementById("resumeFile");
const startBtn    = document.getElementById("startBtn");
const stopBtn     = document.getElementById("stopBtn");
const submitBtn   = document.getElementById("submitBtn");
const skipBtn     = document.getElementById("skipBtn");

 // LOGGING

function log(message, type = "info") {
    const prefix = { info: "ℹ️", success: "✅", error: "❌", warning: "⚠️" }[type] || "ℹ️";
    console.log(`[${new Date().toLocaleTimeString()}] ${prefix} ${message}`);
}

// BEFOREUNLOAD WARNING

window.addEventListener("beforeunload", (e) => {
    if (isRunning && !interviewEnded) {
        // Standard way to trigger the native browser warning dialog.
        // returnValue must be set for older browsers; preventDefault for modern ones.
        e.preventDefault();
        e.returnValue = "Your interview is in progress. If you leave, your progress will be saved and you can resume later.";
        return e.returnValue;
    }
});

// LOCAL-STORAGE HELPERS

function saveSessionToStorage(sid) {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ sessionId: sid }));
    } catch (e) {
        log(`localStorage write failed: ${e.message}`, "warning");
    }
}

function loadSessionFromStorage() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return null;
        const data = JSON.parse(raw);
        return data?.sessionId || null;
    } catch (e) {
        return null;
    }
}

function clearSessionFromStorage() {
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) { /* non-fatal */ }
}


// TIMER HELPERS

function formatTime(seconds) {
    if (typeof seconds !== "number" || isNaN(seconds) || seconds < 0) return "00:00";
    const m = Math.floor(seconds / 60).toString().padStart(2, "0");
    const s = Math.floor(seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
}

function updateTimerUI(seconds, isBuffer = false) {
    const timerEl = document.getElementById("timer");
    if (!timerEl || typeof seconds !== "number" || isNaN(seconds)) return;

    timerEl.textContent = `${isBuffer ? "⏰ BUFFER: " : "⏱️ "}${formatTime(seconds)}`;
    timerEl.classList.remove("green", "yellow", "red");

    if (isBuffer) {
        timerEl.classList.add("red");
    } else if (seconds <= 300) {
        timerEl.classList.add("red");
        if (!warned5Min) { warned5Min = true; showToast("⏰ 5 minutes remaining!", "warning"); }
    } else if (seconds <= 600) {
        timerEl.classList.add("yellow");
        if (!warned10Min) { warned10Min = true; showToast("⏰ 10 minutes remaining!", "warning"); }
    } else {
        timerEl.classList.add("green");
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

// TOAST NOTIFICATIONS

function showToast(message, type = "info") {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        container.style.cssText = `
            position:fixed;top:20px;right:20px;z-index:9999;
            display:flex;flex-direction:column;gap:8px;max-width:320px;`;
        document.body.appendChild(container);
    }

    const colours = { info: "#2196F3", success: "#4CAF50", warning: "#FF9800", error: "#f44336" };
    const toast = document.createElement("div");
    toast.style.cssText = `
        background:${colours[type] || colours.info};color:white;
        padding:12px 16px;border-radius:8px;font-size:14px;font-weight:500;
        box-shadow:0 4px 12px rgba(0,0,0,0.2);animation:slideIn 0.3s ease-out;`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = "slideOut 0.3s ease-in";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

(function injectToastStyles() {
    if (document.getElementById("toast-styles")) return;
    const style = document.createElement("style");
    style.id = "toast-styles";
    style.textContent = `
        @keyframes slideIn  { from{opacity:0;transform:translateX(100%)} to{opacity:1;transform:translateX(0)} }
        @keyframes slideOut { from{opacity:1;transform:translateX(0)} to{opacity:0;transform:translateX(100%)} }`;
    document.head.appendChild(style);
})();

// RESUME BANNER


function showResumeBanner(interruptedSessionId) {
    document.getElementById("resume-banner")?.remove();

    const banner = document.createElement("div");
    banner.id = "resume-banner";
    banner.style.cssText = `
        position:fixed;top:0;left:0;right:0;z-index:10000;
        background:linear-gradient(135deg,#1e3a5f 0%,#2d6a4f 100%);
        color:white;padding:18px 28px;
        display:flex;align-items:center;justify-content:space-between;
        box-shadow:0 4px 24px rgba(0,0,0,0.4);flex-wrap:wrap;gap:12px;`;

    banner.innerHTML = `
        <div style="display:flex;align-items:center;gap:14px;">
            <span style="font-size:28px;">🔄</span>
            <div>
                <div style="font-weight:700;font-size:16px;margin-bottom:2px;">
                    Interview In Progress
                </div>
                <div style="font-size:12px;opacity:0.85;">
                    You were disconnected. Your progress is saved — what would you like to do?
                </div>
            </div>
        </div>

        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px;">

            <div style="display:flex;gap:10px;">
                <!-- Resume Button -->
                <button id="resume-btn" style="
                    background:#22c55e;color:white;border:none;
                    padding:10px 20px;border-radius:8px;
                    font-weight:700;font-size:14px;cursor:pointer;
                    box-shadow:0 2px 8px rgba(34,197,94,0.4);
                    transition:opacity 0.2s;">
                    ▶ Resume Interview
                </button>

                <!-- Submit Button -->
                <button id="submit-interrupted-btn" style="
                    background:#f59e0b;color:white;border:none;
                    padding:10px 20px;border-radius:8px;
                    font-weight:700;font-size:14px;cursor:pointer;
                    box-shadow:0 2px 8px rgba(245,158,11,0.4);
                    transition:opacity 0.2s;">
                    🏁 Submit Interview
                </button>
            </div>

            <!-- Abandon link -->
            <button id="abandon-btn" style="
                background:none;border:none;color:rgba(255,255,255,0.55);
                font-size:11px;cursor:pointer;text-decoration:underline;
                padding:2px 4px;transition:color 0.2s;">
                Abandon interview (no results)
            </button>

        </div>`;

    document.body.prepend(banner);

    // ── Resume ───────────────────────────────────────────────────────────────
    document.getElementById("resume-btn").addEventListener("click", async () => {
        banner.remove();
        await resumeInterview(interruptedSessionId);
    });

    // ── Submit Interrupted ───────────────────────────────────────────────────
    document.getElementById("submit-interrupted-btn").addEventListener("click", async () => {
        banner.remove();
        await submitInterruptedSession(interruptedSessionId);
    });

    // ── Abandon ──────────────────────────────────────────────────────────────
    document.getElementById("abandon-btn").addEventListener("click", () => {
        showAbandonConfirmation(interruptedSessionId, banner);
    });
}

function hideResumeBanner() {
    document.getElementById("resume-banner")?.remove();
}


// ABANDON CONFIRMATION POPUP
function showAbandonConfirmation(interruptedSessionId, bannerEl) {
    document.getElementById("abandon-confirm")?.remove();

    const popup = document.createElement("div");
    popup.id = "abandon-confirm";
    popup.style.cssText = `
        position:fixed;top:0;left:0;right:0;bottom:0;z-index:10001;
        background:rgba(0,0,0,0.65);
        display:flex;align-items:center;justify-content:center;`;

    popup.innerHTML = `
        <div style="
            background:white;border-radius:14px;padding:32px 28px;
            max-width:420px;width:90%;text-align:center;
            box-shadow:0 20px 60px rgba(0,0,0,0.4);">

            <div style="font-size:48px;margin-bottom:16px;">⚠️</div>

            <div style="font-size:18px;font-weight:700;color:#1a1a1a;margin-bottom:10px;">
                Abandon Interview?
            </div>

            <div style="font-size:13px;color:#666;line-height:1.6;margin-bottom:24px;">
                This will permanently discard your interview session.<br/>
                <strong>You will not receive any results or feedback.</strong><br/>
                This action cannot be undone.
            </div>

            <div style="display:flex;gap:12px;justify-content:center;">
                <button id="abandon-cancel-btn" style="
                    background:#f3f4f6;color:#374151;border:none;
                    padding:12px 24px;border-radius:8px;
                    font-weight:600;font-size:14px;cursor:pointer;">
                    ← Go Back
                </button>
                <button id="abandon-confirm-btn" style="
                    background:#ef4444;color:white;border:none;
                    padding:12px 24px;border-radius:8px;
                    font-weight:700;font-size:14px;cursor:pointer;">
                    Yes, Abandon
                </button>
            </div>
        </div>`;

    document.body.appendChild(popup);

    // Cancel — close popup, re-show banner
    document.getElementById("abandon-cancel-btn").addEventListener("click", () => {
        popup.remove();
        // Re-show banner so they can choose again
        showResumeBanner(interruptedSessionId);
    });

    // Confirm abandon
    document.getElementById("abandon-confirm-btn").addEventListener("click", () => {
        popup.remove();
        if (bannerEl) bannerEl.remove();
        discardInterruptedSession();
        showToast("Interview abandoned.", "info");
        log("Interview abandoned by candidate", "warning");
    });
}

// SUBMIT INTERRUPTED SESSION

 async function submitInterruptedSession(interruptedSessionId) {
    log(`Submitting interrupted session: ${interruptedSessionId}`, "info");

    const transcript = document.getElementById("transcript");
    if (transcript) {
        transcript.innerHTML = `
            <div style="display:flex;flex-direction:column;align-items:center;
                        justify-content:center;height:100%;">
                <div style="width:60px;height:60px;border:4px solid #f59e0b;
                            border-top:4px solid transparent;border-radius:50%;
                            animation:spin 1s linear infinite;margin-bottom:20px;"></div>
                <div style="color:#f59e0b;font-size:18px;font-weight:bold;margin-bottom:8px;">
                    Submitting Interview…
                </div>
                <div style="color:#999;font-size:13px;">
                    Generating your results and feedback…
                </div>
            </div>
            <style>@keyframes spin { to{transform:rotate(360deg)} }</style>`;
    }

    startBtn.disabled  = true;
    stopBtn.disabled   = true;
    submitBtn.disabled = true;
    skipBtn.disabled   = true;

    try {
        const res = await fetch(
            `${API_URL_BASE}/finalize_session?session_id=${interruptedSessionId}`,
            { method: "POST" }
        );

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Finalization failed");
        }

        // Success — show results
        interviewEnded = true;
        clearSessionFromStorage();
        showToast("✅ Interview submitted successfully!", "success");
        displayResults(data.summary);
        stopInterview(false);

        log("Interrupted session submitted via REST", "success");

    } catch (err) {
        log(`Submit interrupted failed: ${err.message}`, "error");
        showToast(`❌ Could not submit: ${err.message}`, "error");

        // Restore UI so they can try resume instead
        startBtn.disabled = false;
        if (transcript) {
            transcript.innerHTML = `
                <div style="display:flex;flex-direction:column;align-items:center;
                            justify-content:center;height:100%;gap:16px;">
                    <div style="font-size:40px;">❌</div>
                    <div style="color:#ef4444;font-size:16px;font-weight:bold;">
                        Submission Failed
                    </div>
                    <div style="color:#666;font-size:13px;text-align:center;">
                        ${err.message}<br/>Try resuming the interview instead.
                    </div>
                    <button onclick="showResumeBanner('${interruptedSessionId}')"
                        style="background:#667eea;color:white;border:none;
                               padding:10px 20px;border-radius:8px;
                               font-weight:700;cursor:pointer;font-size:14px;">
                        Show Options Again
                    </button>
                </div>`;
        }
    }
}

 // CONNECTION LOST BANNER
 
function showConnectionLostBanner(message = "Connection lost. Reconnecting…") {
    let banner = document.getElementById("connection-lost-banner");
    if (banner) { banner.querySelector(".clb-msg").textContent = message; return; }

    banner = document.createElement("div");
    banner.id = "connection-lost-banner";
    banner.style.cssText = `
        position:fixed;bottom:20px;left:50%;transform:translateX(-50%);z-index:9998;
        background:#f44336;color:white;padding:14px 24px;border-radius:12px;
        display:flex;align-items:center;gap:12px;
        box-shadow:0 4px 20px rgba(244,67,54,0.4);`;
    banner.innerHTML = `
        <div style="width:16px;height:16px;border:3px solid white;
                    border-top:3px solid transparent;border-radius:50%;
                    animation:spin 0.8s linear infinite;flex-shrink:0;"></div>
        <span class="clb-msg" style="font-weight:600;font-size:14px;">${message}</span>
        <style>@keyframes spin { to{transform:rotate(360deg)} }</style>`;
    document.body.appendChild(banner);
}

function hideConnectionLostBanner() {
    document.getElementById("connection-lost-banner")?.remove();
}


// UI SCREENS


function showCurrentQuestion(questionText, questionNum) {
    const transcript = document.getElementById("transcript");
    transcript.innerHTML = `
        <div style="display:flex;flex-direction:column;height:100%;animation:fadeIn 0.4s ease-in;">
            <div style="display:flex;align-items:center;gap:12px;padding:12px 15px;
                        background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
                        border-radius:10px;margin-bottom:12px;">
                <div style="background:white;color:#667eea;width:35px;height:35px;
                            border-radius:50%;display:flex;align-items:center;
                            justify-content:center;font-size:16px;font-weight:bold;">
                    ${questionNum}
                </div>
                <div style="flex:1;color:white;">
                    <div style="font-weight:600;font-size:13px;">Question ${questionNum}/10</div>
                    <div style="font-size:11px;opacity:0.9;">Active</div>
                </div>
                <div style="background:rgba(255,255,255,0.2);padding:5px 12px;border-radius:20px;
                            font-size:11px;color:white;font-weight:600;
                            display:flex;align-items:center;gap:5px;">
                    <div style="width:8px;height:8px;background:#f44336;border-radius:50%;
                                animation:blink 1s infinite;"></div>
                    REC
                </div>
            </div>
            <div style="flex:1;background:linear-gradient(to bottom,#e3f2fd 0%,#f3e5f5 100%);
                        padding:20px;border-radius:10px;border-left:4px solid #2196F3;
                        overflow-y:auto;margin-bottom:12px;">
                <div style="color:#1976D2;font-size:12px;font-weight:600;margin-bottom:10px;
                            text-transform:uppercase;letter-spacing:0.5px;">❓ Your Question</div>
                <div style="color:#333;font-size:16px;line-height:1.6;font-weight:500;">
                    ${questionText}
                </div>
            </div>
            <div style="background:#fff3e0;padding:12px 15px;border-radius:8px;
                        border:2px solid #FF9800;
                        display:flex;align-items:center;justify-content:center;gap:10px;">
                <span style="font-size:18px;">🎤</span>
                <span style="color:#f57c00;font-weight:600;font-size:14px;">Listening…</span>
            </div>
        </div>
        <style>
            @keyframes fadeIn { from{opacity:0} to{opacity:1} }
            @keyframes blink  { 0%,100%{opacity:1} 50%{opacity:0.3} }
        </style>`;
}

function showProcessing(message = "Processing your answer…") {
    const transcript = document.getElementById("transcript");
    transcript.innerHTML = `
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;height:100%;">
            <div style="width:60px;height:60px;border:4px solid #667eea;
                        border-top:4px solid transparent;border-radius:50%;
                        animation:spin 1s linear infinite;margin-bottom:20px;"></div>
            <div style="color:#667eea;font-size:18px;font-weight:bold;margin-bottom:8px;">
                ${message}
            </div>
            <div style="color:#999;font-size:13px;">Please wait…</div>
        </div>
        <style>@keyframes spin { to{transform:rotate(360deg)} }</style>`;
}

function showAnswerRecorded() {
    const transcript = document.getElementById("transcript");
    transcript.innerHTML = `
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;height:100%;animation:fadeIn 0.4s ease-in;">
            <div style="width:70px;height:70px;background:#4CAF50;border-radius:50%;
                        display:flex;align-items:center;justify-content:center;
                        margin-bottom:20px;box-shadow:0 4px 15px rgba(76,175,80,0.4);">
                <span style="font-size:35px;color:white;">✓</span>
            </div>
            <div style="color:#2E7D32;font-size:20px;font-weight:bold;margin-bottom:8px;">
                Answer Recorded!
            </div>
            <div style="color:#666;font-size:14px;">Preparing next question…</div>
        </div>`;
}

function showQuestionSkipped() {
    const transcript = document.getElementById("transcript");
    transcript.innerHTML = `
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;height:100%;animation:fadeIn 0.4s ease-in;">
            <div style="width:70px;height:70px;background:#FF9800;border-radius:50%;
                        display:flex;align-items:center;justify-content:center;
                        margin-bottom:20px;box-shadow:0 4px 15px rgba(255,152,0,0.4);">
                <span style="font-size:35px;">⏭️</span>
            </div>
            <div style="color:#F57C00;font-size:20px;font-weight:bold;margin-bottom:8px;">
                Question Skipped
            </div>
            <div style="color:#666;font-size:14px;margin-bottom:10px;">
                Moving to next question…
            </div>
        </div>`;
}


// AUDIO HELPERS


function floatTo16BitPCM(float32Array) {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view   = new DataView(buffer);
    for (let i = 0, offset = 0; i < float32Array.length; i++, offset += 2) {
        const s = Math.max(-1, Math.min(1, float32Array[i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
    return buffer;
}

async function playAudioBytes(arrayBuffer) {
    if (!arrayBuffer || !audioContext) return;

    isAISpeaking = true;
    muteMic();
    submitBtn.disabled = true;
    skipBtn.disabled   = true;

    try {
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        const src = audioContext.createBufferSource();
        src.buffer = audioBuffer;
        src.connect(audioContext.destination);
        await new Promise(resolve => { src.onended = resolve; src.start(0); });
    } catch (e) {
        log(`TTS decode/play error: ${e.message}`, "error");
    } finally {
        isAISpeaking = false;
        if (isRunning && !isProcessing) {
            unmuteMic();
            submitBtn.disabled = false;
            skipBtn.disabled   = false;
            resetSilenceTimer();
        }
    }
}


// MIC CONTROL — flag-only, no node disconnect (prevents WS drop on Chrome/Windows)


function muteMic() {
    micEnabled = false;
}

function unmuteMic() {
    if (isRunning) micEnabled = true;
}

// SILENCE TIMER

function resetSilenceTimer() {
    clearTimeout(silenceTimeout);
    if (!isRunning || isAISpeaking || isProcessing) return;
    silenceTimeout = setTimeout(() => {
        if (isRunning && !isAISpeaking && !isProcessing) {
            log("Silence timeout — auto submitting", "info");
            submitAnswer();
        }
    }, SILENCE_DELAY_MS);
}

// RESUME UPLOAD

async function uploadResume() {
    const file = resumeInput.files[0];
    if (!file) { log("No file selected", "error"); return null; }

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res  = await fetch(`${API_URL_BASE}/upload_resume`, { method: "POST", body: formData });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || data.detail || "Upload failed");
        log(`Resume uploaded. Session: ${data.session_id}`, "success");
        return data.session_id;
    } catch (err) {
        log(`Upload failed: ${err.message}`, "error");
        alert(`Resume upload failed: ${err.message}`);
        return null;
    }
}


// MICROPHONE INIT


async function initMicrophone() {
    teardownAudio();

    try {
        audioContext = new AudioContext({ sampleRate: 16000 });
        stream       = await navigator.mediaDevices.getUserMedia({ audio: true });
        source       = audioContext.createMediaStreamSource(stream);
        processor    = audioContext.createScriptProcessor(4096, 1, 1);

        processor.onaudioprocess = (e) => {
            if (!isRunning || !micEnabled) return;
            if (!ws || ws.readyState !== WebSocket.OPEN) return;

            const floatData   = e.inputBuffer.getChannelData(0);
            let sum = 0;
            for (let i = 0; i < floatData.length; i++) sum += Math.abs(floatData[i]);
            const avg         = sum / floatData.length;
            const speakingNow = avg > SILENCE_THRESHOLD;

            if (speakingNow && !isUserSpeaking) { isUserSpeaking = true; resetSilenceTimer(); }
            if (!speakingNow && isUserSpeaking)  { isUserSpeaking = false; }

            ws.send(floatTo16BitPCM(floatData));
        };

        source.connect(processor);
        processor.connect(audioContext.destination);
        micEnabled = true;
        log("Microphone ready", "success");
        return true;
    } catch (err) {
        log(`Microphone failed: ${err.message}`, "error");
        return false;
    }
}

function teardownAudio() {
    micEnabled = false;
    try { processor?.disconnect(); }                        catch {}
    try { source?.disconnect(); }                           catch {}
    try { audioContext?.close(); }                          catch {}
    try { stream?.getTracks().forEach(t => t.stop()); }    catch {}
    audioContext = null; processor = null; source = null; stream = null;
}


// WEBSOCKET — SINGLE SHARED CONNECT FUNCTION


function connectWebSocket() {
    if (!sessionId) { log("connectWebSocket called with no sessionId", "error"); return; }

    if (ws) {
        try { ws.onopen = ws.onmessage = ws.onerror = ws.onclose = null; ws.close(); } catch {}
        ws = null;
    }
    if (pingInterval) { clearInterval(pingInterval); pingInterval = null; }

    const wsUrl = `${WS_URL_BASE}?session_id=${sessionId}`;
    log(`Connecting WebSocket: ${wsUrl}`, "info");
    ws = new WebSocket(wsUrl);
    ws.binaryType = "arraybuffer";

    // ── onopen 
    ws.onopen = () => {
        log("WebSocket connected", "success");
        hideConnectionLostBanner();
        reconnectAttempts = 0;

        stopBtn.disabled   = false;
        submitBtn.disabled = false;
        skipBtn.disabled   = false;

        pingInterval = setInterval(() => {
            if (ws?.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ action: "PING" }));
            } else {
                clearInterval(pingInterval);
                pingInterval = null;
            }
        }, 5000);
    };

    // ── onmessage
    ws.onmessage = async (event) => {
        if (typeof event.data !== "string") {
            await playAudioBytes(event.data);
            return;
        }

        let data;
        try { data = JSON.parse(event.data); } catch { return; }

        if (data.type !== "TIMER_UPDATE" && data.type !== "KEEPALIVE") {
            log(`← ${data.type}`, "info");
        }

        switch (data.type) {

            case "KEEPALIVE": {
                break;
            }

            case "TIMER_UPDATE": {
                remainingSeconds = data.remaining_seconds;
                const nowBuffer  = data.in_buffer_time || false;
                if (nowBuffer && !inBufferTime) {
                    inBufferTime = true;
                    if (!bufferWarningShown) {
                        bufferWarningShown = true;
                        showToast("⏰ Main time expired! Buffer time remaining.", "warning");
                    }
                }
                updateTimerUI(remainingSeconds, inBufferTime);
                if (!timerInterval) startLocalCountdown();
                break;
            }

            case "BUFFER_TIME_WARNING": {
                inBufferTime = true;
                if (!bufferWarningShown) {
                    bufferWarningShown = true;
                    showToast(data.message, "warning");
                }
                break;
            }

            case "RESUMED": {
                log(
                    `Resumed: ${data.questions_answered} answered, ${data.remaining_seconds}s left`,
                    "success",
                );
                showToast("✅ Interview resumed!", "success");

                currentQuestionNumber = data.questions_answered;
                remainingSeconds      = data.remaining_seconds;
                inBufferTime          = data.in_buffer_time || false;
                updateTimerUI(remainingSeconds, inBufferTime);
                if (!timerInterval) startLocalCountdown();

                if (data.is_processing) {
                    showProcessing("Resuming interview…");
                }
                break;
            }

            case "QUESTION": {
                currentQuestionNumber++;
                currentQuestion  = data.text;
                audioChunksReady = false;
                isProcessing     = false;
                log(`Question ${currentQuestionNumber} received`, "info");
                showCurrentQuestion(data.text, currentQuestionNumber);
                break;
            }

            case "TTS_START": {
                submitBtn.disabled = true;
                skipBtn.disabled   = true;
                break;
            }

            case "TTS_END": {
                audioChunksReady = true;
                if (!isAISpeaking && !isProcessing && isRunning) {
                    unmuteMic();
                    submitBtn.disabled = false;
                    skipBtn.disabled   = false;
                    resetSilenceTimer();
                }
                break;
            }

            case "FINAL_TRANSCRIPT": {
                log("Answer acknowledged by server", "info");
                if (data.text?.includes("skipped")) {
                    showQuestionSkipped();
                } else {
                    showAnswerRecorded();
                }
                break;
            }

            case "END": {
                log("Interview ended cleanly", "success");
                interviewEnded = true;
                clearSessionFromStorage();
                displayResults(data.summary);
                stopInterview(false);
                break;
            }

            case "ERROR": {
                log(`Server error: ${data.text}`, "error");
                showToast(`❌ ${data.text}`, "error");
                if (data.text?.includes("expired") || data.text?.includes("Invalid")) {
                    interviewEnded = true;
                    clearSessionFromStorage();
                }
                stopInterview(true);
                break;
            }
        }
    };

    // ── onerror 
    ws.onerror = (error) => {
        log("WebSocket error", "error");
        console.error(error);
    };

    // ── onclose
    ws.onclose = (event) => {
        log(`WebSocket closed: code=${event.code}`, "warning");

        if (pingInterval) { clearInterval(pingInterval); pingInterval = null; }

        if (sessionId && !interviewEnded && !isDiscarding) {
            saveSessionToStorage(sessionId);
        }

        if (interviewEnded || isDiscarding || !isRunning) return;

        if (reconnectAttempts >= MAX_RECONNECT) {
            log(`Max reconnect attempts (${MAX_RECONNECT}) reached`, "error");
            showConnectionLostBanner(
                `Could not reconnect after ${MAX_RECONNECT} attempts. Please refresh.`
            );
            stopInterview(true);
            return;
        }

        const delay = isProcessing ? RECONNECT_PROC_MS : RECONNECT_FAST_MS;

        if (isProcessing) {
            showProcessing("Processing your answer…");
        } else {
            showConnectionLostBanner("Connection lost. Reconnecting…");
        }

        if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }

        reconnectAttempts++;

        reconnectTimer = setTimeout(async () => {
            reconnectTimer = null;
            if (interviewEnded || isDiscarding || !isRunning) return;

            log(`Reconnect attempt ${reconnectAttempts}/${MAX_RECONNECT}…`, "info");
            isAISpeaking = false;

            const micOk = await initMicrophone();
            if (!micOk) {
                showConnectionLostBanner("Mic unavailable — check browser permissions");
                return;
            }

            connectWebSocket();
        }, delay);
    };
}

 
// START INTERVIEW (fresh)


async function startInterview() {
    if (isRunning) { log("Already running", "warning"); return; }

    resetInterviewState();
    isRunning = true;
    startBtn.disabled = true;

    const transcript = document.getElementById("transcript");
    transcript.innerHTML = `
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;height:100%;">
            <div style="width:80px;height:80px;
                        background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
                        border-radius:50%;display:flex;align-items:center;
                        justify-content:center;margin-bottom:20px;">
                <span style="font-size:40px;">🚀</span>
            </div>
            <div style="font-size:22px;font-weight:bold;color:#667eea;margin-bottom:10px;">
                Starting Interview
            </div>
            <div style="color:#666;font-size:14px;">Uploading resume…</div>
        </div>`;

    sessionId = await uploadResume();
    if (!sessionId) { isRunning = false; startBtn.disabled = false; return; }

    saveSessionToStorage(sessionId);

    const micOk = await initMicrophone();
    if (!micOk) {
        alert("Microphone access denied. Please allow microphone and try again.");
        stopInterview(true);
        return;
    }

    connectWebSocket();
}

//RESUME INTERVIEW

async function resumeInterview(existingSessionId) {
    if (isRunning) { log("Already running", "warning"); return; }

    log(`Resuming session: ${existingSessionId}`, "info");
    resetInterviewState();
    isRunning = true;
    sessionId = existingSessionId;
    saveSessionToStorage(sessionId);

    const transcript = document.getElementById("transcript");
    transcript.innerHTML = `
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;height:100%;">
            <div style="width:80px;height:80px;
                        background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
                        border-radius:50%;display:flex;align-items:center;
                        justify-content:center;margin-bottom:20px;">
                <span style="font-size:40px;">🔄</span>
            </div>
            <div style="font-size:22px;font-weight:bold;color:#667eea;margin-bottom:10px;">
                Resuming Interview
            </div>
            <div style="color:#666;font-size:14px;">Reconnecting…</div>
        </div>`;

    startBtn.disabled = true;

    const micOk = await initMicrophone();
    if (!micOk) {
        alert("Microphone access denied. Please allow microphone and try again.");
        stopInterview(true);
        return;
    }

    connectWebSocket();
}


// DISCARD INTERRUPTED SESSION (Abandon — no results)

function discardInterruptedSession() {
    log("Discarding interrupted session", "warning");
    isDiscarding   = true;
    interviewEnded = true;
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
    sessionId = null;
    clearSessionFromStorage();
    isDiscarding = false;
}

// STOP INTERVIEW
function stopInterview(resetUI = true) {
    isRunning = false;
    stopTimer();
    clearTimeout(silenceTimeout);
    if (pingInterval)   { clearInterval(pingInterval);  pingInterval   = null; }
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
    teardownAudio();
    try { ws?.close(); ws = null; } catch {}

    if (resetUI) {
        startBtn.disabled  = false;
        stopBtn.disabled   = true;
        submitBtn.disabled = true;
        skipBtn.disabled   = true;
    }
}

// RESET STATE
function resetInterviewState() {
    interviewEnded        = false;
    isDiscarding          = false;
    isProcessing          = false;
    audioChunksReady      = false;
    isAISpeaking          = false;
    isUserSpeaking        = false;
    currentQuestionNumber = 0;
    currentQuestion       = null;
    remainingSeconds      = 0;
    inBufferTime          = false;
    warned10Min           = false;
    warned5Min            = false;
    bufferWarningShown    = false;
    reconnectAttempts     = 0;
    stopTimer();
    clearTimeout(silenceTimeout);
}

// SUBMIT ANSWER

function submitAnswer() {
    if (isProcessing) { return; }
    if (!ws || ws.readyState !== WebSocket.OPEN || !isRunning) { return; }
    if (!audioChunksReady) {
        showToast("⚠️ Please wait — the question is still loading.", "warning");
        return;
    }

    log("→ Submitting answer", "info");
    isProcessing     = true;
    muteMic();
    audioChunksReady = false;
    clearTimeout(silenceTimeout);
    submitBtn.disabled = true;
    skipBtn.disabled   = true;
    ws.send(JSON.stringify({ action: "SUBMIT_ANSWER" }));
}

// SKIP QUESTION
function skipQuestion() {
    if (isProcessing) { return; }
    if (!ws || ws.readyState !== WebSocket.OPEN || !isRunning) { return; }
    if (!audioChunksReady) {
        showToast("⚠️ Please wait — the question is still loading.", "warning");
        return;
    }

    log("→ Skipping question", "warning");
    isProcessing     = true;
    muteMic();
    audioChunksReady = false;
    clearTimeout(silenceTimeout);
    submitBtn.disabled = true;
    skipBtn.disabled   = true;
    ws.send(JSON.stringify({ action: "SKIP_QUESTION" }));
}

// RESULT DISPLAY

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

function displayResults(summary) {
    const transcript = document.getElementById("transcript");
    let text = "";

    text += "\n╔═══════════════════════════════════════════════════════════════════╗\n";
    text += "║                     📊 INTERVIEW RESULTS                          ║\n";
    text += "╚═══════════════════════════════════════════════════════════════════╝\n\n";
    text += "┌─────────────────────────────────────────────────────────────────┐\n";
    text += "│                    INTERVIEW TRANSCRIPT                         │\n";
    text += "└─────────────────────────────────────────────────────────────────┘\n\n";

    summary.questions.forEach((question, index) => {
        const answer   = summary.answers[index]                   || "No answer";
        const score    = summary.scores[index] || {final_score: 0};
        const duration = summary.time_per_answer_seconds?.[index] || 0;

        text += `${getScoreEmoji(score.final_score)} Question ${index + 1}:\n`;
        text += `   Q: ${question}\n`;
        text += `   A: ${answer}\n`;

        const fs = score.final_score ?? 0;
        text += `   Score: ${fs.toFixed(2)} (${getScoreGrade(fs)}) | Time: ${Math.floor(duration)}s\n\n`;
    });

    text += "\n┌─────────────────────────────────────────────────────────────────┐\n";
    text += "│                      OVERALL SUMMARY                            │\n";
    text += "└─────────────────────────────────────────────────────────────────┘\n\n";
    text += `${summary.result === "PASS" ? "✅" : "❌"} Final Result:       ${summary.result}\n`;
    text += `📈 Average Score:      ${summary.average_score.toFixed(2)} / 1.00\n`;
    text += `📝 Questions Answered: ${summary.questions_answered} / ${summary.questions_asked}\n`;
    text += `⏱️  Total Duration:     ${Math.floor(summary.total_duration_seconds / 60)}m ${Math.floor(summary.total_duration_seconds % 60)}s\n`;
    text += `🏁 Completion:         ${summary.completion_reason.replace(/_/g, " ")}\n`;

    if (summary.covered_projects?.length > 0) {
        text += `💼 Projects Covered:   ${summary.covered_projects.join(", ")}\n`;
    }

    text += "\n\n┌─────────────────────────────────────────────────────────────────┐\n";
    text += "│                         FEEDBACK                                │\n";
    text += "└─────────────────────────────────────────────────────────────────┘\n\n";
    text += summary.feedback?.trim() ? summary.feedback + "\n" : "⏳ Feedback unavailable.\n";
    text += "\n\n╔═══════════════════════════════════════════════════════════════════╗\n";
    text += "║          Thank you for completing the interview! 🎉              ║\n";
    text += "╚═══════════════════════════════════════════════════════════════════╝\n";

    transcript.textContent = text;
    transcript.scrollTop   = 0;
}

// EVENT LISTENERS
resumeInput.addEventListener("change", () => {
    startBtn.disabled = !resumeInput.files[0];
});

startBtn.addEventListener("click", async (e) => {
    e.preventDefault();
    startBtn.disabled = true;
    await startInterview();
});

stopBtn.addEventListener("click", (e) => {
    e.preventDefault();
    interviewEnded = true;
    clearSessionFromStorage();
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

//PAGE LOAD

(function onPageLoad() {
    const interruptedId = loadSessionFromStorage();
    if (interruptedId) {
        log(`Found interrupted session: ${interruptedId}`, "warning");
        setTimeout(() => showResumeBanner(interruptedId), 300);
    }
})();

log("audio.js v5 loaded ✓", "success");