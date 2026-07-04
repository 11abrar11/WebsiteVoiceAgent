import glob
import os
import json

PROJECT_ROOT = r"C:\Projects\Website Voice Agent"
BRAIN_DIR = r"C:\Users\11abr\.gemini\antigravity-ide\brain"

def replay():
    print("Replaying IDE tool calls from ALL conversation histories...")
    
    # Sort transcripts by modified time to replay in chronological order
    transcript_paths = glob.glob(os.path.join(BRAIN_DIR, "*", ".system_generated", "logs", "transcript_full.jsonl"))
    transcript_paths.sort(key=os.path.getmtime)
    
    for transcript_path in transcript_paths:
        print(f"Reading {transcript_path}...")
        with open(transcript_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except:
                    continue
                    
                if data.get("type") == "PLANNER_RESPONSE":
                    tool_calls = data.get("tool_calls", [])
                    for tc in tool_calls:
                        name = tc.get("name", "").replace("default_api:", "")
                        args = tc.get("args", {})
                        
                        if name == "write_to_file":
                            target = args.get("TargetFile")
                            content = args.get("CodeContent")
                            if target:
                                if target.lower().startswith(PROJECT_ROOT.lower()):
                                    print(f"Restoring file via write_to_file: {target}")
                                    os.makedirs(os.path.dirname(target), exist_ok=True)
                                    with open(target, 'w', encoding='utf-8') as tf:
                                        tf.write(content)
                                        
                        elif name == "replace_file_content":
                            target = args.get("TargetFile")
                            if target and target.lower().startswith(PROJECT_ROOT.lower()) and os.path.exists(target):
                                print(f"Applying replace_file_content to: {target}")
                                target_content = args.get("TargetContent", "")
                                replacement_content = args.get("ReplacementContent", "")
                                
                                with open(target, 'r', encoding='utf-8') as tf:
                                    file_content = tf.read()
                                    
                                if target_content in file_content:
                                    file_content = file_content.replace(target_content, replacement_content)
                                    with open(target, 'w', encoding='utf-8') as tf:
                                        tf.write(file_content)
                                        
                        elif name == "multi_replace_file_content":
                            target = args.get("TargetFile")
                            if target and target.lower().startswith(PROJECT_ROOT.lower()) and os.path.exists(target):
                                print(f"Applying multi_replace_file_content to: {target}")
                                chunks = args.get("ReplacementChunks", [])
                                
                                with open(target, 'r', encoding='utf-8') as tf:
                                    file_content = tf.read()
                                    
                                for chunk in chunks:
                                    t_c = chunk.get("TargetContent", "")
                                    r_c = chunk.get("ReplacementContent", "")
                                    if t_c in file_content:
                                        file_content = file_content.replace(t_c, r_c)
                                
                                with open(target, 'w', encoding='utf-8') as tf:
                                    tf.write(file_content)

if __name__ == "__main__":
    replay()