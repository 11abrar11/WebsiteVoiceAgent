import asyncio
import os
import time
import base64
from app.services.tts import tts_service
from app.services.stt import stt_service

async def test_tts():
    print("Testing ElevenLabs TTS...")
    start_time = time.time()
    audio = tts_service.synthesize("Hello, I am calling to confirm your meeting.")
    latency = time.time() - start_time
    print(f"TTS Latency: {latency:.2f}s")
    if audio:
        print(f"TTS Output: {len(audio)} bytes")
    else:
        print("TTS Output: None or Empty")

async def test_stt():
    print("Testing Groq STT...")
    # Generate some dummy audio or use an existing file to test
    # If no audio file is easily available, we skip the actual audio test or use empty
    try:
        with open("scratch/test_audio.webm", "wb") as f:
            pass # Just an empty file for now, Groq might fail on it
    except:
        pass
    
    start_time = time.time()
    # We will pass a tiny fake wav header just to not crash immediately if possible
    fake_wav = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
    text = await stt_service.transcribe(fake_wav)
    latency = time.time() - start_time
    print(f"STT Latency: {latency:.2f}s")
    print(f"STT Transcript: '{text}'")

async def test_meeting():
    print("Testing MeetingEngine booking logic without dateutil...")
    from app.meeting.engine import MeetingEngine
    
    class FakeRepo:
        async def book_meeting(self, meeting_date, meeting_time, lead_id, notes):
            return f"Booked: {meeting_date} {meeting_time} for lead {lead_id}"
            
    engine = MeetingEngine(FakeRepo())
    result = await engine.book("2026-07-10", "15:00", lead_id=42)
    print(f"Meeting Engine Result (15:00): {result}")
    
    result2 = await engine.book("2026-07-10", "09:30:00", lead_id=42)
    print(f"Meeting Engine Result (09:30:00): {result2}")

async def main():
    await test_meeting()
    await test_tts()
    await test_stt()

if __name__ == "__main__":
    asyncio.run(main())