"""
StreamTape Extractor - Python port from Kotlin
Handles video extraction from StreamTape servers
"""

import aiohttp
import re
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup


class StreamTapeExtractor:
    """
    Extracts video URLs from StreamTape.
    Python port of the Kotlin StreamTapeExtractor.
    """
    
    BASE_URL = "https://streamtape.com/e/"
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def extract(self, url: str, quality: str = "Streamtape", subtitles: List[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Extract video URL from StreamTape.
        Mirrors videoFromUrl from Kotlin.
        """
        try:
            # Normalize URL
            base_url = "https://streamtape.com/e/"
            
            if not url.startswith(base_url):
                # Extract ID from URL: ["https", "", "<domain>", "<???>", "<id>", ...]
                parts = url.split("/")
                if len(parts) < 5:
                    return None
                video_id = parts[4]
                new_url = base_url + video_id
            else:
                new_url = url
            
            session = await self._get_session()
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }
            
            async with session.get(new_url, headers=headers) as response:
                html = await response.text()
            
            soup = BeautifulSoup(html, "html.parser")
            
            # Find script containing robotlink
            target_line = "document.getElementById('robotlink')"
            script_elem = None
            
            for script in soup.select("script"):
                if script.string and target_line in script.string:
                    script_elem = script
                    break
            
            if not script_elem or not script_elem.string:
                return None
            
            script_data = script_elem.string
            
            # Extract video URL parts
            # Pattern: document.getElementById('robotlink').innerHTML = '<part1>' + ('xcd<part2>')
            part1_match = re.search(r"innerHTML\s*=\s*'([^']+)'", script_data)
            part2_match = re.search(r"\+\s*\('xcd([^']+)'\)", script_data)
            
            if not part1_match:
                return None
            
            part1 = part1_match.group(1)
            part2 = part2_match.group(1) if part2_match else ""
            
            video_url = f"https:{part1}{part2}"
            
            return {
                "quality": quality,
                "url": video_url,
                "subtitles": subtitles or [],
            }
            
        except Exception as e:
            print(f"StreamTapeExtractor error: {e}")
            return None
    
    async def extract_list(self, url: str, quality: str = "Streamtape", subtitles: List[Dict] = None) -> List[Dict[str, Any]]:
        """
        Extract video URL and return as list.
        Mirrors videosFromUrl from Kotlin.
        """
        video = await self.extract(url, quality, subtitles)
        return [video] if video else []
    
    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
