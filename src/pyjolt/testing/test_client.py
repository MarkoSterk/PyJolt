"""
Test client class
"""
from httpx import AsyncClient, ASGITransport

from ..pyjolt import PyJolt

class TestClient:
    """
    Test client class for testing of PyJolt applications
    """
    def __init__(self, app: PyJolt):
        self.app = app
        self.transport = ASGITransport(app = self.app)
        self.client = AsyncClient(transport=self.transport, base_url=app.get_conf("APP_TEST_URL", ""))

    async def request(self, method: str, path: str, **kwargs):
        """
        Universal method for requests
        """
        response = await self.client.request(method, path, **kwargs)
        return response

    async def get(self, path: str, **kwargs):
        """
        Method for GET request testing
        """
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs):
        """
        Method for POST request testing
        """
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs):
        """
        Method for PUT request testing
        """
        return await self.request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs):
        """
        Method for PATCH request testing
        """
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs):
        """
        Method for DELETE request testing
        """
        return await self.request("DELETE", path, **kwargs)

    async def close(self):
        """
        Closes test client
        """
        await self.client.aclose()
