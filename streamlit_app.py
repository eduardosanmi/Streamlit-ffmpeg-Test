import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import base64
import io
from scipy.io.wavfile import write

st.title("Real-Time Audio Streaming")

sample_rate = 44100
chunk_duration = 1  # Seconds per audio chunk
frequencies = [440, 480, 520, 580]

# Initialize session state
if 'running' not in st.session_state:
    st.session_state.running = False

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
with col2:
    if st.button("Stop Streaming") and st.session_state.running:
        st.session_state.running = False

html_code = """
<script>
const audioContext = new (window.AudioContext || window.webkitAudioContext)();
let nextTime = 0;
let bufferQueue = [];

function playNextChunk() {
    if (bufferQueue.length === 0) return;
    
    const chunk = bufferQueue.shift();
    audioContext.decodeAudioData(chunk.buffer, (buffer) => {
        const source = audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContext.destination);
        source.start(nextTime);
        nextTime = Math.max(nextTime, audioContext.currentTime) + buffer.duration;
    });
}

// Check for new chunks every 100ms
setInterval(() => {
    if (bufferQueue.length > 0) playNextChunk();
}, 100);

window.addEventListener('message', (event) => {
    if (event.data.type === 'AUDIO_CHUNK') {
        const binaryString = window.atob(event.data.data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        bufferQueue.push(bytes);
    }
});
</script>
"""

# Generate and stream audio chunks
if st.session_state.running:
    freq = np.random.choice(frequencies)
    chunk = generate_audio_chunk(freq, chunk_duration)
    components.html(
        f"<script>window.parent.postMessage({{ type: 'AUDIO_CHUNK', data: '{chunk}' }}, '*');</script>",
        height=0
    )
    st.rerun()  # Changed from st.experimental_rerun()

components.html(html_code, height=0)