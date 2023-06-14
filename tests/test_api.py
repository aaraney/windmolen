import pytest
from windmolen.api import FanIn
from typing import AsyncIterator

pytestmark = pytest.mark.asyncio


async def simple_iter(rng: range) -> AsyncIterator[int]:
    for item in rng:
        yield item


async def test_fan_in():
    ranges = (
        simple_iter(range(0, 1)),
        simple_iter(range(1, 2)),
    )

    expected = set(range(0, 2))
    async with FanIn(*ranges) as async_iter:
        async for item in async_iter:
            assert item in expected


async def test_fan_in_uneven_iterators():
    ranges = (
        simple_iter(range(0, 1)),
        simple_iter(range(1, 3)),
    )

    expected = set(range(0, 3))
    async with FanIn(*ranges) as async_iter:
        async for item in async_iter:
            assert item in expected
