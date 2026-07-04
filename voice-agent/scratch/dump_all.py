import json
import re

def dump_all():
    log_file = r"C:\Users\11abr\.gemini\antigravity-ide\brain\452edcce-7168-4922-bbf1-07e906b26df6\.system_generated\logs\transcript_full.jsonl"
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    recovered = set()
    for line in lines:
        try:
            data = json.loads(line)
        except:
            continue
            
        if data.get("type") == "VIEW_FILE":
            content = data.get("content", "")
            match = re.search(r"File Path: `file:///([cC]):/Projects/Website(?:%20| )Voice(?:%20| )Agent/voice-agent/([^`]+)`", content, re.IGNORECASE)
            if match:
                filepath = match.group(2).replace("%20", " ")
                recovered.add(filepath)

    print("Found files in transcript:")
    for f in recovered:
        print(f)

if __name__ == "__main__":
    dump_all()
