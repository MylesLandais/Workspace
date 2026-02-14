"""Pytest configuration for E2E tests."""

import pytest
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from puppeteer_test_setup import PuppeteerTestBase, GraphQLTestClient


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def puppeteer():
    """Puppeteer test fixture."""
    base = PuppeteerTestBase(headless=True)
    await base.setup()
    yield base
    await base.teardown()


@pytest.fixture
def graphql_client():
    """GraphQL client fixture."""
    return GraphQLTestClient()




