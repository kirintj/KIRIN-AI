import pytest


@pytest.mark.asyncio
async def test_login_missing_credentials(client):
    response = await client.post("/api/v1/base/access_token", json={})
    assert response.status_code == 422
