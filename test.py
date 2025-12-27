"""
Quick test for HiAnime API
"""
import asyncio
from hianime import HiAnime


async def test():
    h = HiAnime()
    try:
        # Search
        print("Searching 'Boruto'...")
        results = await h.search("Boruto")
        anime = results["results"][0]
        print(f"Found: {anime['title']} ({anime['id']})")
        
        # Episodes
        print("\nGetting episodes...")
        eps = await h.get_episodes(anime["id"])
        print(f"Total: {eps['total_episodes']} episodes")
        
        # Get first episode video
        ep = eps["episodes"][0]
        print(f"\nGetting video for: {ep['title']}")
        
        video = await h.get_video(ep["id"], "HD-1", "sub")
        
        if video.get("videos"):
            v = video["videos"][0]
            print(f"\n✓ Stream URL: {v['url'][:60]}...")
            print(f"✓ Quality: {v['quality']}")
            print(f"✓ Referer: {v['referer']}")
            print(f"✓ Subtitles: {len(v.get('subtitles', []))} tracks")
        else:
            print("No video found")
            
    finally:
        await h.close()


if __name__ == "__main__":
    asyncio.run(test())
