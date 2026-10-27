// Real-time audio streaming client for Pipecat testing UI

let ws = null;
let audioContext = null;
let mediaStream = null;
let audioWorkletNode = null;
let isCallActive = false;
let nextPlayTime = 0;

const callBtn = document.getElementById("callButton");
const callIcon = document.getElementById("callIcon");
const callLabel = document.getElementById("callLabel");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const logBox = document.getElementById("logBox");
const visualizerBars = document.querySelectorAll("#visualizer .bar");

function log(msg) {
  const time = new Date().toLocaleTimeString();
  logBox.innerHTML += `\n[${time}] ${msg}`;
  logBox.scrollTop = logBox.scrollHeight;
}

function updateStatus(text, state = "idle") {
  statusText.textContent = text;
  statusDot.className = "status-dot";
  if (state === "active") statusDot.classList.add("active");
  if (state === "error") statusDot.classList.add("error");
}

callBtn.addEventListener("click", async () => {
  if (isCallActive) {
    endCall();
  } else {
    await startCall();
  }
});

async function startCall() {
  try {
    updateStatus("Requesting microphone...", "idle");
    log("Requesting microphone access...");

    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    audioContext = new (window.AudioContext || window.webkitAudioContext)({
      sampleRate: 16000,
    });
    nextPlayTime = audioContext.currentTime;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/test-client`;

    log(`Connecting to ${wsUrl}...`);
    ws = new WebSocket(wsUrl);
    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
      log("Connected to AI voice agent.");
      updateStatus("Connected & Listening", "active");
      isCallActive = true;
      callBtn.classList.add("in-call");
      callIcon.innerHTML = "&#128683;";
      callLabel.textContent = "Click to End Call";
      startAudioCapture();
    };

    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        playAudioChunk(event.data);
      }
    };

    ws.onerror = (err) => {
      log("WebSocket error occurred.");
      updateStatus("Connection Error", "error");
    };

    ws.onclose = () => {
      log("Disconnected from voice agent.");
      endCall();
    };
  } catch (err) {
    log(`Failed to start call: ${err.message}`);
    updateStatus("Failed to access mic", "error");
  }
}

function startAudioCapture() {
  const source = audioContext.createMediaStreamSource(mediaStream);
  // Buffer size 2048 at 16kHz gives ~128ms chunks
  const processor = audioContext.createScriptProcessor(2048, 1, 1);

  processor.onaudioprocess = (e) => {
    if (!isCallActive || !ws || ws.readyState !== WebSocket.OPEN) return;

    const inputData = e.inputBuffer.getChannelData(0);
    // Convert Float32 to 16-bit PCM (Linear16)
    const pcmData = new Int16Array(inputData.length);
    let sum = 0;
    for (let i = 0; i < inputData.length; i++) {
      let s = Math.max(-1, Math.min(1, inputData[i]));
      pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
      sum += Math.abs(s);
    }

    // Animate visualizer based on mic level
    animateVisualizer(sum / inputData.length);

    ws.send(pcmData.buffer);
  };

  source.connect(processor);
  processor.connect(audioContext.destination);
  audioWorkletNode = { source, processor };
}

async function playAudioChunk(arrayBuffer) {
  if (!audioContext || arrayBuffer.byteLength === 0) return;

  try {
    // Web Audio API decodes WAV format with auto-detected sample rate & channels
    const copy = arrayBuffer.slice(0);
    const audioBuffer = await audioContext.decodeAudioData(copy);
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);

    const currentTime = audioContext.currentTime;
    if (nextPlayTime < currentTime) {
      nextPlayTime = currentTime;
    }
    source.start(nextPlayTime);
    nextPlayTime += audioBuffer.duration;
  } catch (err) {
    // Fallback to raw Int16 PCM if decodeAudioData encounters raw stream
    try {
      const int16 = new Int16Array(arrayBuffer);
      const float32 = new Float32Array(int16.length);
      for (let i = 0; i < int16.length; i++) {
        float32[i] = int16[i] / 32768.0;
      }
      const audioBuffer = audioContext.createBuffer(1, float32.length, 24000);
      audioBuffer.getChannelData(0).set(float32);
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      const currentTime = audioContext.currentTime;
      if (nextPlayTime < currentTime) nextPlayTime = currentTime;
      source.start(nextPlayTime);
      nextPlayTime += audioBuffer.duration;
    } catch (_) {}
  }
}

function animateVisualizer(level) {
  visualizerBars.forEach((bar, idx) => {
    const scale = Math.min(60, Math.max(12, level * 250 * (1 + (idx % 3) * 0.5)));
    bar.style.height = `${scale}px`;
    bar.style.opacity = level > 0.02 ? "0.9" : "0.4";
  });
}

function endCall() {
  isCallActive = false;
  if (ws) {
    ws.close();
    ws = null;
  }
  if (audioWorkletNode) {
    try {
      audioWorkletNode.source.disconnect();
      audioWorkletNode.processor.disconnect();
    } catch (_) {}
    audioWorkletNode = null;
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach((t) => t.stop());
    mediaStream = null;
  }
  if (audioContext && audioContext.state !== "closed") {
    audioContext.close();
    audioContext = null;
  }

  callBtn.classList.remove("in-call");
  callIcon.innerHTML = "&#128222;";
  callLabel.textContent = "Click to Start Call";
  updateStatus("Call Ended", "idle");
  log("Call ended.");
  animateVisualizer(0);
}
