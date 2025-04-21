from pydantic import BaseModel, HttpUrl, validator, Field
from typing import List, Optional
from datetime import datetime

class Article(BaseModel):
    title: str
    abstract: str
    section: str
    url: HttpUrl
    published_date: datetime

class TopStoriesResponse(BaseModel):
    section: str
    last_updated: Optional[datetime]
    results: List[Article]


class SectionsResponse(BaseModel):
    arts: Optional[List[Article]]
    food: Optional[List[Article]]
    movies: Optional[List[Article]]
    travel: Optional[List[Article]]
    science: Optional[List[Article]]


class ArticleSearchItem(BaseModel):
    headline: str
    snippet: str
    web_url: HttpUrl
    pub_date: datetime


class ArticleSearchResponse(BaseModel):
    query: str
    results: List[ArticleSearchItem]
