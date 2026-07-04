import os
import io
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class STTService:
    def __init__(self):
        print("Initializing Groq Whisper STT...")
        self.client = AsyncGroq(api_key=GROQ_API_KEY)
        self.model = "whisper-large-v3-turbo"
        
    async def transcribe(self, audio_data: bytes) -> str:
        """
        Transcribes binary audio data into text using Groq's insanely fast Whisper API.
        """
        try:
            transcription = await self.client.audio.transcriptions.create(
              file=("audio.webm", audio_data),
              model=self.model,
              response_format="json",
              language="en",
            )
            return transcription.text.strip()
        except Exception as e:
            print(f"STT Error: {e}")
            return ""

stt_service = STTService()