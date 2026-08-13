from fastapi import FastAPI
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
app = FastAPI()

@app.post("/test")
async def test_post():
    print("Hashing...")
    hashed = pwd_context.hash("Test@1234")
    print("Done")
    return {"message": "ok"}
