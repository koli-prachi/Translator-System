import os
import streamlit as st
from datetime import datetime
import yt_dlp

# Import your backend functions
from translate_media import (
    transcribe_audio,
    translate_text,
    text_to_speech_gtts,
    extract_audio_from_video,
    merge_audio_with_video_simple,
)

output_dir = "translated_output"
os.makedirs(output_dir, exist_ok=True)

st.set_page_config(page_title="English to Hindi Audio/Video Translator", layout="centered")
st.title("🎙 English to Hindi Audio/Video Translator")
st.write("Upload an English audio/video file or paste a YouTube link to get a Hindi dubbed version!")

# --- YouTube Link Section ---
st.subheader("Paste a YouTube link")
youtube_url = st.text_input("YouTube Video URL")

if st.button("Download from YouTube") and youtube_url:
    with st.spinner("Downloading from YouTube..."):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            downloaded_file = ydl.prepare_filename(info)
            # Sometimes the extension is .webm or .m4a, handle accordingly
            if not os.path.exists(downloaded_file):
                base = os.path.splitext(downloaded_file)[0]
                for ext in ['.webm', '.m4a', '.mp3', '.mp4']:
                    if os.path.exists(base + ext):
                        downloaded_file = base + ext
                        break
            st.success(f"Downloaded: {downloaded_file}")
            st.session_state['yt_downloaded_file'] = downloaded_file

# Only show Translate if a file is present in session state
if 'yt_downloaded_file' in st.session_state:
    downloaded_file = st.session_state['yt_downloaded_file']
    file_ext = os.path.splitext(downloaded_file)[1].lower()
    is_video = file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
    is_audio = file_ext in ['.mp3', '.wav', '.m4a', '.aac', '.flac', '.webm']
    base_name = os.path.splitext(os.path.basename(downloaded_file))[0]

    # Show preview
    if is_video and os.path.exists(downloaded_file):
        st.video(downloaded_file)
    elif is_audio and os.path.exists(downloaded_file):
        st.audio(downloaded_file)

    if st.button("Translate! (YouTube)"):
        def process_file(input_path, base_name, is_video, is_audio, source_label):
            # Show original media
            if is_video and os.path.exists(input_path):
                st.video(input_path)
            elif is_audio and os.path.exists(input_path):
                st.audio(input_path)

            output_video_path = os.path.join(output_dir, f"{base_name}_hindi.mp4") if is_video else None
            output_audio_path = os.path.join(output_dir, f"{base_name}_hindi.wav")

            with st.spinner("Processing..."):
                # Step 1: Extract audio if video
                if is_video:
                    temp_audio_path = os.path.join(output_dir, f"{base_name}_temp_audio.wav")
                    extract_audio_from_video(input_path, temp_audio_path)
                    audio_to_process = temp_audio_path
                else:
                    audio_to_process = input_path

                # Step 2: Transcribe
                english_text = transcribe_audio(audio_to_process)
                st.write("*Transcription:*", english_text)

                # Step 3: Translate
                hindi_text = translate_text(english_text)
                st.write("*Translation:*", hindi_text)

                # Step 4: TTS
                text_to_speech_gtts(hindi_text, output_audio_path)

                # Show and offer download for Hindi audio
                if os.path.exists(output_audio_path):
                    st.audio(output_audio_path, format="audio/wav")
                    with open(output_audio_path, "rb") as f:
                        st.download_button("Download Hindi Audio", f, file_name=f"{base_name}_hindi.wav")
                else:
                    st.warning("Hindi audio file not found!")

                # Step 5: Merge with video if needed
                if is_video:
                    merge_audio_with_video_simple(input_path, output_audio_path, output_video_path)
                    if os.path.exists(output_video_path):
                        st.video(output_video_path)
                        with open(output_video_path, "rb") as f:
                            st.download_button("Download Dubbed Video", f, file_name=f"{base_name}_hindi.mp4")
                    else:
                        st.warning("Dubbed video file not found!")

                # Save history
                with open(os.path.join(output_dir, "history.txt"), "a", encoding="utf-8") as hist:
                    hist.write(f"{datetime.now()} | {source_label} | {base_name}\n")

        process_file(downloaded_file, base_name, is_video, is_audio, "YouTube")
        # Optionally clear session state after processing
        del st.session_state['yt_downloaded_file']

# --- File Upload Section ---
st.subheader("Or upload an audio/video file")
uploaded_file = st.file_uploader("Upload Audio/Video", type=["mp3", "wav", "mp4", "avi", "mov", "mkv", "wmv", "flv", "m4a", "aac", "flac"])

def process_file(input_path, base_name, is_video, is_audio, source_label):
    # Show original media
    if is_video and os.path.exists(input_path):
        st.video(input_path)
    elif is_audio and os.path.exists(input_path):
        st.audio(input_path)

    output_video_path = os.path.join(output_dir, f"{base_name}_hindi.mp4") if is_video else None
    output_audio_path = os.path.join(output_dir, f"{base_name}_hindi.wav")

    if st.button(f"Translate! ({source_label})", key=f"translate_{base_name}_{source_label}"):
        with st.spinner("Processing..."):
            # Step 1: Extract audio if video
            if is_video:
                temp_audio_path = os.path.join(output_dir, f"{base_name}_temp_audio.wav")
                extract_audio_from_video(input_path, temp_audio_path)
                audio_to_process = temp_audio_path
            else:
                audio_to_process = input_path

            # Step 2: Transcribe
            english_text = transcribe_audio(audio_to_process)
            st.write("*Transcription:*", english_text)

            # Step 3: Translate
            hindi_text = translate_text(english_text)
            st.write("*Translation:*", hindi_text)

            # Step 4: TTS
            text_to_speech_gtts(hindi_text, output_audio_path)

            # Show and offer download for Hindi audio
            if os.path.exists(output_audio_path):
                st.audio(output_audio_path, format="audio/wav")
                with open(output_audio_path, "rb") as f:
                    st.download_button("Download Hindi Audio", f, file_name=f"{base_name}_hindi.wav")
            else:
                st.warning("Hindi audio file not found!")

            # Step 5: Merge with video if needed
            if is_video:
                merge_audio_with_video_simple(input_path, output_audio_path, output_video_path)
                if os.path.exists(output_video_path):
                    st.video(output_video_path)
                    with open(output_video_path, "rb") as f:
                        st.download_button("Download Dubbed Video", f, file_name=f"{base_name}_hindi.mp4")
                else:
                    st.warning("Dubbed video file not found!")

            # Save history
            with open(os.path.join(output_dir, "history.txt"), "a", encoding="utf-8") as hist:
                hist.write(f"{datetime.now()} | {source_label} | {base_name}\n")

if uploaded_file:
    input_path = os.path.join(output_dir, uploaded_file.name)
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"Uploaded: {uploaded_file.name}")

    file_ext = os.path.splitext(input_path)[1].lower()
    is_video = file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
    is_audio = file_ext in ['.mp3', '.wav', '.m4a', '.aac', '.flac']
    base_name = os.path.splitext(os.path.basename(input_path))[0]

    process_file(input_path, base_name, is_video, is_audio, "Upload")

# --- History Section ---
st.subheader("History")
history_file = os.path.join(output_dir, "history.txt")
if os.path.exists(history_file):
    with open(history_file, "r", encoding="utf-8") as hist:
        for line in hist.readlines()[-10:][::-1]:  # Show last 10
            st.write(line.strip())
else:
    st.write("No history yet.")
