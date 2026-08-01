import asyncio
from main import register, login, RegisterRequest, LoginRequest
from db import connect_to_mongo, close_mongo_connection

async def test_auth_direct():
    print("Connecting to DB...")
    await connect_to_mongo()
    
    print("\n--- Testing Registration ---")
    reg_req = RegisterRequest(
        name="Test User",
        email="test2@pipelineiq.com",
        password="securepassword123"
    )
    
    try:
        res = await register(reg_req)
        print("Registration Success:", res)
    except Exception as e:
        print("Registration Failed:", e)
        
    print("\n--- Testing Login ---")
    log_req = LoginRequest(
        email="test2@pipelineiq.com",
        password="securepassword123"
    )
    
    try:
        res = await login(log_req)
        print("Login Success! Token:", res["token"][:30] + "...")
        print("User Data:", res["user"])
    except Exception as e:
        print("Login Failed:", e)
        
    print("\nClosing DB Connection...")
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test_auth_direct())
