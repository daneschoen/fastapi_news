import pytest
from httpx import AsyncClient, Response
from backend import app
import respx
import json


@pytest.mark.asyncio
async def test_topstories():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/nytimes/topstories")
    assert response.status_code == 200
    data = response.json()
    for section in ["arts", "food", "movies", "travel", "science"]:
        assert section in data
        if isinstance(data[section], list):
            assert len(data[section]) <= 2
            for article in data[section]:
                assert "title" in article
                assert "abstract" in article
                assert "section" in article
                assert "url" in article
                assert "published_date" in article

@pytest.mark.asyncio
@respx.mock
async def test_topstories_invalid_section():
    # Mock one section to fail (e.g., /arts)
    base_url = "https://api.nytimes.com/svc/topstories/v2"
    respx.get(f"{base_url}/arts.json").mock(return_value=Response(500, text="Internal Server Error"))

    sample_ok_response = {
        "status": "OK",
        "results": []
    }

    for section in ["food", "movies", "travel", "science"]:
        respx.get(f"{base_url}/{section}.json").mock(
            return_value=Response(200, json=sample_ok_response)
        )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/nytimes/topstories")

    assert response.status_code == 200
    data = response.json()

    # "arts" should be None or missing
    assert "arts" in data
    assert data["arts"] is None or data["arts"] == []

    # Other sections should be empty lists
    for section in ["food", "movies", "travel", "science"]:
        assert section in data
        assert isinstance(data[section], list)

@pytest.mark.asyncio
async def test_article_search_basic_query():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/nytime/articlesearch?q=climate")
    assert response.status_code == 200
    data = response.json()
    assert "query" in data and data["query"] == "climate"
    assert "results" in data
    if data["results"]:
        result = data["results"][0]
        assert "headline" in result
        assert "snippet" in result
        assert "web_url" in result
        assert "pub_date" in result

@pytest.mark.asyncio
async def test_article_search_with_filters():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/nytime/articlesearch?q=technology&begin_date=20240101&end_date=20240401&sort=oldest"
        )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "technology"
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_article_search_invalid_begin_date():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/nytime/articlesearch?q=climate&begin_date=2024-01-01")
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any("begin_date" in str(err["loc"]) for err in data["detail"])

@pytest.mark.asyncio
async def test_article_search_invalid_sort():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/nytime/articlesearch?q=climate&sort=fastest")
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any("sort" in str(err["loc"]) for err in data["detail"])
