import streamlit as st
import numpy as np
import av
from pydub import AudioSegment
from streamlit_webrtc import WebRtcMode, webrtc_streamer

# Streamlit UI
st.title("🎵 Real-Time Frequency Streaming (No SoundDevice)")

# Frequency slider (updates dynamically)
frequency = st.slider("Frequency (Hz)", 100, 1000, 440, step=10)

# Generate a sine wave for a given frequency
def generate_sine_wave(freq, duration=0.5, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    waveform = 0.5 * np.sin(2 * np.pi * freq * t)  # 50% volume sine wave
    audio = (waveform * 32767).astype(np.int16)  # Convert to int16
    return audio.tobytes()

# WebRTC audio streamer
def audio_callback(frame: av.AudioFrame) -> av.AudioFrame:
    audio_data = generate_sine_wave(frequency)
    audio_segment = AudioSegment(
        data=audio_data,
        sample_width=2,
        frame_rate=44100,
        channels=1
    )
    return av.AudioFrame.from_ndarray(np.array(audio_segment.get_array_of_samples()), format="s16")

webrtc_streamer(
    key="audio-stream",
    mode=WebRtcMode.SENDONLY,
    audio_frame_callback=audio_callback,
    media_stream_constraints={"audio": True, "video": False},
)

import pathlib
import subprocess

import ffmpeg
import streamlit as st

# global variables
uploaded_mp3_file = None
uploaded_mp3_file_length = 0
filename = None
downloadfile = None

def convert_mp3_to_wav_ffmpeg_bytes2bytes(input_data: bytes) -> bytes:
    """
    It converts mp3 to wav using ffmpeg
    :param input_data: bytes object of a mp3 file
    :return: A bytes object of a wav file.
    """
    # print('convert_mp3_to_wav_ffmpeg_bytes2bytes')
    args = (ffmpeg
            .input('pipe:', format='mp3')
            .output('pipe:', format='wav')
            .global_args('-loglevel', 'error')
            .get_args()
            )
    # print(args)
    proc = subprocess.Popen(
        ['ffmpeg'] + args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    return proc.communicate(input=input_data)[0]

def on_file_change(uploaded_mp3_file):
    return convert_mp3_to_wav_ffmpeg_bytes2bytes(uploaded_mp3_file.getvalue())

def on_change_callback():
    """
    It prints a message to the console. Just for testing of callbacks.
    """
    print(f'on_change_callback: {uploaded_mp3_file}')


# The below code is a simple streamlit web app that allows you to upload an mp3 file
# and then download the converted wav file.
if __name__ == '__main__':
    st.title('MP3 to WAV Converter test app')
    st.markdown("""This is a quick example app for using **ffmpeg** on Streamlit Cloud.
    It uses the `ffmpeg` binary and the python wrapper `ffmpeg-python` library.""")

    uploaded_mp3_file = st.file_uploader('Upload Your MP3 File', type=['mp3'], on_change=on_change_callback)

    if uploaded_mp3_file:
        uploaded_mp3_file_length = len(uploaded_mp3_file.getvalue())
        filename = pathlib.Path(uploaded_mp3_file.name).stem
        if uploaded_mp3_file_length > 0:
            st.text(f'Size of uploaded "{uploaded_mp3_file.name}" file: {uploaded_mp3_file_length} bytes')
            downloadfile = on_file_change(uploaded_mp3_file)

    st.markdown("""---""")
    if downloadfile:
        length = len(downloadfile)
        if length > 0:
            st.subheader('After conversion to WAV you can download it below')
            button = st.download_button(label="Download .wav file",
                            data=downloadfile,
                            file_name=f'{filename}.wav',
                            mime='audio/wav')
            st.text(f'Size of "{filename}.wav" file to download: {length} bytes')
    st.markdown("""---""")
