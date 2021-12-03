from typing import Optional
from fastapi import FastAPI, status
from pydantic import BaseModel

app = FastAPI()

class Search(BaseModel):
    bw : str
    keywords : Optional[str]


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/search" , status_code=status.HTTP_201_CREATED)
def search(search : Search):
    
    return "Search successful"

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}