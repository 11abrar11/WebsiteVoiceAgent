import sys
import traceback

print("Testing Kokoro...", flush=True)
try:
    from kokoro import KPipeline
    pipeline = KPipeline(lang_code='a')
    print("Kokoro loaded!", flush=True)
except Exception as e:
    print("Exception during Kokoro load:", flush=True)
    traceback.print_exc()

print("Testing STT...", flush=True)
try:
    from faster_whisper import WhisperModel
    model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    print("STT loaded!", flush=True)
except Exception as e:
    print("Exception during STT load:", flush=True)
    traceback.print_exc()
