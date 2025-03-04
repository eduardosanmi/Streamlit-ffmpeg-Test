import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import base64
import io
import time
from scipy.io.wavfile import write

st.title("Real-Time Audio Streaming")

sample_rate = 44100
chunk_duration = 0.3  # Reduced chunk duration for smoother playback
frequencies = [440, 480, 520, 580]

# Initialize session state
if 'running' not in st.session_state:
    st.session_state.running = False
    st.session_state.last_chunk_time = 0
    st.session_state.chunk_queue = []

def generate_audio_chunk(frequency, duration):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio = np.sin(2 * np.pi * frequency * t)
    audio = (audio * 32767).astype(np.int16)
    buffer = io.BytesIO()
    write(buffer, sample_rate, audio)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

# Control buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("Start Streaming") and not st.session_state.running:
        st.session_state.running = True
        st.session_state.last_chunk_time = time.time()
with col2:
    if st.button("Stop Streaming") and st.session_state.running:
        st.session_state.running = False

html_code = """
<script>
let audioContext = null;
let nextTime = 0;
let bufferQueue = [];

function initAudioContext() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
}

function playNextChunk() {
    if (!audioContext || bufferQueue.length === 0) return;
    
    const chunk = bufferQueue.shift();
    audioContext.decodeAudioData(chunk.buffer, (buffer) => {
        const source = audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContext.destination);
        const startTime = Math.max(nextTime, audioContext.currentTime);
        source.start(startTime);
        nextTime = startTime + buffer.duration;
    });
}

// Check for new chunks every 50ms
setInterval(() => {
    if (bufferQueue.length > 0) playNextChunk();
}, 50);

window.addEventListener('message', (event) => {
    if (event.data.type === 'AUDIO_CHUNK') {
        const binaryString = window.atob(event.data.data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        bufferQueue.push(bytes);
    }
    
    if (event.data.type === 'INIT_AUDIO') {
        initAudioContext();
    }
});
</script>
"""

# Initialize audio context
components.html(
    "<script>window.parent.postMessage({ type: 'INIT_AUDIO' }, '*');</script>",
    height=0
)

# Audio generation logic
if st.session_state.running:
    elapsed = time.time() - st.session_state.last_chunk_time
    if elapsed >= chunk_duration:
        freq = np.random.choice(frequencies)
        chunk = generate_audio_chunk(freq, chunk_duration)
        components.html(
            f"<script>window.parent.postMessage({{ type: 'AUDIO_CHUNK', data: '{chunk}' }}, '*');</script>",
            height=0
        )
        st.session_state.last_chunk_time = time.time()
    
    # Create a placeholder to keep the script running
    placeholder = st.empty()
    placeholder.write("Streaming...")
    time.sleep(0.1)  # Reduced sleep time
    st.rerun()  # Use st.rerun() if available

components.html(html_code, height=0)