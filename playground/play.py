from attr import attrs, attrib
from typing import List
from trio import open_nursery
import trio
from trio_typing import Nursery


class WorkItem:
    def __init__(self, fn, *args):
        self.fn = fn
        self.args = args


class TrioExecutor:
    def __init__(self):
        self._work_queue: List[WorkItem] = []
        self.running: int = 0

    def __enter__(self):
        return self

    def submit(self, fn, /, *args):
        w = WorkItem(fn, *args)
        self._work_queue.append(w)

    def __exit__(self, exc_type, exc_val, exc_tb):
        nm_worker = 3

        async def wait_and_call():
            while len(self._work_queue) > 0:
                if self.running < 3:
                    self.running += 1
                    work: WorkItem = self._work_queue.pop(0)
                    async with open_nursery() as n:
                        n.start_soon(work.fn, *work.args)
                    self.running -= 1
                else:
                    await trio.sleep(0.01)

        async def start():
            async with open_nursery() as nursery:
                for i in range(nm_worker):
                    nursery.start_soon(wait_and_call)

        trio.run(start)


if __name__ == "__main__":

    async def count(id: int):
        for i in range(10):
            await trio.sleep(0.5)
            print(f"[{id}]: {i}")

    with TrioExecutor() as e:
        for i in range(10):
            e.submit(count, i)
