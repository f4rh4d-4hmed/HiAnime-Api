"""
HiAnime - Python port of the Kotlin Aniyomi Extension https://github.com/yuzono/aniyomi-extensions
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode, quote
import json

from megacloud_extractor import MegaCloudExtractor
from streamtape_extractor import StreamTapeExtractor


class HiAnime:
    """
    HiAnime scraper - Python port from Kotlin/Aniyomi
    Supports: Search, Browse, Episode listing, Video extraction
    """
    
    # Available domains (fallback support)
    DOMAINS = [
        "hianime.to",
        "hianime.nz", 
        "hianime.sx",
        "hianime.is",
        "hianime.bz",
        "hianime.pe",
        "hianime.cx",
        "hianime.do",
        "hianimez.is",
    ]
    
    HOSTER_NAMES = ["HD-1", "HD-2", "HD-3", "StreamTape"]
    
    def __init__(self, base_url: str = "https://hianime.to"):
        self.base_url = base_url
        self.ajax_route = "/v2"
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Extractors
        self.megacloud_extractor = MegaCloudExtractor()
        self.streamtape_extractor = StreamTapeExtractor()
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=self._get_headers()
            )
        return self._session
    
    def _get_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        if referer:
            headers["Referer"] = referer
        return headers
    
    def _get_api_headers(self, referer: str) -> Dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Referer": referer,
            "X-Requested-With": "XMLHttpRequest",
        }
    
    async def _fetch(self, url: str, headers: Optional[Dict] = None) -> str:
        session = await self._get_session()
        async with session.get(url, headers=headers or self._get_headers()) as response:
            response.raise_for_status()
            return await response.text()
    
    async def _fetch_json(self, url: str, headers: Optional[Dict] = None) -> Dict:
        session = await self._get_session()
        async with session.get(url, headers=headers or self._get_headers()) as response:
            response.raise_for_status()
            return await response.json()
    
    def _parse_anime_element(self, element, use_english: bool = False) -> Dict[str, Any]:
        """Parse anime from HTML element - mirrors popularAnimeFromElement"""
        detail = element.select_one("div.film-detail a")
        poster = element.select_one("div.film-poster > img")
        
        href = detail.get("href", "") if detail else ""
        # Remove query string like in Kotlin: url.substringBefore("?")
        url = href.split("?")[0] if href else ""
        
        # Get title - prefer English if available, else use Japanese
        if use_english and detail and detail.has_attr("title"):
            title = detail.get("title", "")
        else:
            title = detail.get("data-jname", "") if detail else ""
        
        # Fallback to text content if no attributes
        if not title and detail:
            title = detail.get_text(strip=True)
        
        thumbnail = poster.get("data-src", "") if poster else ""
        
        # Extract anime ID from URL
        anime_id = url.split("/")[-1] if url else ""
        
        return {
            "id": anime_id,
            "title": title,
            "url": url,
            "thumbnail": thumbnail,
        }
    
    def _has_next_page(self, soup: BeautifulSoup) -> bool:
        """Check if there's a next page - mirrors popularAnimeNextPageSelector"""
        return soup.select_one("li.page-item a[title=Next]") is not None
    
    async def search(self, query: str, page: int = 1) -> Dict[str, Any]:
        """Search for anime - mirrors searchAnimeRequest"""
        url = f"{self.base_url}/search?keyword={quote(query)}&page={page}"
        html = await self._fetch(url)
        soup = BeautifulSoup(html, "html.parser")
        
        results = []
        for element in soup.select("div.flw-item"):
            anime = self._parse_anime_element(element)
            if anime["id"]:
                results.append(anime)
        
        return {
            "results": results,
            "has_next_page": self._has_next_page(soup),
            "page": page,
        }
    
    async def get_popular(self, page: int = 1) -> Dict[str, Any]:
        """Get most popular anime - mirrors popularAnimeRequest"""
        url = f"{self.base_url}/most-popular?page={page}"
        html = await self._fetch(url)
        soup = BeautifulSoup(html, "html.parser")
        
        results = []
        for element in soup.select("div.flw-item"):
            anime = self._parse_anime_element(element)
            if anime["id"]:
                results.append(anime)
        
        return {
            "results": results,
            "has_next_page": self._has_next_page(soup),
            "page": page,
        }
    
    async def get_latest(self, page: int = 1) -> Dict[str, Any]:
        """Get recently updated anime - mirrors latestUpdatesRequest"""
        url = f"{self.base_url}/recently-updated?page={page}"
        html = await self._fetch(url)
        soup = BeautifulSoup(html, "html.parser")
        
        results = []
        for element in soup.select("div.flw-item"):
            anime = self._parse_anime_element(element)
            if anime["id"]:
                results.append(anime)
        
        return {
            "results": results,
            "has_next_page": self._has_next_page(soup),
            "page": page,
        }
    
    async def filter_anime(self, page: int = 1, filters: Dict[str, str] = None) -> Dict[str, Any]:
        """Filter anime with various parameters - mirrors searchAnimeRequest with filters"""
        params = {"page": str(page)}
        if filters:
            params.update(filters)
        
        url = f"{self.base_url}/filter?{urlencode(params)}"
        html = await self._fetch(url)
        soup = BeautifulSoup(html, "html.parser")
        
        results = []
        for element in soup.select("div.flw-item"):
            anime = self._parse_anime_element(element)
            if anime["id"]:
                results.append(anime)
        
        return {
            "results": results,
            "has_next_page": self._has_next_page(soup),
            "page": page,
            "filters": filters or {},
        }
    
    async def get_anime_details(self, anime_id: str) -> Dict[str, Any]:
        """Get anime details - mirrors animeDetailsParse"""
        url = f"{self.base_url}/{anime_id}"
        html = await self._fetch(url)
        soup = BeautifulSoup(html, "html.parser")
        
        # Get thumbnail
        poster = soup.select_one("div.anisc-poster img")
        thumbnail = poster.get("src", "") if poster else ""
        
        # Get info section
        info = soup.select_one("div.anisc-info")
        
        def get_info(tag: str, is_list: bool = False) -> Optional[str]:
            if is_list:
                items = info.select(f"div.item-list:contains('{tag}') > a") if info else []
                return ", ".join([item.get_text(strip=True) for item in items]) or None
            item = info.select_one(f"div.item-title:contains('{tag}')") if info else None
            if item:
                name = item.select_one(".name, .text")
                return name.get_text(strip=True) if name else None
            return None
        
        # Parse status
        status_text = get_info("Status:")
        status = "Unknown"
        if status_text:
            if "Currently Airing" in status_text:
                status = "Ongoing"
            elif "Finished Airing" in status_text:
                status = "Completed"
        
        # Build description
        description_parts = []
        overview = get_info("Overview:")
        if overview:
            description_parts.append(overview)
        
        aired = get_info("Aired:")
        if aired:
            description_parts.append(f"\nAired: {aired}")
        
        premiered = get_info("Premiered:")
        if premiered:
            description_parts.append(f"\nPremiered: {premiered}")
        
        synonyms = get_info("Synonyms:")
        if synonyms:
            description_parts.append(f"\nSynonyms: {synonyms}")
        
        japanese = get_info("Japanese:")
        if japanese:
            description_parts.append(f"\nJapanese: {japanese}")
        
        # Get title
        title_elem = soup.select_one("h2.film-name")
        title = title_elem.get_text(strip=True) if title_elem else anime_id
        
        # Get Japanese title
        jp_title_elem = soup.select_one("h2.film-name[data-jname]")
        jp_title = jp_title_elem.get("data-jname", "") if jp_title_elem else ""
        
        return {
            "id": anime_id,
            "title": title,
            "japanese_title": jp_title,
            "thumbnail": thumbnail,
            "status": status,
            "studios": get_info("Studios:"),
            "genres": get_info("Genres:", is_list=True),
            "description": "".join(description_parts),
            "url": f"{self.base_url}/{anime_id}",
        }
    
    async def get_episodes(self, anime_id: str) -> Dict[str, Any]:
        """Get all episodes for an anime - mirrors episodeListRequest/episodeListParse"""
        # Extract numeric ID from anime_id (e.g., "boruto-123" -> "123")
        numeric_id = anime_id.split("-")[-1]
        
        url = f"{self.base_url}/ajax{self.ajax_route}/episode/list/{numeric_id}"
        referer = f"{self.base_url}/{anime_id}"
        
        data = await self._fetch_json(url, self._get_api_headers(referer))
        
        html = data.get("html", "")
        soup = BeautifulSoup(html, "html.parser")
        
        episodes = []
        for element in soup.select("a.ep-item"):
            ep_num_str = element.get("data-number", "1")
            ep_title = element.get("title", "")
            ep_id = element.get("data-id", "")
            href = element.get("href", "")
            
            # Parse episode number (handles 1, 1.5, etc.)
            try:
                ep_num = float(ep_num_str) if ep_num_str else 1.0
            except ValueError:
                ep_num = 1.0
            
            # Check if filler episode
            is_filler = "ssl-item-filler" in element.get("class", [])
            
            # Extract episode ID from href (e.g., "/watch/anime?ep=12345" -> "12345")
            episode_id = href.split("?ep=")[-1] if "?ep=" in href else ep_id
            
            episodes.append({
                "id": episode_id,
                "number": ep_num,
                "title": f"Ep. {ep_num_str}: {ep_title}",
                "is_filler": is_filler,
                "url": href,
            })
        
        # Sort by episode number ascending (1, 1.5, 2, 3...)
        episodes.sort(key=lambda x: x["number"])
        
        return {
            "anime_id": anime_id,
            "total_episodes": len(episodes),
            "episodes": episodes,
        }
    
    async def get_episode_servers(self, episode_id: str, type_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get available servers for an episode - mirrors videoListRequest"""
        url = f"{self.base_url}/ajax{self.ajax_route}/episode/servers?episodeId={episode_id}"
        referer = f"{self.base_url}/watch?ep={episode_id}"
        
        data = await self._fetch_json(url, self._get_api_headers(referer))
        
        html = data.get("html", "")
        soup = BeautifulSoup(html, "html.parser")
        
        servers = {
            "sub": [],
            "dub": [],
            "raw": [],
            "mixed": [],
        }
        
        type_mapping = {
            "servers-sub": "sub",
            "servers-dub": "dub", 
            "servers-raw": "raw",
            "servers-mixed": "mixed",
        }
        
        for server_type, type_key in type_mapping.items():
            if type_filter and type_filter != type_key:
                continue
                
            for item in soup.select(f"div.{server_type} div.item"):
                server_id = item.get("data-id", "")
                server_name = item.get_text(strip=True)
                data_type = item.get("data-type", type_key)
                
                if server_name in self.HOSTER_NAMES:
                    servers[type_key].append({
                        "id": server_id,
                        "name": server_name,
                        "type": data_type,
                    })
        
        return {
            "episode_id": episode_id,
            "servers": servers,
        }
    
    async def _get_server_source_link(self, server_id: str, referer: str) -> str:
        """Get the source link for a server - mirrors sources fetch in getVideoList"""
        url = f"{self.base_url}/ajax{self.ajax_route}/episode/sources?id={server_id}"
        data = await self._fetch_json(url, self._get_api_headers(referer))
        return data.get("link", "")
    
    async def get_video(self, episode_id: str, server: str = "HD-1", type: str = "sub") -> Dict[str, Any]:
        """Get video URL from a specific server - mirrors extractVideo"""
        # First get servers
        servers_data = await self.get_episode_servers(episode_id, type)
        
        # Find the requested server
        type_servers = servers_data["servers"].get(type, [])
        target_server = None
        
        for s in type_servers:
            if s["name"].lower() == server.lower():
                target_server = s
                break
        
        if not target_server:
            # Try to find any matching server in any type if not found
            for t in ["sub", "dub", "mixed", "raw"]:
                for s in servers_data["servers"].get(t, []):
                    if s["name"].lower() == server.lower():
                        target_server = s
                        type = t
                        break
                if target_server:
                    break
        
        if not target_server:
            return {
                "error": f"Server '{server}' not found for type '{type}'",
                "available_servers": servers_data["servers"],
            }
        
        # Get the source link
        referer = f"{self.base_url}/watch?ep={episode_id}"
        source_link = await self._get_server_source_link(target_server["id"], referer)
        
        if not source_link:
            return {"error": "Failed to get source link"}
        
        # Extract video based on server type
        videos = []
        
        if server == "StreamTape":
            video = await self.streamtape_extractor.extract(source_link, f"Streamtape - {type}")
            if video:
                videos = [video]
        elif server in ["HD-1", "HD-2", "HD-3"]:
            videos = await self.megacloud_extractor.extract(source_link, type, server)
        
        return {
            "episode_id": episode_id,
            "server": server,
            "type": type,
            "source_link": source_link,
            "videos": videos,
        }
    
    async def get_stream(self, anime_id: str, episode_num: int, type: str = "sub", server: str = "HD-1") -> Dict[str, Any]:
        """
        Convenience method to get stream directly from anime ID and episode number.
        Combines anime lookup, episode finding, and video extraction.
        """
        # Get episodes
        episodes_data = await self.get_episodes(anime_id)
        
        # Find the requested episode
        target_episode = None
        for ep in episodes_data["episodes"]:
            if int(ep["number"]) == episode_num:
                target_episode = ep
                break
        
        if not target_episode:
            return {
                "error": f"Episode {episode_num} not found",
                "total_episodes": episodes_data["total_episodes"],
            }
        
        # Get video
        video_data = await self.get_video(target_episode["id"], server, type)
        
        return {
            "anime_id": anime_id,
            "episode": episode_num,
            "episode_title": target_episode["title"],
            "server": server,
            "type": type,
            **video_data,
        }
    
    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
        # Also close extractor sessions
        await self.megacloud_extractor.close()
        await self.streamtape_extractor.close()
