"""
HiAnime API - Simple anime streaming API
"""

from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from hianime import HiAnime

hianime: HiAnime = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global hianime
    hianime = HiAnime()
    yield
    await hianime.close()


app = FastAPI(
    title="HiAnime API",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {
        "api": "HiAnime",
        "endpoints": [
            "GET /search?q=boruto&page=1",
            "GET /popular?page=1",
            "GET /latest?page=1",
            "GET /info/{anime_id}",
            "GET /episodes/{anime_id}",
            "GET /servers/{episode_id}",
            "GET /watch/{episode_id}?server=HD-1&type=sub",
        ]
    }


@app.get("/search")
async def search(q: str, page: int = 1):
    """Search anime by keyword"""
    return await hianime.search(q, page)


@app.get("/popular")
async def popular(page: int = 1):
    """Most popular anime"""
    return await hianime.get_popular(page)


@app.get("/latest")
async def latest(page: int = 1):
    """Recently updated anime"""
    return await hianime.get_latest(page)


@app.get("/info/{anime_id}")
async def info(anime_id: str):
    """Get anime details"""
    return await hianime.get_anime_details(anime_id)


@app.get("/episodes/{anime_id}")
async def episodes(anime_id: str):
    """Get all episodes for an anime"""
    return await hianime.get_episodes(anime_id)


@app.get("/servers/{episode_id}")
async def servers(episode_id: str):
    """Get available servers for an episode"""
    return await hianime.get_episode_servers(episode_id)


@app.get("/watch/{episode_id}")
async def watch(episode_id: str, server: str = "HD-1", type: str = "sub"):
    """
    Get video stream URL
    
    - server: HD-1, HD-2, HD-3, StreamTape
    - type: sub, dub, raw
    
    Returns m3u8 URL with required headers (referer)
    """
    return await hianime.get_video(episode_id, server, type)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=25565)
