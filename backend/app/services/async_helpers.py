import asyncio
from app.core.thread_pool import run_in_thread

async def run_in_thread(func, *args):
    return await run_in_thread(func, *args)