import asyncio
from concurrent.futures import ThreadPoolExecutor


# Dedicated thread pool for blocking LLM/TTS work
# max_workers=4 means 4 concurrent LLM calls max
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="llm_worker")


async def run_in_thread(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, func, *args)