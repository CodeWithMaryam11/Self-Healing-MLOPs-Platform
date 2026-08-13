from fastapi import FastAPI
import asyncio
import certifi
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()
client = AsyncIOMotorClient('mongodb+srv://mominzahoor-selfhealingmlops:selfhealingmlops@cluster0.bt7hyad.mongodb.net', tlsCAFile=certifi.where())

@app.get("/")
async def root():
    try:
        result = await asyncio.wait_for(client.admin.command('ping'), timeout=5.0)
        return {"result": result}
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}
