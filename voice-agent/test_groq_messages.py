import asyncio
import os
import traceback
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

async def test():
    try:
        api_key = os.getenv('GROQ_API_KEY')
        client = AsyncGroq(api_key=api_key)
        
        system_prompt = "You are a helpful assistant."
        chat_history = [
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "test"}
        ]
        
        messages = [{"role": "system", "content": system_prompt}] + chat_history
        
        res = await client.chat.completions.create(
            model='llama-3.1-8b-instant', 
            messages=messages
        )
        print("Response:", res.choices[0].message.content)
    except Exception as e:
        traceback.print_exc()

asyncio.run(test())
