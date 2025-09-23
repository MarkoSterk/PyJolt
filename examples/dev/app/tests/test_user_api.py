"""
User API tests
"""

# async def test_healthcheck(client):
#     r = await client.get("/health")
#     assert r.status_code == 200
#     assert r.headers["content-type"].startswith("application/json")
#     assert r.json() == {"status": "ok"}

async def test_get_users(client):
    print("Running this test: ", client)
    res = await client.get("/api/v1/users")
    assert res.status_code == 200


