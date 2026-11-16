import asyncio
import sys
from app.config import settings
from app.providers import OpenRouterProvider
async def main(model):
    p = OpenRouterProvider(settings.openrouter_api_key)
    resp = await p.complete(model, [{"role": "user", "content": "Say hi in 5 words."}],
    max_tokens=100)
    print(resp["choices"][0]["message"]["content"], "|", resp.get("usage"))


asyncio.run(main(sys.argv[1]))
