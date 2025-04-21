# main.py
from fastapi import FastAPI, Query, HTTPException
import httpx
import os
from dotenv import load_dotenv
from schema import Article, TopStoriesResponse, SectionsResponse, ArticleSearchItem, ArticleSearchResponse
from typing import List, Optional
from datetime import datetime

load_dotenv()

app = FastAPI()

NYT_API_KEY = os.getenv("NYT_API_KEY")
NYT_TOP_STORIES_URL = "https://api.nytimes.com/svc/topstories/v2"


@app.get("/section/{section}", response_model=TopStoriesResponse)
async def get_top_stories(section: str):
    url = f"{NYT_TOP_STORIES_URL}/{section}.json"
    params = {"api-key": NYT_API_KEY}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Error fetching section from NYT API")

            data = response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"NYT API error: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching data from NYT API: {str(e)}"
            )
    articles = [
        Article(
            title=article["title"],
            abstract=article["abstract"],
            section=article["section"],
            url=article["url"],
            published_date=article["published_date"]
        )
        for article in data.get("results", [])
    ]

    return TopStoriesResponse(
        section=section,
        last_updated=data.get("last_updated"),
        results=articles
    )


@app.get("/nytimes/topstories", response_model=SectionsResponse)
async def get_sections():
    sections = ["arts", "food", "movies", "travel", "science"]
    section_data = {}

    async with httpx.AsyncClient() as client:
        for section in sections:
            url = f"{NYT_TOP_STORIES_URL}/{section}.json"
            params = {"api-key": NYT_API_KEY}
            response = await client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                articles = sorted(
                    data.get("results", []),
                    key=lambda x: x.get("published_date", ""),
                    reverse=True
                )[:2]
                data = [
                    Article(
                        title=article["title"],
                        abstract=article["abstract"],
                        section=article["section"],
                        url=article["url"],
                        published_date=article["published_date"]
                    )
                    for article in articles
                ]
                section_data[section] = data
            else:
                section_data[section] = None
    return SectionsResponse(**section_data)


@app.get("/nytime/articlesearch", response_model=ArticleSearchResponse)
async def article_search(
    q: str = Query(..., description="Search query string"),
    begin_date: Optional[str] = Query(None, regex=r"^\d{8}$", description="Begin date in YYYYMMDD format"),
    end_date: Optional[str] = Query(None, regex=r"^\d{8}$", description="End date in YYYYMMDD format"),
    sort: Optional[str] = Query("newest", regex="^(newest|oldest)$", description="Sort order: newest or oldest")
):
    url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
    params = {
        "q": q,
        "api-key": NYT_API_KEY,
        "sort": sort
    }

    if begin_date:
        params["begin_date"] = begin_date
    if end_date:
        params["end_date"] = end_date

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching article search")

    data = response.json()
    docs = data.get("response", {}).get("docs", [])

    results = [
        ArticleSearchItem(
            headline=doc.get("headline", {}).get("main", "No headline"),
            snippet=doc.get("snippet", "No snippet"),
            web_url=doc.get("web_url"),
            pub_date=doc.get("pub_date")
        )
        for doc in docs
    ]

    return ArticleSearchResponse(query=q, results=results)
