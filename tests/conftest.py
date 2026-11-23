import pytest
import pytest_asyncio

from rephonic import AsyncRephonic, Rephonic


@pytest.fixture(autouse=True)
def _no_api_version_env(monkeypatch):
    monkeypatch.delenv("REPHONIC_API_VERSION", raising=False)


@pytest.fixture
def client():
    with Rephonic(api_key="test-key", max_retries=0) as c:
        yield c


@pytest_asyncio.fixture
async def aclient():
    async with AsyncRephonic(api_key="test-key", max_retries=0) as c:
        yield c
