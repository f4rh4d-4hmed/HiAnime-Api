"""
Test HTTP error responses (404, 400, 422, 503) for HiAnime API
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app import app, hianime


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_hianime():
    """Mock the hianime instance for all tests"""
    with patch('app.hianime') as mock:
        yield mock


class TestErrorResponses:
    """Test suite for HTTP error responses"""
    
    # ==================== 404 NOT FOUND TESTS ====================
    
    def test_search_404_no_results(self, client, mock_hianime):
        """Test 404 when search returns no results"""
        mock_hianime.search = AsyncMock(return_value={"results": []})
        
        response = client.get("/search?q=nonexistentanime123456")
        
        assert response.status_code == 404
        assert "No results found" in response.json()["detail"]
    
    def test_popular_404_no_results(self, client, mock_hianime):
        """Test 404 when popular page is empty"""
        mock_hianime.get_popular = AsyncMock(return_value={"results": []})
        
        response = client.get("/popular?page=999")
        
        assert response.status_code == 404
        assert "No popular anime found" in response.json()["detail"]
    
    def test_latest_404_no_results(self, client, mock_hianime):
        """Test 404 when latest page is empty"""
        mock_hianime.get_latest = AsyncMock(return_value={"results": []})
        
        response = client.get("/latest?page=999")
        
        assert response.status_code == 404
        assert "No latest anime found" in response.json()["detail"]
    
    def test_info_404_anime_not_found(self, client, mock_hianime):
        """Test 404 when anime ID is not found"""
        mock_hianime.get_anime_details = AsyncMock(
            return_value={"error": "Anime not found"}
        )
        
        response = client.get("/info/invalid-anime-id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_episodes_404_not_found(self, client, mock_hianime):
        """Test 404 when episodes not found"""
        mock_hianime.get_episodes = AsyncMock(
            return_value={"error": "Anime not found"}
        )
        
        response = client.get("/episodes/invalid-anime-id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_episodes_404_no_episodes(self, client, mock_hianime):
        """Test 404 when anime has no episodes"""
        mock_hianime.get_episodes = AsyncMock(
            return_value={"episodes": []}
        )
        
        response = client.get("/episodes/some-anime-id")
        
        assert response.status_code == 404
        assert "No episodes found" in response.json()["detail"]
    
    def test_servers_404_episode_not_found(self, client, mock_hianime):
        """Test 404 when episode ID not found"""
        mock_hianime.get_episode_servers = AsyncMock(
            return_value={"error": "Episode not found"}
        )
        
        response = client.get("/servers/invalid-episode-id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_servers_404_no_servers(self, client, mock_hianime):
        """Test 404 when no servers available"""
        mock_hianime.get_episode_servers = AsyncMock(
            return_value={"servers": {}}
        )
        
        response = client.get("/servers/some-episode-id")
        
        assert response.status_code == 404
        assert "No servers found" in response.json()["detail"]
    
    def test_watch_404_server_not_found(self, client, mock_hianime):
        """Test 404 when server not found for episode"""
        mock_hianime.get_video = AsyncMock(
            return_value={"error": "Server not found"}
        )
        
        response = client.get("/watch/some-episode-id?server=HD-1&type=sub")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_watch_404_no_videos(self, client, mock_hianime):
        """Test 404 when no video streams available"""
        mock_hianime.get_video = AsyncMock(
            return_value={"videos": []}
        )
        
        response = client.get("/watch/some-episode-id?server=HD-1&type=sub")
        
        assert response.status_code == 404
        assert "No video streams found" in response.json()["detail"]
    
    # ==================== 400 BAD REQUEST TESTS ====================
    
    def test_episodes_400_invalid_anime_id(self, client, mock_hianime):
        """Test 400 for invalid anime ID format"""
        mock_hianime.get_episodes = AsyncMock(
            return_value={"error": "Invalid anime ID"}
        )
        
        response = client.get("/episodes/invalid$$$$")
        
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]
    
    def test_servers_400_invalid_episode_id(self, client, mock_hianime):
        """Test 400 for invalid episode ID format"""
        mock_hianime.get_episode_servers = AsyncMock(
            return_value={"error": "Invalid episode ID"}
        )
        
        response = client.get("/servers/invalid$$$$")
        
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]
    
    def test_watch_400_invalid_server(self, client, mock_hianime):
        """Test 400 for invalid server parameter"""
        response = client.get("/watch/some-episode-id?server=INVALID-SERVER&type=sub")
        
        assert response.status_code == 400
        assert "Invalid server" in response.json()["detail"]
        assert "HD-1" in response.json()["detail"]
    
    def test_watch_400_invalid_type(self, client, mock_hianime):
        """Test 400 for invalid type parameter"""
        response = client.get("/watch/some-episode-id?server=HD-1&type=invalid")
        
        assert response.status_code == 400
        assert "Invalid type" in response.json()["detail"]
        assert "sub" in response.json()["detail"]
    
    def test_watch_400_api_error(self, client, mock_hianime):
        """Test 400 for general API error from backend"""
        mock_hianime.get_video = AsyncMock(
            return_value={"error": "Bad request error"}
        )
        
        response = client.get("/watch/some-episode-id?server=HD-1&type=sub")
        
        assert response.status_code == 400
        assert "error" in response.json()["detail"].lower()
    
    # ==================== 422 UNPROCESSABLE ENTITY TESTS ====================
    
    def test_search_422_missing_query(self, client, mock_hianime):
        """Test 422 when required query parameter is missing"""
        response = client.get("/search")
        
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert isinstance(detail, list)
        assert any("q" in str(error).lower() for error in detail)
    
    def test_search_422_empty_query(self, client, mock_hianime):
        """Test 422 when query is empty (min_length=1 validation)"""
        response = client.get("/search?q=")
        
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert isinstance(detail, list)
    
    def test_search_422_invalid_page_type(self, client, mock_hianime):
        """Test 422 when page parameter is not an integer"""
        response = client.get("/search?q=test&page=abc")
        
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert isinstance(detail, list)
        assert any("page" in str(error).lower() for error in detail)
    
    def test_search_422_page_less_than_one(self, client, mock_hianime):
        """Test 422 when page parameter is less than 1 (ge=1 validation)"""
        response = client.get("/search?q=test&page=0")
        
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert isinstance(detail, list)
        assert any("page" in str(error).lower() for error in detail)
    
    def test_popular_422_invalid_page_type(self, client, mock_hianime):
        """Test 422 when page parameter is not an integer for popular"""
        response = client.get("/popular?page=invalid")
        
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert isinstance(detail, list)
    
    def test_popular_422_page_negative(self, client, mock_hianime):
        """Test 422 when page parameter is negative for popular"""
        response = client.get("/popular?page=-5")
        
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert isinstance(detail, list)
    
    def test_latest_422_invalid_page_type(self, client, mock_hianime):
        """Test 422 when page parameter is not an integer for latest"""
        response = client.get("/latest?page=xyz")
        
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert isinstance(detail, list)
    
    # ==================== 503 SERVICE UNAVAILABLE TESTS ====================
    
    def test_search_503_service_error(self, client, mock_hianime):
        """Test 503 when search service is unavailable"""
        mock_hianime.search = AsyncMock(
            return_value={"error": "Service temporarily unavailable"}
        )
        
        response = client.get("/search?q=test")
        
        assert response.status_code == 503
        assert len(response.json()["detail"]) > 0
    
    def test_popular_503_service_error(self, client, mock_hianime):
        """Test 503 when popular service is unavailable"""
        mock_hianime.get_popular = AsyncMock(
            return_value={"error": "Connection timeout"}
        )
        
        response = client.get("/popular?page=1")
        
        assert response.status_code == 503
        assert len(response.json()["detail"]) > 0
    
    def test_latest_503_service_error(self, client, mock_hianime):
        """Test 503 when latest service is unavailable"""
        mock_hianime.get_latest = AsyncMock(
            return_value={"error": "Network error occurred"}
        )
        
        response = client.get("/latest?page=1")
        
        assert response.status_code == 503
        assert len(response.json()["detail"]) > 0
    
    def test_info_503_service_error(self, client, mock_hianime):
        """Test 503 when anime details service is unavailable"""
        mock_hianime.get_anime_details = AsyncMock(
            return_value={"error": "Service error"}
        )
        
        response = client.get("/info/some-anime-id")
        
        assert response.status_code == 503
        assert len(response.json()["detail"]) > 0
    
    def test_episodes_503_service_error(self, client, mock_hianime):
        """Test 503 when episodes service is unavailable"""
        mock_hianime.get_episodes = AsyncMock(
            return_value={"error": "Upstream service unavailable"}
        )
        
        response = client.get("/episodes/some-anime-id")
        
        assert response.status_code == 503
        assert len(response.json()["detail"]) > 0
    
    def test_servers_503_service_error(self, client, mock_hianime):
        """Test 503 when servers service is unavailable"""
        mock_hianime.get_episode_servers = AsyncMock(
            return_value={"error": "Backend service down"}
        )
        
        response = client.get("/servers/some-episode-id")
        
        assert response.status_code == 503
        assert len(response.json()["detail"]) > 0
    
    # ==================== EDGE CASES ====================
    
    def test_multiple_validation_errors(self, client, mock_hianime):
        """Test 422 when multiple validation errors occur"""
        response = client.get("/search?page=invalid")
        
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert isinstance(detail, list)
        # Should have errors for both missing 'q' and invalid 'page'
        assert len(detail) >= 1
    
    def test_watch_all_invalid_servers(self, client, mock_hianime):
        """Test 400 for each invalid server option"""
        invalid_servers = ["INVALID", "HD-4", "hd-1", "StreamTap", ""]
        
        for server in invalid_servers:
            response = client.get(f"/watch/ep-123?server={server}&type=sub")
            assert response.status_code == 400
            assert "Invalid server" in response.json()["detail"]
    
    def test_watch_all_invalid_types(self, client, mock_hianime):
        """Test 400 for each invalid type option"""
        invalid_types = ["INVALID", "subbed", "dubbed", "english", ""]
        
        for typ in invalid_types:
            response = client.get(f"/watch/ep-123?server=HD-1&type={typ}")
            assert response.status_code == 400
            assert "Invalid type" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
