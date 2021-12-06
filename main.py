from typing import Optional

from sqlalchemy.sql.schema import ForeignKey
from fastapi import FastAPI, status
from pydantic import BaseModel
from ui.start import *

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session , relationship
from fastapi.middleware.cors import CORSMiddleware

engine = create_engine("sqlite:///data.db")

Base = declarative_base()

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer , primary_key=True)
    number = Column(Integer)
    name = Column(String())
    description = Column(String())

class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer , primary_key=True)
    query = Column(String)
    article_limit = Column(Integer)
    age_limit = Column(Integer)
    etape = Column(Integer)
    created_at = Column(String)

class CategoryToRequest(Base):
    __tablename__ = "category_to_request"
    id = Column(Integer , primary_key=True)
    id_request = Column(Integer)
    id_category = Column(Integer)
    id_result = Column(Integer)
    comment = Column(String)

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer , primary_key=True)
    sentence = Column(String)
    article_name = Column(String)
    article_link = Column(String)
    value = Column(Integer)
    in_what = Column(String)
    method = Column(String)
    subject = Column(String)

class Search(BaseModel):
    bw : str
    keywords : Optional[str]


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/search" , status_code=status.HTTP_201_CREATED)
def search(search : Search):
    a = Start(max_articles=10)
    request_id = a.traitement(search.bw , search.keywords)
    return { "request_id" : request_id}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

@app.get("/requests")
def get_requests():
    session = Session(bind=engine , expire_on_commit=False)
    requests = session.query(Request).all()
    session.close()
    return requests

@app.get("/requests/{request_id}" )
def get_request(request_id):
    session = Session(bind=engine , expire_on_commit=False)
    request = session.query(CategoryToRequest , Request , Result , Category).filter(Request.id == request_id , CategoryToRequest.id_request == Request.id , CategoryToRequest.id_result == Result.id , CategoryToRequest.id_category == Category.id).all()
    session.close()
    return request



@app.get("/categories")
def get_categories():
    session = Session(bind=engine , expire_on_commit=False)
    categories = session.query(Category).all()
    session.close()
    return categories