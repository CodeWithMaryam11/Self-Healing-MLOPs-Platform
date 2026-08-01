import os
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_to_mongo():
    db_instance.client = AsyncIOMotorClient(MONGO_URL)
    db_instance.db = db_instance.client.pipelineiq
    print(f"Connected to MongoDB at {MONGO_URL}")

async def close_mongo_connection():
    if db_instance.client:
        db_instance.client.close()
        print("Closed MongoDB connection")

def get_db():
    return db_instance.db

# Sync DB (PyMongo) - For background threads / CPU heavy tasks
try:
    # pyrefly: ignore [missing-import]
    from pymongo import MongoClient
    sync_client = MongoClient(MONGO_URL)
    sync_db = sync_client.pipelineiq
except ImportError:
    sync_db = None

def get_sync_db():
    return sync_db
