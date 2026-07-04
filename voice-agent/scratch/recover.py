import json
import re
import glob

def recover():
    log_file = r"C:\Users\11abr\.gemini\antigravity-ide\brain\452edcce-7168-4922-bbf1-07e906b26df6\.system_generated\logs\transcript_full.jsonl"
    
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for line in lines:
        try:
            data = json.loads(line)
        except:
            continue
            
        if data.get("type") == "VIEW_FILE":
            content = data.get("content", "")
            if "Total Bytes:" in content:
                print("Found a view_file response!")
                if "The following code has been modified" in content:
                    print("Found modified code marker!")
                match = re.search(r"File Path: `file:///([cC]):/Projects/Website(?:%20| )Voice(?:%20| )Agent/voice-agent/([^`]+)`", content, re.IGNORECASE)
                if not match:
                    print(f"Regex failed on:\n{content[:150]}")
                    continue
                
                filepath = match.group(2).replace("%20", " ")
                print(f"Found {filepath}")
                
                # Extract content
                start_marker = "Please note that any changes targeting the original code should remove the line number, colon, and leading space.\n"
                end_marker = "The above content shows the entire, complete file contents"
                
                start_idx = content.find(start_marker)
                if start_idx == -1:
                    continue
                start_idx += len(start_marker)
                
                end_idx = content.find(end_marker, start_idx)
                if end_idx == -1:
                    end_idx = len(content)
                    
                code_lines = content[start_idx:end_idx].strip().split('\n')
                
                clean_code = []
                for cl in code_lines:
                    # Remove line numbers: "1: import asyncio"
                    clean_line = re.sub(r'^\d+:\s?', '', cl)
                    clean_code.append(clean_line)
                    
                if len(clean_code) <= 1:
                    print(f"Skipping {filepath} because content is empty")
                    continue
                    
                with open(filepath, "w", encoding="utf-8") as out:
                    out.write('\n'.join(clean_code))
                    
                print(f"Recovered {filepath}")

if __name__ == "__main__":
    recover()
