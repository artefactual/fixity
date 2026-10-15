from collections.abc import Iterator

import pytest

from fixity.models import engine


@pytest.fixture(autouse=True, scope="session")
def dispose_engine() -> Iterator[None]:
    """Close the pooled database connections once the test session ends."""
    yield
    engine.dispose()
