import asyncio
from typing import Awaitable, Callable, List, TypeVar

T = TypeVar("T")


async def run_with_limit(tasks: List[Callable[[], Awaitable[T]]], limit: int) -> List[T]:
    semaphore = asyncio.Semaphore(limit)

    async def _runner(task_factory: Callable[[], Awaitable[T]]) -> T:
        async with semaphore:
            return await task_factory()

    return await asyncio.gather(*[_runner(task) for task in tasks])

