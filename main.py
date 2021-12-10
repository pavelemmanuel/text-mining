from typing import Optional
from pydantic.types import OptionalInt
from sqlalchemy.sql.expression import select

from sqlalchemy.sql.schema import ForeignKey
from fastapi import FastAPI, status
from pydantic import BaseModel
from starlette import requests
from ui.start import *

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, lazyload, relation , relationship , selectinload
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

    category_to_request = relationship("CategoryToRequest" , back_populates="category")



class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer , primary_key=True)
    query = Column(String)
    article_limit = Column(Integer)
    age_limit = Column(Integer)
    etape = Column(Integer)
    created_at = Column(String)

    category_to_request = relationship("CategoryToRequest" , back_populates="request")

class CategoryToRequest(Base):
    __tablename__ = "category_to_request"
    id = Column(Integer , primary_key=True)
    id_request = Column(Integer , ForeignKey("requests.id"))
    id_category = Column(Integer , ForeignKey("categories.id"))
    comment = Column(String)

    request = relationship("Request" , back_populates="category_to_request")
    results = relationship("Result"  , back_populates="category_to_request")
    category = relationship("Category" , back_populates="category_to_request")

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer , primary_key=True)
    cat_to_req_id = Column(Integer , ForeignKey("category_to_request.id"))
    sentence = Column(String)
    article_name = Column(String)
    article_link = Column(String)
    value = Column(Integer)
    in_what = Column(String)
    method = Column(String)
    subject = Column(String)

    category_to_request = relationship("CategoryToRequest" , back_populates="results")

class Search(BaseModel):
    bw : str
    force : bool = False
    step : int = 0
    keywords : Optional[str]
    nb_article : Optional[int] = 1000


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/search" , status_code=status.HTTP_201_CREATED)
def search(search : Search):
    a = Start(max_articles=search.nb_article)
    step = a.traitement(search.bw , search.keywords , search.step , search.force)
    if step[0] == 2 :
        #Soit il a déjà été fait on le lui demande
        return {"state" : step[0] , "timestamp"  :  step[1] , "request_id" : step[2]}
    elif step[0] == 10 :
        #ca a marché
        return {"state" : step[0] , "timestamp" : step[1] , "request_id" : step[2]}
    elif step[0] == 1 :
        #telechargé pas analysé
        return {"state" : step[0] , "timestamp" : step[1] , "request_id" : step[2]}


@app.get("/requests")
def get_requests():
    session = Session(bind=engine , expire_on_commit=False)
    requests = session.query(Request).filter(Request.etape > 0).all()
    session.close()
    return requests

@app.get("/requests/{request_id}" )
def get_request(request_id):
    session = Session(bind=engine , expire_on_commit=False)

    request = session.query(CategoryToRequest ).options(selectinload(CategoryToRequest.category) , selectinload(CategoryToRequest.request), selectinload(CategoryToRequest.results)).filter(CategoryToRequest.id_request == request_id).all()
    #request = session.query(CategoryToRequest.results ).filter(CategoryToRequest.id_request == request_id).all()
    #request = session.query(CategoryToRequest , Category , Request , Result).filter(CategoryToRequest.id == request_id ,  CategoryToRequest.id_category == Category.id , CategoryToRequest.id_request == Request.id , Result.cat_to_req_id == CategoryToRequest.id).all()
    #request = session.query(CategoryToRequest , Request , Result , Category).filter(Request.id == request_id , CategoryToRequest.id_request == Request.id , CategoryToRequest.id_result == Result.id , CategoryToRequest.id_category == Category.id).all()
    session.close()
    return request

@app.get("/categories")
def get_categories():
    session = Session(bind=engine , expire_on_commit=False)
    categories = session.query(Category).all()
    session.close()
    return categories