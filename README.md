# Windmolen

Treat multiple asynchronous iterators like they are a single asynchronous iterator.

**Example:**

```python
import asyncio
from windmolen import FanIn


async def async_iterator_1():
    for i in range(1, 5):
        yield i
        await asyncio.sleep(0.5)


async def async_iterator_2():
    for j in range(5, 9):
        yield j
        await asyncio.sleep(1)


async def main():
    async with FanIn(async_iterator_1(), async_iterator_2()) as async_iterators:
        async for item in async_iterators:
            print(item)


if __name__ == "__main__":
    asyncio.run(main())
```

## Install

```shell
pip install windmolen
```
