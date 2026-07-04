import io
import numpy as np
import soundfile as sf
import threading
import httpx

# ---- KOKORO TTS (Backup) ----
from kokoro import KPipeline

class KokoroTTSService:
    def __init__(self):
        self.pipeline = None
        self._load_lock = threading.Lock()
        
    def load_model(self):
        with self._load_lock:
            if self.pipeline is None:
                print("Loading Kokoro TTS model (this takes ~15 seconds)...")
                self.pipeline = KPipeline(lang_code='a')
                print("Kokoro TTS model loaded successfully!")

    def synthesize(self, text: str) -> bytes:
        # Ensure model is loaded before synthesizing
        if self.pipeline is None:
            self.load_model()
            
        try:
            generator = self.pipeline(text, voice='af_heart', speed=1.3)
            audio_chunks = []
            for i, (gs, ps, audio) in enumerate(generator):
                audio_chunks.append(audio)
            if not audio_chunks:
                return b""
            full_audio = np.concatenate(audio_chunks)
            wav_io = io.BytesIO()
            sf.write(wav_io, full_audio, 24000, format='WAV')
            return wav_io.getvalue()
        except Exception as e:
            print(f"TTS Error: {e}")
            return b""


class ElevenLabsTTSService:
    def __init__(self):
        print("Initializing ElevenLabs TTS...")
        import os
        self.api_key = os.getenv("ELEVENLABS_API_KEY", "")
        # 'Bella' - a default female voice available to free tier API users
        self.voice_id = "EXAVITQu4vr4xnSDxMaL"
        self.url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

    def synthesize(self, text: str) -> bytes:
        try:
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            data = {
                "text": text,
                "model_id": "eleven_turbo_v2_5",  # Super fast conversational model
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            # Using httpx for a quick synchronous request
            with httpx.Client() as client:
                response = client.post(self.url, json=data, headers=headers, timeout=10.0)
                
            if response.status_code == 200:
                return response.content
            else:
                print(f"ElevenLabs API Error: {response.status_code} - {response.text}")
                return b""
                
        except Exception as e:
            print(f"ElevenLabs TTS Exception: {e}")
            return b""

# Active TTS Service — swap to KokoroTTSService() if ElevenLabs quota runs out
tts_service = ElevenLabsTTSService()
