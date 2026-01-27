# HiAnime API

A Python API for streaming anime from HiAnime. Supports search, browse, and video extraction with Sub/Dub/Raw options.

## Installation

```bash
# Clone or download the project
cd HiAnime

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Run the API server
python -m uvicorn app:app --host 0.0.0.0 --port 8000

# Or simply
python app.py
```

API will be available at `http://localhost:8000`

## API Endpoints

### Search Anime

```
GET /search?q={query}&page={page}
```

**Example:**
```bash
curl "http://localhost:8000/search?q=boruto"
```

**Response:**
```json
{
  "results": [
    {
      "id": "boruto-naruto-next-generations-8143",
      "title": "Boruto: Naruto Next Generations",
      "url": "/boruto-naruto-next-generations-8143",
      "thumbnail": "https://cdn.hianime.to/..."
    }
  ],
  "has_next_page": true,
  "page": 1
}
```

---

### Popular Anime

```
GET /popular?page={page}
```

**Example:**
```bash
curl "http://localhost:8000/popular"
```

---

### Latest/Recently Updated

```
GET /latest?page={page}
```

**Example:**
```bash
curl "http://localhost:8000/latest"
```

---

### Anime Details

```
GET /info/{anime_id}
```

**Example:**
```bash
curl "http://localhost:8000/info/boruto-naruto-next-generations-8143"
```

**Response:**
```json
{
  "id": "boruto-naruto-next-generations-8143",
  "title": "Boruto: Naruto Next Generations",
  "japanese_title": "BORUTO-ボルト- NARUTO NEXT GENERATIONS",
  "thumbnail": "https://cdn.hianime.to/...",
  "status": "Completed",
  "studios": "Pierrot",
  "genres": "Action, Adventure, Martial Arts, Shounen, Super Power",
  "description": "..."
}
```

---

### Get Episodes

```
GET /episodes/{anime_id}
```

**Example:**
```bash
curl "http://localhost:8000/episodes/boruto-naruto-next-generations-8143"
```

**Response:**
```json
{
  "anime_id": "boruto-naruto-next-generations-8143",
  "total_episodes": 293,
  "episodes": [
    {
      "id": "92761",
      "number": 1,
      "title": "Ep. 1: Boruto Uzumaki!",
      "is_filler": false
    },
    {
      "id": "92762",
      "number": 2,
      "title": "Ep. 2: The Hokage's Son!",
      "is_filler": false
    }
  ]
}
```

---

### Get Servers

```
GET /servers/{episode_id}
```

**Example:**
```bash
curl "http://localhost:8000/servers/92761"
```

**Response:**
```json
{
  "episode_id": "92761",
  "servers": {
    "sub": [
      {"id": "1024602", "name": "HD-1", "type": "sub"},
      {"id": "1024600", "name": "HD-2", "type": "sub"}
    ],
    "dub": [
      {"id": "1124782", "name": "HD-1", "type": "dub"},
      {"id": "1124729", "name": "HD-2", "type": "dub"}
    ],
    "raw": [],
    "mixed": []
  }
}
```

---

### Get Video Stream

```
GET /watch/{episode_id}?server={server}&type={type}
```

**Parameters:**
| Parameter | Default | Options |
|-----------|---------|---------|
| `server` | `HD-1` | `HD-1`, `HD-2`, `HD-3`, `StreamTape` |
| `type` | `sub` | `sub`, `dub`, `raw`, `mixed` |

**Example:**
```bash
# Get SUB stream from HD-1
curl "http://localhost:8000/watch/92761?server=HD-1&type=sub"

# Get DUB stream from HD-2
curl "http://localhost:8000/watch/92761?server=HD-2&type=dub"
```

**Response:**
```json
{
  "episode_id": "92761",
  "server": "HD-1",
  "type": "sub",
  "source_link": "https://megacloud.blog/embed-2/v3/e-1/...",
  "videos": [
    {
      "quality": "HD-1 - 1920x1080 - sub",
      "url": "https://example.com/.../index-f1-v1-a1.m3u8",
      "subtitles": [
        {"url": "https://mgstatics.xyz/.../eng-2.vtt", "label": "English"},
        {"url": "https://mgstatics.xyz/.../spa-5.vtt", "label": "Spanish"}
      ],
      "referer": "https://megacloud.blog/"
    },
    {
      "quality": "HD-1 - 1280x720 - sub",
      "url": "https://example.com/.../index-f2-v1-a1.m3u8",
      "subtitles": [...],
      "referer": "https://megacloud.blog/"
    }
  ]
}
```

---

## Playing the Stream

The M3U8 streams require HTTP headers to play. Use the `referer` from the response.

### VLC (via M3U playlist)

Create a `.m3u` file:
```
#EXTM3U
#EXTVLCOPT:http-referrer=https://megacloud.blog/
#EXTVLCOPT:http-user-agent=Mozilla/5.0
#EXTINF:-1,Episode Title
https://example.com/.../index-f1-v1-a1.m3u8
```

### MPV

```bash
mpv --referrer="https://megacloud.blog/" "https://example.com/.../index-f1-v1-a1.m3u8"
```

### FFplay

```bash
ffplay -headers "Referer: https://megacloud.blog/" "https://example.com/.../index-f1-v1-a1.m3u8"
```

### In Your App

When making HTTP requests to the M3U8 URL, include these headers:
```
Referer: https://megacloud.blog/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

---

## Usage Examples

### Python

```python
import requests

BASE = "http://localhost:8000"

# Search for anime
results = requests.get(f"{BASE}/search", params={"q": "boruto"}).json()
anime_id = results["results"][0]["id"]

# Get episodes
episodes = requests.get(f"{BASE}/episodes/{anime_id}").json()
episode_id = episodes["episodes"][0]["id"]

# Get stream URL
stream = requests.get(f"{BASE}/watch/{episode_id}", params={
    "server": "HD-1",
    "type": "dub"
}).json()

# Extract video info
video = stream["videos"][0]
print(f"URL: {video['url']}")
print(f"Referer: {video['referer']}")
```

### JavaScript/Node.js

```javascript
const BASE = "http://localhost:8000";

// Search
const search = await fetch(`${BASE}/search?q=boruto`).then(r => r.json());
const animeId = search.results[0].id;

// Get episodes
const eps = await fetch(`${BASE}/episodes/${animeId}`).then(r => r.json());
const episodeId = eps.episodes[0].id;

// Get stream
const stream = await fetch(`${BASE}/watch/${episodeId}?server=HD-1&type=sub`).then(r => r.json());
const video = stream.videos[0];

console.log("M3U8:", video.url);
console.log("Referer:", video.referer);
```

### cURL (Full Flow)

```bash
# 1. Search
curl -s "http://localhost:8000/search?q=naruto" | jq '.results[0].id'

# 2. Get episodes
curl -s "http://localhost:8000/episodes/naruto-112" | jq '.episodes[0].id'

# 3. Get stream
curl -s "http://localhost:8000/watch/12345?type=dub" | jq '.videos[0]'
```

---

## Deployment (AWS)

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t hianime-api .
docker run -p 8000:8000 hianime-api
```

### Direct on EC2

```bash
# Install Python
sudo apt update && sudo apt install python3-pip python3-venv

# Setup
git clone <repo> && cd HiAnime
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run with auto-restart
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

---

## Files

| File | Description |
|------|-------------|
| `app.py` | FastAPI application with endpoints |
| `hianime.py` | Main scraper class |
| `megacloud_extractor.py` | Video extraction for HD-1/HD-2/HD-3 |
| `streamtape_extractor.py` | Video extraction for StreamTape |
| `requirements.txt` | Python dependencies |
| `test.py` | Quick test script |

---

## Notes

- Streams are HLS (M3U8) format
- Always use the `referer` header when fetching video segments
- Video URLs expire after some time, fetch fresh when needed
- HD-1 usually provides the best quality
- DUB availability varies by anime

---

## Error Handling

The API returns appropriate HTTP status codes and error messages for various error conditions.

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| `400` | Bad Request - Invalid parameters (e.g., invalid server, type, or ID format) |
| `404` | Not Found - Resource not found (anime, episode, no results) |
| `422` | Unprocessable Entity - Validation error (e.g., missing required parameter) |
| `503` | Service Unavailable - Failed to connect to upstream server |

### Error Examples

#### 404 - Anime Not Found

```bash
curl "http://localhost:8000/info/non-existent-anime-12345"
```

```json
{
  "detail": "Anime 'non-existent-anime-12345' not found"
}
```

#### 404 - No Search Results

```bash
curl "http://localhost:8000/search?q=xyznonexistent123"
```

```json
{
  "detail": "No results found for query 'xyznonexistent123'"
}
```

#### 400 - Invalid Server Parameter

```bash
curl "http://localhost:8000/watch/92761?server=InvalidServer"
```

```json
{
  "detail": "Invalid server 'InvalidServer'. Valid options: HD-1, HD-2, HD-3, StreamTape"
}
```

#### 400 - Invalid Type Parameter

```bash
curl "http://localhost:8000/watch/92761?type=invalid"
```

```json
{
  "detail": "Invalid type 'invalid'. Valid options: sub, dub, raw, mixed"
}
```

#### 422 - Missing Required Parameter

```bash
curl "http://localhost:8000/search"
```

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["query", "q"],
      "msg": "Field required"
    }
  ]
}
```

#### 422 - Invalid Page Number

```bash
curl "http://localhost:8000/search?q=naruto&page=0"
```

```json
{
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": ["query", "page"],
      "msg": "Input should be greater than or equal to 1"
    }
  ]
}
```

#### 400 - Invalid Episode ID Format

```bash
curl "http://localhost:8000/servers/invalid-id"
```

```json
{
  "detail": "Invalid episode ID 'invalid-id'. Episode ID must be numeric."
}
```

#### 503 - Service Unavailable

```bash
curl "http://localhost:8000/search?q=naruto"
```

```json
{
  "detail": "Failed to connect to server: Cannot connect to host hianime.to:443"
}
```

## License

This project is licensed under the [CC BY-NC 4.0](LICENSE) license.

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
