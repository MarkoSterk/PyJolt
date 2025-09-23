"""
Test setup
"""

import pytest
from pyjolt.testing import PyJoltTestClient
from app import create_app

@pytest.fixture
async def app():
    app = create_app()
    yield app

@pytest.fixture
async def client(app):
    async with PyJoltTestClient(app) as c:
        yield c
