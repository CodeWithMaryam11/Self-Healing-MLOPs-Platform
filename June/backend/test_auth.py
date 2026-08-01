import asyncio
# pyrefly: ignore [missing-import]
import nest_asyncio
nest_asyncio.apply()

# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
from main import app, startup_db_client, shutdown_db_client

client = TestClient(app)

async def test_auth():
    print("Starting DB Client...")
    await startup_db_client()
    
    print("\n--- Testing Registration ---")
    register_payload = {
        "name": "Test User",
        "email": "test@pipelineiq.com",
        "password": "securepassword123"
    }
    res = client.post("/api/v1/auth/register", json=register_payload)
    print("Register Response Status:", res.status_code)
    print("Register Response Body:", res.json())
    
    print("\n--- Testing Login ---")
    login_payload = {
        "email": "test@pipelineiq.com",
        "password": "securepassword123"
    }
    res = client.post("/api/v1/auth/login", json=login_payload)
    print("Login Response Status:", res.status_code)
    print("Login Response Body:", res.json())
    
    if res.status_code == 200:
        token = res.json().get("token")
        print("\nSuccessfully received JWT Token:", token[:20] + "...")
        
    print("\nShutting down DB Client...")
    await shutdown_db_client()

if __name__ == "__main__":
    asyncio.run(test_auth())
