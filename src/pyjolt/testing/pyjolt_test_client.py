"""
Test client class
"""

from httpx import AsyncClient, ASGITransport

class PyJoltTestClient:
    """
    Test client class for testing of PyJolt applications
    """
    def __init__(self, app):
        self.app = app
        self.transport = ASGITransport(app=self.app)
        self.client = AsyncClient(transport=self.transport, base_url="http://testserver")

    # The critical pieces to allow "async with TestClient(app) as client:"
    async def __aenter__(self):
        # __aenter__ can be empty or do any setup
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Here we properly close the underlying client, triggering lifespan.shutdown
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
        # Not strictly needed if you're already doing it in __aexit__, but can keep for convenience
        await self.client.aclose()
