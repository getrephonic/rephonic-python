import pytest
import pytest_asyncio

from rephonic import AsyncRephonic, Rephonic


@pytest.fixture
def client():
    with Rephonic(api_key="test-key", max_retries=0) as c:
        yield c


@pytest_asyncio.fixture
async def aclient():
    async with AsyncRephonic(api_key="test-key", max_retries=0) as c:
        yield c
