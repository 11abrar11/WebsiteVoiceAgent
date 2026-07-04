import asyncio
import os
import traceback
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

async def test():
    try:
        api_key = os.getenv('GROQ_API_KEY')
        print(f"API Key loaded: {api_key is not None}")
        client = AsyncGroq(api_key=api_key)
        res = await client.chat.completions.create(
            model='llama3-8b-8192', 
            messages=[{'role': 'user', 'content': 'test'}]
        )
        print("Response:", res.choices[0].message.content)
    except Exception as e:
        traceback.print_exc()

asyncio.run(test())
