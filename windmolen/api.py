import asyncio
from typing import (
    AsyncIterator,
    Awaitable,
    Callable,
    Generic,
    Optional,
    Type,
    Tuple,
    TypeVar,
    Union,
)
from typing_extensions import Self
from types import TracebackType

T = TypeVar("T")
R = TypeVar("R")

T_OR_STOP = Union[T, StopAsyncIteration]
FN_REF = Callable[[], Awaitable[T]]
FN_REF_RESULT = Tuple[FN_REF[T], T_OR_STOP[T]]

_SENTINEL = object()


async def _fn_ref_and_result(
    fn: FN_REF[T],
) -> FN_REF_RESULT[T]:
    try:
        result = await fn()
        return fn, result
    except StopAsyncIteration as e:
        return fn, e


class FanIn(Generic[T]):
    def __init__(self, *iters: AsyncIterator[T]):
        self._queue: asyncio.Queue[Union[T, object]] = asyncio.Queue()
        self._iters = iters
        self._tasks: set[asyncio.Task[FN_REF_RESULT[T]]] = set()

    def _done_callback(self, t: "asyncio.Task[FN_REF_RESULT[T]]"):
        global _SENTINEL

        fn, result = t.result()
        self._tasks.remove(t)
        if isinstance(result, StopAsyncIteration):
            self._queue.put_nowait(_SENTINEL)
            return
        task = asyncio.create_task(_fn_ref_and_result(fn))
        task.add_done_callback(self._done_callback)
        self._tasks.add(task)

        self._queue.put_nowait(result)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_value: Optional[BaseException] = None,
        exc_traceback: Optional[TracebackType] = None,
    ):
        await self.stop()

    def __aiter__(self) -> AsyncIterator[T]:
        for iterator in self._iters:
            self._tasks.add(asyncio.create_task(_fn_ref_and_result(iterator.__anext__)))

        for task in self._tasks:
            task.add_done_callback(self._done_callback)

        return self

    async def __anext__(self) -> T:
        while self._tasks:
            value = await self._queue.get()
            if value == _SENTINEL:
                continue
            return value
        raise StopAsyncIteration

    async def stop(self):
        for task in self._tasks:
            task.remove_done_callback(self._done_callback)
            task.cancel()
