import asyncio 
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=12, thread_name_prefix="worker")


async def run_in_thread(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, func, *args)
    