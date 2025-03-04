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
FREQUENCIES = [440, 480, 520, 580]

# Initialize session state
if 'audio_initialized' not in st.session_state:
    st.session_state.audio_initialized = False
    st.session_state.running = False

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
    start_btn = st.button("Start Streaming", disabled=st.session_state.running)
with col2:
    stop_btn = st.button("Stop Streaming", disabled=not st.session_state.running)

html_code = f"""
<script>
let audioContext = null;
let nextScheduledTime = 0;
const bufferQueue = [];
const MAX_BUFFER_AHEAD = 1.5;  // Buffer up to 1.5 seconds of audio

async function initAudioContext() {{
    try {{
        if (!audioContext) {{
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('AudioContext created');
        }}
        if (audioContext.state === 'suspended') {{
            await audioContext.resume();
            console.log('AudioContext resumed');
        }}
        return true;
    }} catch (error) {{
        console.error('AudioContext initialization failed:', error);
        return false;
    }}
}}

async function processChunk(base64Data) {{
    try {{
        // Convert base64 to ArrayBuffer
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {{
            bytes[i] = binaryString.charCodeAt(i);
        }}
        
        // Decode and schedule audio
        const audioBuffer = await audioContext.decodeAudioData(bytes.buffer);
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        
        // Calculate optimal start time
        const now = audioContext.currentTime;
        const startTime = Math.max(nextScheduledTime, now);
        source.start(startTime);
        nextScheduledTime = startTime + audioBuffer.duration;
        
        console.log('Scheduled chunk at:', startTime, 'duration:', audioBuffer.duration);
        
    }} catch (error) {{
        console.error('Error processing chunk:', error);
    }}
}}

// Message handler
window.addEventListener('message', async (event) => {{
    if (event.data.type === 'AUDIO_CHUNK') {{
        if (!audioContext || audioContext.state !== 'running') {{
            console.log('AudioContext not ready, initializing...');
            const success = await initAudioContext();
            if (!success) return;
        }}
        
        await processChunk(event.data.chunk);
    }}
}});

// Initialize on any click
document.addEventListener('click', async () => {{
    const success = await initAudioContext();
    if (success) {{
        window.parent.postMessage({{ type: 'AUDIO_READY' }}, '*');
    }}
}});
</script>
"""

components.html(html_code, height=0)

# Audio generation and streaming logic
if start_btn:
    st.session_state.running = True

if stop_btn:
    st.session_state.running = False

if st.session_state.running:
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
    
    # Maintain streaming loop
    time.sleep(CHUNK_DURATION * 0.9)  # Slightly faster than real-time
    st.rerun()

# Initialization check
if not st.session_state.audio_initialized:
    components.html(
        """
        <script>
            window.parent.postMessage({ type: 'AUDIO_INIT' }, '*');
        </script>
        """,
        height=0
    )
    st.session_state.audio_initialized = True