"""
Test client class
"""
from typing import TYPE_CHECKING
from httpx import AsyncClient, ASGITransport

if TYPE_CHECKING:
    from ..pyjolt import PyJolt

class PyJoltTestClient:
    """
    Test client class for testing of PyJolt applications
    """
    def __init__(self, app: "PyJolt"):
        self.app = app
        self.transport = ASGITransport(app=self.app)
        self.client = AsyncClient(transport=self.transport, base_url="http://testserver")

    async def __aenter__(self):
        # __aenter__ can be empty or do any setup
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Properly closes the underlying client, triggering lifespan.shutdown
        await self.client.aclose()

    async def request(self, method: str, path: str, **kwargs):
        response = await self.client.request(method, path, **kwargs)
        return response

    async def get(self, path: str, **kwargs):
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs):
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs):
        return await self.request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs):
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs):
        return await self.request("DELETE", path, **kwargs)

    async def close(self):
        await self.client.aclose()
