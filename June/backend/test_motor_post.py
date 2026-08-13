from fastapi import FastAPI
from pydantic import BaseModel
import certifi
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

class Item(BaseModel):
    name: str

client = AsyncIOMotorClient('mongodb+srv://mominzahoor-selfhealingmlops:selfhealingmlops@cluster0.bt7hyad.mongodb.net', tlsCAFile=certifi.where())

@app.post("/test")
async def test_post(item: Item):
    return {"message": item.name}
