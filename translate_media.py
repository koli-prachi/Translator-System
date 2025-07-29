import os
import re
import whisper
from transformers import MarianMTModel, MarianTokenizer
from gtts import gTTS
import subprocess

def extract_audio_from_video(video_path, audio_path):
    try:
        cmd = [
            'ffmpeg', '-i', video_path, 
            '-vn', '-acodec', 'pcm_s16le', 
            '-ar', '16000', '-ac', '1', 
            audio_path, '-y'
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✓ Audio extracted to: {audio_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error extracting audio: {e}")
        return False

def transcribe_audio(audio_path):
    try:
        print("Loading Whisper model...")
        model = whisper.load_model("base")
        print("Transcribing audio...")
        result = model.transcribe(audio_path, language="en", task="transcribe", verbose=True)
        english_text = result["text"].strip()
        english_text = re.sub(r'\s+', ' ', english_text)
        english_text = english_text.replace(' .', '.').replace(' ,', ',')
        print(f"✓ Transcription: {english_text}")
        return english_text
    except Exception as e:
        print(f"✗ Error transcribing: {e}")
        return None

def translate_text(english_text):
    try:
        print("Loading translation model...")
        model_name = 'Helsinki-NLP/opus-mt-en-hi'
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        print("Translating text...")
        english_text = english_text.strip()
        if not english_text:
            return None
        sentences = re.split(r'[.!?]+', english_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        translated_sentences = []
        for sentence in sentences:
            if len(sentence) < 3:
                continue
            try:
                inputs = tokenizer(sentence, return_tensors="pt", padding=True, truncation=True, max_length=512)
                translated = model.generate(**inputs)
                translated_sentence = tokenizer.decode(translated[0], skip_special_tokens=True)
                translated_sentences.append(translated_sentence)
            except Exception as e:
                print(f"Warning: Could not translate sentence: {sentence}")
                continue
        hindi_text = ' '.join(translated_sentences)
        print(f"✓ Translation: {hindi_text}")
        return hindi_text
    except Exception as e:
        print(f"✗ Error translating: {e}")
        return None

def text_to_speech_gtts(hindi_text, output_audio_path):
    try:
        print("Generating Hindi speech using gTTS (Google Text-to-Speech)...")
        tts = gTTS(text=hindi_text, lang='hi')
        tts.save(output_audio_path)
        print(f"✓ Speech generated: {output_audio_path}")
        return True
    except Exception as e:
        print(f"✗ Error in gTTS: {e}")
        return False

def merge_audio_with_video_simple(video_path, audio_path, output_video_path):
    try:
        cmd = [
            'ffmpeg', '-i', video_path, '-i', audio_path,
            '-c:v', 'copy', '-map', '0:v:0', '-map', '1:a:0',
            '-shortest', output_video_path, '-y'
        ]
        subprocess.run(cmd, check=True)
        print(f"✓ Video created: {output_video_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error creating video: {e}")
        return False

def main():
    print("=== English to Hindi Audio/Video Translator (Improved) ===")
    print("This tool translates English audio/video to Hindi\n")
    input_path = input("Enter the path to your audio/video file: ").strip().strip('"')
    if not os.path.exists(input_path):
        print("✗ File not found!")
        return
    file_ext = os.path.splitext(input_path)[1].lower()
    is_video = file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
    is_audio = file_ext in ['.mp3', '.wav', '.m4a', '.aac', '.flac']
    if not (is_video or is_audio):
        print("✗ Unsupported file format!")
        return
    output_dir = "translated_output"
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    if is_video:
        output_video_path = os.path.join(output_dir, f"{base_name}_hindi.mp4")
        output_audio_path = os.path.join(output_dir, f"{base_name}_hindi.wav")
    else:
        output_audio_path = os.path.join(output_dir, f"{base_name}_hindi.wav")
    if is_video:
        print(f"\nStep 1: Extracting audio from video...")
        temp_audio_path = os.path.join(output_dir, "temp_audio.wav")
        if not extract_audio_from_video(input_path, temp_audio_path):
            return
        audio_to_process = temp_audio_path
    else:
        audio_to_process = input_path
    print(f"\nStep 2: Transcribing audio...")
    english_text = transcribe_audio(audio_to_process)
    if not english_text:
        return
    print(f"\nStep 3: Translating to Hindi...")
    hindi_text = translate_text(english_text)
    if not hindi_text:
        return
    print(f"\nStep 4: Generating Hindi speech...")
    if not text_to_speech_gtts(hindi_text, output_audio_path):
        return
    if is_video:
        print(f"\nStep 5: Creating dubbed video...")
        if not merge_audio_with_video_simple(input_path, output_audio_path, output_video_path):
            return
    if is_video and os.path.exists(temp_audio_path):
        os.remove(temp_audio_path)
    print(f"\n=== Translation Complete! ===")
    if is_video:
        print(f"✓ Dubbed video: {output_video_path}")
    print(f"✓ Hindi audio: {output_audio_path}")
    print(f"✓ Original text: {english_text}")
    print(f"✓ Translated text: {hindi_text}")
    print(f"\nNote: If the audio quality is poor, try using shorter audio clips (10-30 seconds) for better results.")

if __name__ == "__main__":
    main()