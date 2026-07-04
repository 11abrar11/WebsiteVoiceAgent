import os
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class LLMService:
    def __init__(self):
        self.client = AsyncGroq(api_key=GROQ_API_KEY)
        # Using llama-3.3-70b-versatile as requested
        self.model = "llama-3.3-70b-versatile"

    async def generate_response(self, system_prompt: str, chat_history: list) -> str:
        """
        Generates a non-streaming response using the Groq API.
        chat_history should be a list of dictionaries with 'role' and 'content'.
        """
        messages = [{"role": "system", "content": system_prompt}] + chat_history
        
        try:
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=256,
                top_p=1,
                stream=False,
                stop=None,
            )
            return completion.choices[0].message.content
        except Exception as e:
            import traceback
            traceback.print_exc()
            return "I'm having a little trouble thinking right now. Could you repeat that?"

    async def generate_response_stream(self, system_prompt: str, chat_history: list):
        """
        Generates a streaming response using the Groq API.
        Yields text chunks as they arrive.
        """
        messages = [{"role": "system", "content": system_prompt}] + chat_history
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=512,
                top_p=1,
                stream=True,
                stop=None,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield " I'm having a little trouble thinking right now. Could you repeat that?"

llm_service = LLMService()
