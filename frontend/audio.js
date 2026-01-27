

// let ws = null;
// let audioContext = null;
// let processor = null;
// let source = null;
// let stream = null;
// let isRunning = false;
// let sessionId = null;

// const resumeInput = document.getElementById("resumeFile");
// const startBtn = document.getElementById("startBtn");
// const stopBtn = document.getElementById("stopBtn");
// const uploadStatus = document.getElementById("uploadStatus");

// // Upload resume immediately after selection
// resumeInput.addEventListener("change", async () => {
//   const file = resumeInput.files[0];
//   if (!file) return;

//   uploadStatus.textContent = "Uploading resume...";
//   startBtn.disabled = true;

//   const formData = new FormData();
//   formData.append("file", file);

//   // JD is controlled by company (not candidate)
//   formData.append("job_description", "Python Developer");

//   try {
//     const res = await fetch("http://localhost:8000/upload_resume", {
//       method: "POST",
//       body: formData
//     });

//     const data = await res.json();

//     sessionId = data.session_id;
//     uploadStatus.textContent = "Resume uploaded. Ready to start interview.";
//     startBtn.disabled = false;

//   } catch (err) {
//     uploadStatus.textContent = "Resume upload failed.";
//     console.error(err);
//   }
// });

// // Start Interview
// window.startInterview = async function () {
//   if (isRunning || !sessionId) return;
//   isRunning = true;

//   const transcriptDiv = document.getElementById("transcript");
//   const feedbackDiv = document.getElementById("feedback");

//   ws = new WebSocket(
//     `ws://localhost:8000/ws/interview?session_id=${sessionId}`
//   );

//   ws.onopen = () => console.log("WebSocket connected");

//   ws.onmessage = (event) => {
//     const data = JSON.parse(event.data);

//     if (data.type === "QUESTION") {
//       transcriptDiv.textContent += `\n\nQ: ${data.text}\n`;
//     }

//     if (data.type === "PARTIAL_TRANSCRIPT") {
//       transcriptDiv.textContent += data.text + " ";
//     }

//     if (data.type === "FINAL_TRANSCRIPT") {
//       transcriptDiv.textContent += "\n" + data.text;
//     }

//     if (data.type === "FEEDBACK") {
//       feedbackDiv.textContent = data.text;
//     }

//     transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
//   };

//   ws.onclose = () => {
//     console.log("WebSocket closed");
//     isRunning = false;
//   };

//   // Audio
//   audioContext = new AudioContext({ sampleRate: 16000 });
//   stream = await navigator.mediaDevices.getUserMedia({ audio: true });

//   source = audioContext.createMediaStreamSource(stream);
//   processor = audioContext.createScriptProcessor(4096, 1, 1);

//   processor.onaudioprocess = (e) => {
//     if (!isRunning || ws.readyState !== WebSocket.OPEN) return;
//     ws.send(e.inputBuffer.getChannelData(0).buffer);
//   };

//   source.connect(processor);
//   processor.connect(audioContext.destination);
// };

// // Stop Interview
// window.stopInterview = function () {
//   if (!isRunning) return;

//   isRunning = false;

//   if (ws && ws.readyState === WebSocket.OPEN) {
//     ws.send("END");
//     ws.close();
//   }

//   if (processor) processor.disconnect();
//   if (source) source.disconnect();
//   if (audioContext) audioContext.close();
//   if (stream) stream.getTracks().forEach(t => t.stop());

//   startBtn.disabled = false;
//   stopBtn.disabled = true;
// };

// // Buttons
// startBtn.onclick = async () => {
//   startBtn.disabled = true;
//   stopBtn.disabled = false;
//   document.getElementById("transcript").textContent = "";
//   document.getElementById("feedback").textContent = "Feedback will appear here...";
//   await window.startInterview();
// };

// stopBtn.onclick = () => {
//   stopBtn.disabled = true;
//   startBtn.disabled = false;
//   window.stopInterview();
// };





let ws = null;
let audioContext = null;
let processor = null;
let source = null;
let stream = null;
let isRunning = false;
let sessionId = null;
let silenceTimeout;

// Buttons
const resumeInput = document.getElementById("resumeFile");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const submitBtn = document.getElementById("submitBtn");

// Enable start button after file selection
resumeInput.addEventListener("change", () => {
  startBtn.disabled = false;
});

// Upload resume & create session
async function uploadResume() {
  const file = resumeInput.files[0];
  if (!file) return null;

  const formData = new FormData();
  formData.append("file", file);

  // JD manually set
  const job_description = "Python Developer"; 
  formData.append("job_description", job_description);

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

// Start interview
async function startInterview() {
  if (isRunning) return;
  isRunning = true;

  sessionId = await uploadResume();
  if (!sessionId) { isRunning = false; return; }

  const transcriptDiv = document.getElementById("transcript");
  const feedbackDiv = document.getElementById("feedback");

  // WebSocket
  ws = new WebSocket(`ws://localhost:8000/ws/interview?session_id=${sessionId}`);

  ws.onopen = () => console.log("WebSocket connected");

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "PARTIAL_TRANSCRIPT") {
      transcriptDiv.textContent += data.text + " ";
      transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
      resetSilenceTimer();
    }

    if (data.type === "FINAL_TRANSCRIPT") {
      transcriptDiv.textContent += "\n" + data.text;
      transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
    }

    if (data.type === "FEEDBACK") {
      feedbackDiv.textContent = data.text;
    }

    if (data.type === "QUESTION") {
      transcriptDiv.textContent += "\n\n Question: " + data.text + "\n";
      transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
      resetSilenceTimer();
    }

    if (data.type === "END") {
      transcriptDiv.textContent += "\n\n" + data.text;
      transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
      startBtn.disabled = false;
      stopBtn.disabled = true;
      submitBtn.disabled = true;
      isRunning = false;
    }

    if (data.type === "ERROR") {
      alert(data.text);
      isRunning = false;
    }
  };

  ws.onclose = () => { console.log("WebSocket closed"); isRunning = false; };

  // Audio setup
  audioContext = new AudioContext({ sampleRate: 16000 });
  stream = await navigator.mediaDevices.getUserMedia({ audio: true });

  source = audioContext.createMediaStreamSource(stream);
  processor = audioContext.createScriptProcessor(4096, 1, 1);

  processor.onaudioprocess = (e) => {
    if (!isRunning) return;
    const input = e.inputBuffer.getChannelData(0);
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(input.buffer);
    resetSilenceTimer();
  };

  source.connect(processor);
  processor.connect(audioContext.destination);

  stopBtn.disabled = false;
  submitBtn.disabled = false;
}

// Stop interview
function stopInterview() {
  if (!isRunning) return;
  isRunning = false;

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ text: "STOP_INTERVIEW" }));
    ws.close();
  }

  if (processor) processor.disconnect();
  if (source) source.disconnect();
  if (audioContext) audioContext.close();
  if (stream) stream.getTracks().forEach(track => track.stop());

  startBtn.disabled = false;
  stopBtn.disabled = true;
  submitBtn.disabled = true;
}

// Submit current answer manually
function submitAnswer() {
  if (!isRunning) return;
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ text: "SUBMIT_ANSWER" }));
  resetSilenceTimer();
}

// Silence detection
function resetSilenceTimer() {
  clearTimeout(silenceTimeout);
  silenceTimeout = setTimeout(() => {
    if (isRunning) submitAnswer();
  }, 10000); // 10 seconds
}

// Event listeners
startBtn.addEventListener("click", async () => {
  startBtn.disabled = true;
  stopBtn.disabled = false;
  submitBtn.disabled = false;
  document.getElementById("transcript").textContent = "";
  document.getElementById("feedback").textContent = "Feedback will appear here after the interview.";
  await startInterview();
});

stopBtn.addEventListener("click", stopInterview);
submitBtn.addEventListener("click", submitAnswer);
