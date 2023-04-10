from queue import Queue, Full, Empty
from typing import Generic, TypeVar
from asyncio import sleep


T = TypeVar('T')


class AsyncQueue(Generic[T]):
    """Async wrapper for queue.Queue"""

    SLEEP: float = 0.01

    def __init__(self, queue: Queue[T]) -> None:
        self._Q: Queue[T] = queue

    def get_nowait(self) -> T:
        return self._Q.get_nowait()

    async def get(self) -> T:
        while True:
            try:
                return self.get_nowait()
            except Empty:
                await sleep(self.SLEEP)

    async def put(self, item: T) -> None:
        while True:
            try:
                self._Q.put_nowait(item)
                return None
            except Full:
                await sleep(self.SLEEP)

    def task_done(self) -> None:
        self._Q.task_done()
        return None

    @property
    def sync_queue(self) -> Queue[T]:
        return self._Q
