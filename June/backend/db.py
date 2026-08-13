import os
import certifi
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")

# Use certifi's CA bundle for SSL verification (fixes macOS certificate issues)
_is_atlas = "mongodb+srv" in MONGO_URL or "mongodb.net" in MONGO_URL
_tls_ca_file = certifi.where() if _is_atlas else None

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_to_mongo():
    db_instance.client = AsyncIOMotorClient(MONGO_URL, tlsCAFile=_tls_ca_file)
    db_instance.db = db_instance.client.pipelineiq
    print(f"Connected to MongoDB at {MONGO_URL}")

async def close_mongo_connection():
    if db_instance.client:
        db_instance.client.close()
        print("Closed MongoDB connection")

def get_db():
    return db_instance.db

# Sync DB (PyMongo) - Lazy initialization for background threads / CPU heavy tasks
_sync_client = None
_sync_db = None

def get_sync_db():
    global _sync_client, _sync_db
    if _sync_db is None:
        try:
            # pyrefly: ignore [missing-import]
            from pymongo import MongoClient
            _sync_client = MongoClient(MONGO_URL, tlsCAFile=_tls_ca_file)
            _sync_db = _sync_client.pipelineiq
        except Exception as e:
            print(f"Failed to initialize sync MongoClient: {e}")
            _sync_db = None
    return _sync_db
