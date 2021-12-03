from typing import Optional
from fastapi import FastAPI, status
from pydantic import BaseModel
from ui.article_search import *

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

engine = create_engine("sqlite:///data.db")

Base = declarative_base()

app = FastAPI()

class Categories(Base):
    __tablename__ = 'categories'
    id = Column(Integer , primary_key=True)
    number = Column(Integer)
    name = Column(String())
    description = Column(String())


class Search(BaseModel):
    bw : str
    keywords : Optional[str]


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/search" , status_code=status.HTTP_201_CREATED)
def search(search : Search):
    a = ArticleSearch(pubmed_limt=4)
    a.traitement_mots(search.bw , search.keywords)
    return "Search successful"

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}


@app.get("/categories")
def get_categories():
    session = Session(bind=engine , expire_on_commit=False)
    categories = session.query(Categories).all()
    session.close()

    return categories