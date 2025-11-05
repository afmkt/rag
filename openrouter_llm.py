import os
import openai
from rich import print
from dotenv import load_dotenv
load_dotenv()
class OpenRouterLLM:
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv("OPEN_ROUTER_API_KEY")
        # Use the environment variable OPEN_ROUTER_MODEL as the default model
        self.model = model or os.getenv("OPEN_ROUTER_MODEL")
        if not self.model:
            raise ValueError("OPEN_ROUTER_MODEL environment variable must be set to a valid model id.")
        print(f"[OpenRouterLLM] Using model: {self.model}")
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )

    def invoke(self, prompt: str):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        class Result:
            def __init__(self, content):
                self.content = content
        return Result(response.choices[0].message.content)
