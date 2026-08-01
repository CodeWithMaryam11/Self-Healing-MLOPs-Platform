import asyncio
from db import connect_to_mongo, close_mongo_connection, get_db

async def check_user():
    await connect_to_mongo()
    db = get_db()
    
    user = await db.users.find_one({"email": "test@pipelineiq.com"})
    if user:
        print("YES! User exists:", user)
    else:
        print("NO! User was not created due to the crash.")
        
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(check_user())
