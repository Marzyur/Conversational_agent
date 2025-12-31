import os
from groq import Groq
from gtts import gTTS
import io
import base64
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def transcribe_audio(audio_bytes):
    """Uses Groq's Whisper-large-v3 for ultra-fast Speech-to-Text."""
    if not audio_bytes: return ""
    
    # Create a temporary file-like object for Groq
    audio_file = ("speech.webm", audio_bytes)
    
    try:
        translation = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3",
            response_format="text"
        )
        return translation
    except Exception as e:
        print(f"STT Error: {e}")
        return ""

def speak_text(text):
    """Converts AI text to audio for autoplay."""
    if not text: return ""
    tts = gTTS(text=text, lang='en', tld='com')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    b64 = base64.b64encode(fp.read()).decode()
    return f'<audio autoplay src="data:audio/mp3;base64,{b64}">'