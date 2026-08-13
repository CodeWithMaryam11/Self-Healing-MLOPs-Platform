from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str

@app.post("/test")
async def test_post(item: Item):
    print("DEBUG: test POST hit")
    return {"message": item.name}
