import pytest


def test_placeholder() -> None:
    """A placeholder test to ensure CI passes when no real tests are present."""
    assert True


@pytest.mark.asyncio
async def test_async_placeholder() -> None:
    """A placeholder async test to verify pytest-asyncio configuration."""
    assert True
