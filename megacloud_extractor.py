"""
MegaCloud Extractor - Python port from Kotlin
Handles video extraction from MegaCloud/RapidCloud servers (HD-1, HD-2, HD-3)
"""

import aiohttp
import re
import json
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode, quote


class MegaCloudExtractor:
    """
    Extracts video URLs from MegaCloud servers.
    Python port of the Kotlin MegaCloudExtractor.
    """
    
    SOURCES_URL = "/embed-2/v3/e-1/getSources?id="
    SOURCES_SPLITTER = "/e-1/"
    
    # API for decryption (you need to host this or use the external one)
    MEGACLOUD_API = "https://megacloud-api.vercel.app/api/decrypt"
    
    def __init__(self, megacloud_api: str = None):
        self.megacloud_api = megacloud_api or self.MEGACLOUD_API
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def extract(self, url: str, type: str, name: str) -> List[Dict[str, Any]]:
        """
        Extract video URLs from MegaCloud embed URL.
        Mirrors getVideosFromUrl from Kotlin.
        """
        try:
            video_data = await self._get_video_dto(url)
            
            if not video_data:
                return []
            
            videos = []
            
            for video in video_data:
                m3u8_url = video.get("m3u8", "")
                tracks = video.get("tracks", [])
                
                # Filter subtitle tracks
                subtitles = [
                    {"url": t["file"], "label": t.get("label", "Unknown")}
                    for t in tracks
                    if t.get("kind") == "captions"
                ]
                
                # Extract quality variants from HLS playlist
                qualities = await self._extract_qualities(m3u8_url, url)
                
                for quality in qualities:
                    videos.append({
                        "quality": f"{name} - {quality['resolution']} - {type}",
                        "url": quality["url"],
                        "subtitles": subtitles,
                        "referer": f"https://{self._get_host(url)}/",
                    })
                
                # If no specific qualities found, add the main m3u8
                if not qualities and m3u8_url:
                    videos.append({
                        "quality": f"{name} - Auto - {type}",
                        "url": m3u8_url,
                        "subtitles": subtitles,
                        "referer": f"https://{self._get_host(url)}/",
                    })
            
            return videos
            
        except Exception as e:
            print(f"MegaCloudExtractor error: {e}")
            return []
    
    async def _get_video_dto(self, url: str) -> List[Dict[str, Any]]:
        """
        Get video data from MegaCloud.
        Mirrors getVideoDto from Kotlin.
        """
        # Extract ID from URL
        if self.SOURCES_SPLITTER not in url:
            raise Exception("Failed to extract ID from URL")
        
        id_part = url.split(self.SOURCES_SPLITTER)[-1]
        video_id = id_part.split("?")[0]
        
        if not video_id:
            raise Exception("Failed to extract ID from URL")
        
        host = self._get_host(url)
        if not host:
            raise Exception(f"MegaCloud host is invalid: {url}")
        
        megacloud_server_url = f"https://{host}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{megacloud_server_url}/",
        }
        
        session = await self._get_session()
        
        # Fetch the embed page to get the nonce
        async with session.get(url, headers=headers) as response:
            response_text = await response.text()
        
        # Extract nonce - try 48-char match first, then 3x16-char match
        nonce = None
        
        # Try 48-character nonce
        match1 = re.search(r'\b[a-zA-Z0-9]{48}\b', response_text)
        if match1:
            nonce = match1.group(0)
        else:
            # Try 3x16-character nonce
            match2 = re.search(r'\b([a-zA-Z0-9]{16})\b.*?\b([a-zA-Z0-9]{16})\b.*?\b([a-zA-Z0-9]{16})\b', response_text, re.DOTALL)
            if match2:
                nonce = match2.group(1) + match2.group(2) + match2.group(3)
        
        if not nonce:
            raise Exception("Failed to extract nonce from response")
        
        # Fetch sources with nonce
        sources_url = f"{megacloud_server_url}{self.SOURCES_URL}{video_id}&_k={nonce}"
        
        async with session.get(sources_url, headers=headers) as response:
            src_res = await response.text()
        
        try:
            data = json.loads(src_res)
        except json.JSONDecodeError:
            raise Exception("Failed to parse sources response")
        
        sources = data.get("sources", [])
        encrypted = data.get("encrypted", True)
        tracks = data.get("tracks", [])
        
        # Get decryption key if needed
        key = None
        
        result = []
        
        for source in sources:
            encoded = source.get("file", "")
            
            if not encrypted or ".m3u8" in encoded:
                m3u8 = encoded
            else:
                # Decrypt using API
                if key is None:
                    key = await self._request_new_key()
                
                decrypt_url = (
                    f"{self.megacloud_api}"
                    f"?encrypted_data={quote(encoded)}"
                    f"&nonce={quote(nonce)}"
                    f"&secret={quote(key)}"
                )
                
                async with session.get(decrypt_url) as response:
                    decrypted_response = await response.text()
                
                # Extract file URL from response
                file_match = re.search(r'"file":"(.*?)"', decrypted_response)
                if file_match:
                    m3u8 = file_match.group(1)
                else:
                    raise Exception("Video URL not found in decrypted response")
            
            result.append({
                "m3u8": m3u8,
                "tracks": tracks,
            })
        
        return result
    
    async def _request_new_key(self) -> str:
        """
        Fetch the current MegaCloud decryption key.
        Mirrors requestNewKey from Kotlin.
        """
        session = await self._get_session()
        
        keys_url = "https://raw.githubusercontent.com/yogesh-hacker/MegacloudKeys/refs/heads/main/keys.json"
        
        async with session.get(keys_url) as response:
            if response.status != 200:
                raise Exception("Failed to fetch keys.json")
            
            keys_json = await response.text()
            
            if not keys_json:
                raise Exception("keys.json is empty")
            
            keys = json.loads(keys_json)
            key = keys.get("mega")
            
            if not key:
                raise Exception("Mega key not found in keys.json")
            
            return key
    
    async def _extract_qualities(self, m3u8_url: str, referer_url: str) -> List[Dict[str, str]]:
        """
        Extract different quality variants from HLS master playlist.
        """
        if not m3u8_url:
            return []
        
        session = await self._get_session()
        host = self._get_host(referer_url)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": f"https://{host}/",
        }
        
        try:
            async with session.get(m3u8_url, headers=headers) as response:
                playlist = await response.text()
            
            qualities = []
            base_url = m3u8_url.rsplit("/", 1)[0]
            
            lines = playlist.strip().split("\n")
            for i, line in enumerate(lines):
                if line.startswith("#EXT-X-STREAM-INF"):
                    # Extract resolution
                    res_match = re.search(r'RESOLUTION=(\d+x\d+)', line)
                    resolution = res_match.group(1) if res_match else "Unknown"
                    
                    # Get the URL on the next line
                    if i + 1 < len(lines):
                        url_line = lines[i + 1].strip()
                        if url_line and not url_line.startswith("#"):
                            # Handle relative URLs
                            if url_line.startswith("http"):
                                quality_url = url_line
                            else:
                                quality_url = f"{base_url}/{url_line}"
                            
                            qualities.append({
                                "resolution": resolution,
                                "url": quality_url,
                            })
            
            return qualities
            
        except Exception as e:
            print(f"Error extracting qualities: {e}")
            return []
    
    def _get_host(self, url: str) -> Optional[str]:
        """Extract host from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return None
    
    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
