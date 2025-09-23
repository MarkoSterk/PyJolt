"""
Test setup
"""

import asyncio
import pytest
from pyjolt.testing import PyJoltTestClient

from app import create_app

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def app():
    # Build your ASGI app in testing mode
    app = create_app()
    yield app

@pytest.fixture
async def client(app):
    # Your client supports "async with"
    async with PyJoltTestClient(app) as c:
        yield c
