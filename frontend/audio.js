// frontend/audio.js
let ws = null;
let audioContext = null;
let processor = null;
let source = null;
let stream = null;
let isRunning = false;

window.startInterview = async function () {
  if (isRunning) return;
  isRunning = true;

  const transcriptDiv = document.getElementById("transcript");
  const feedbackDiv = document.getElementById("feedback");

  // Open WebSocket
  ws = new WebSocket("ws://localhost:8000/ws");

  ws.onopen = () => console.log("WebSocket connected");

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "PARTIAL_TRANSCRIPT") {
        transcriptDiv.textContent += data.text + " ";
        transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
    }

    if (data.type === "FINAL_TRANSCRIPT") {
        transcriptDiv.textContent += "\n" + data.text;
        transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
    }

    if (data.type === "FEEDBACK") {
        const feedbackDiv = document.getElementById("feedback");
        if (feedbackDiv) {
            feedbackDiv.textContent = data.text;
        }
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
  const pcm = new Float32Array(input);

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(pcm.buffer);
  }
};

  source.connect(processor);
  processor.connect(audioContext.destination);
};

window.stopInterview = function () {
  if (!isRunning) return;
  isRunning = false;

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send("END");
    ws.close();
  }

  if (processor) processor.disconnect();
  if (source) source.disconnect();
  if (audioContext) audioContext.close();
  if (stream) stream.getTracks().forEach(track => track.stop());
};
