"""
HiAnime API - Simple anime streaming API
"""

from fastapi import FastAPI, HTTPException, Query
from contextlib import asynccontextmanager
from hianime import HiAnime

hianime: HiAnime = None

# Valid parameter values
VALID_SERVERS = ["HD-1", "HD-2", "HD-3", "StreamTape"]
VALID_TYPES = ["sub", "dub", "raw", "mixed"]


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
async def search(q: str = Query(..., min_length=1, description="Search query"), page: int = Query(1, ge=1, description="Page number")):
    """Search anime by keyword"""
    result = await hianime.search(q, page)
    if result.get("error"):
        raise HTTPException(status_code=503, detail=result["error"])
    if not result.get("results"):
        raise HTTPException(status_code=404, detail=f"No results found for query '{q}'")
    return result


@app.get("/popular")
async def popular(page: int = Query(1, ge=1, description="Page number")):
    """Most popular anime"""
    result = await hianime.get_popular(page)
    if result.get("error"):
        raise HTTPException(status_code=503, detail=result["error"])
    if not result.get("results"):
        raise HTTPException(status_code=404, detail=f"No popular anime found for page {page}")
    return result


@app.get("/latest")
async def latest(page: int = Query(1, ge=1, description="Page number")):
    """Recently updated anime"""
    result = await hianime.get_latest(page)
    if result.get("error"):
        raise HTTPException(status_code=503, detail=result["error"])
    if not result.get("results"):
        raise HTTPException(status_code=404, detail=f"No latest anime found for page {page}")
    return result


@app.get("/info/{anime_id}")
async def info(anime_id: str):
    """Get anime details"""
    result = await hianime.get_anime_details(anime_id)
    if result.get("error"):
        error_msg = result["error"]
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=503, detail=error_msg)
    return result


@app.get("/episodes/{anime_id}")
async def episodes(anime_id: str):
    """Get all episodes for an anime"""
    result = await hianime.get_episodes(anime_id)
    if result.get("error"):
        error_msg = result["error"]
        if "invalid" in error_msg.lower():
            raise HTTPException(status_code=400, detail=error_msg)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=503, detail=error_msg)
    if not result.get("episodes"):
        raise HTTPException(status_code=404, detail=f"No episodes found for anime '{anime_id}'")
    return result


@app.get("/servers/{episode_id}")
async def servers(episode_id: str):
    """Get available servers for an episode"""
    result = await hianime.get_episode_servers(episode_id)
    if result.get("error"):
        error_msg = result["error"]
        if "invalid" in error_msg.lower():
            raise HTTPException(status_code=400, detail=error_msg)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=503, detail=error_msg)
    # Check if any servers are available
    all_servers = result.get("servers", {})
    has_servers = any(all_servers.get(t) for t in VALID_TYPES)
    if not has_servers:
        raise HTTPException(status_code=404, detail=f"No servers found for episode '{episode_id}'")
    return result


@app.get("/watch/{episode_id}")
async def watch(episode_id: str, server: str = "HD-1", type: str = "sub"):
    """
    Get video stream URL
    
    - server: HD-1, HD-2, HD-3, StreamTape
    - type: sub, dub, raw, mixed
    
    Returns m3u8 URL with required headers (referer)
    """
    # Validate server parameter
    if server not in VALID_SERVERS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid server '{server}'. Valid options: {', '.join(VALID_SERVERS)}"
        )
    
    # Validate type parameter
    if type not in VALID_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid type '{type}'. Valid options: {', '.join(VALID_TYPES)}"
        )
    
    result = await hianime.get_video(episode_id, server, type)
    
    if result.get("error"):
        # Check if it's a server not found error
        if "not found" in result["error"].lower():
            raise HTTPException(status_code=404, detail=result["error"])
        raise HTTPException(status_code=400, detail=result["error"])
    
    if not result.get("videos"):
        raise HTTPException(
            status_code=404, 
            detail=f"No video streams found for episode '{episode_id}' with server '{server}' and type '{type}'"
        )
    
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
