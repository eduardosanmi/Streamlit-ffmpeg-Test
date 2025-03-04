import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import base64
import io
import time
from scipy.io.wavfile import write

st.title("Real-Time Audio Streaming")

# Audio configuration
SAMPLE_RATE = 44100
CHUNK_DURATION = 0.5  # Seconds per audio chunk
FREQUENCIES = [440, 480, 520, 580, 540, 510]  # More frequencies for variation

# Initialize session state
if 'running' not in st.session_state:
    st.session_state.running = False
    st.session_state.last_chunk = None

def generate_wav_chunk(frequency):
    """Generate WAV-formatted audio chunk as base64 string"""
    t = np.linspace(0, CHUNK_DURATION, int(SAMPLE_RATE * CHUNK_DURATION), False)
    audio = np.sin(2 * np.pi * frequency * t)
    audio = (audio * 32767).astype(np.int16)  # 16-bit PCM
    
    # Create WAV file in memory
    buffer = io.BytesIO()
    write(buffer, SAMPLE_RATE, audio)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

# Control buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("Start Streaming") and not st.session_state.running:
        st.session_state.running = True
with col2:
    if st.button("Stop Streaming") and st.session_state.running:
        st.session_state.running = False

html_code = f"""
<script>
let audioContext = null;
let nextScheduledTime = 0;
const bufferQueue = [];
const MAX_BUFFER_AHEAD = 2;  // Buffer up to 2 seconds of audio

async function initAudioContext() {{
    if (!audioContext) {{
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        // Resume context if suspended (required by autoplay policies)
        await audioContext.resume();
    }}
    return audioContext;
}}

async function decodeAndSchedule(chunkBase64) {{
    try {{
        const audioContext = await initAudioContext();
        const binaryString = window.atob(chunkBase64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {{
            bytes[i] = binaryString.charCodeAt(i);
        }}
        
        const audioBuffer = await audioContext.decodeAudioData(bytes.buffer);
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        
        const startTime = Math.max(nextScheduledTime, audioContext.currentTime);
        source.start(startTime);
        nextScheduledTime = startTime + audioBuffer.duration;
        
        // Keep only needed buffers
        while ((nextScheduledTime - audioContext.currentTime) > MAX_BUFFER_AHEAD) {{
            await new Promise(resolve => setTimeout(resolve, 100));
        }}
    }} catch (error) {{
        console.error('Audio processing error:', error);
    }}
}}

// Listen for audio chunks from Python
window.addEventListener('message', (event) => {{
    if (event.data.type === 'AUDIO_CHUNK') {{
        decodeAndSchedule(event.data.chunk);
    }}
}});

// Initialize audio context on user interaction
document.addEventListener('click', async () => {{
    await initAudioContext();
}}, {{ once: true }});
</script>
"""

components.html(html_code, height=0)

# Audio generation loop
while st.session_state.running:
    start_time = time.time()
    
    # Generate and send audio chunk
    freq = np.random.choice(FREQUENCIES)
    chunk = generate_wav_chunk(freq)
    
    # Send chunk to JavaScript
    components.html(
        f"""
        <script>
            window.parent.postMessage({{
                type: 'AUDIO_CHUNK',
                chunk: '{chunk}'
            }}, '*');
        </script>
        """,
        height=0
    )
    
    # Calculate sleep time to maintain real-time generation
    elapsed = time.time() - start_time
    sleep_time = max(CHUNK_DURATION - elapsed, 0)
    time.sleep(sleep_time)