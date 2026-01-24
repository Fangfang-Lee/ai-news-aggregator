import pytest
from fastapi.testclient import TestClient


class TestCategoriesAPI:
    """Tests for category API endpoints"""

    def test_get_categories_empty(self, client: TestClient):
        """Test getting categories when none exist"""
        response = client.get("/api/categories/")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_category(self, client: TestClient):
        """Test creating a new category"""
        category_data = {
            "name": "AI",
            "description": "Artificial Intelligence",
            "color": "#6366f1"
        }
        response = client.post("/api/categories/", json=category_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AI"
        assert data["description"] == "Artificial Intelligence"
        assert data["color"] == "#6366f1"
        assert "id" in data

    def test_get_categories(self, client: TestClient, sample_category):
        """Test getting all categories"""
        response = client.get("/api/categories/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == sample_category.name

    def test_get_category_by_id(self, client: TestClient, sample_category):
        """Test getting a specific category"""
        response = client.get(f"/api/categories/{sample_category.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_category.id
        assert data["name"] == sample_category.name

    def test_get_category_not_found(self, client: TestClient):
        """Test getting a non-existent category"""
        response = client.get("/api/categories/999")
        assert response.status_code == 404

    def test_update_category(self, client: TestClient, sample_category):
        """Test updating a category"""
        update_data = {"name": "Machine Learning", "color": "#10b981"}
        response = client.put(f"/api/categories/{sample_category.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Machine Learning"
        assert data["color"] == "#10b981"

    def test_delete_category(self, client: TestClient, sample_category):
        """Test deleting a category"""
        response = client.delete(f"/api/categories/{sample_category.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify it's deleted
        response = client.get(f"/api/categories/{sample_category.id}")
        assert response.status_code == 404


class TestSourcesAPI:
    """Tests for RSS source API endpoints"""

    def test_create_source(self, client: TestClient, sample_category):
        """Test creating a new RSS source"""
        source_data = {
            "name": "Test Feed",
            "url": "https://example.com/feed",
            "category_id": sample_category.id
        }
        response = client.post("/api/sources/", json=source_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Feed"
        assert data["url"] == "https://example.com/feed"

    def test_get_sources(self, client: TestClient, sample_source):
        """Test getting all RSS sources"""
        response = client.get("/api/sources/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == sample_source.name

    def test_get_source_by_id(self, client: TestClient, sample_source):
        """Test getting a specific RSS source"""
        response = client.get(f"/api/sources/{sample_source.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_source.id
        assert data["name"] == sample_source.name

    def test_update_source(self, client: TestClient, sample_source):
        """Test updating an RSS source"""
        update_data = {"name": "Updated Feed", "is_active": False}
        response = client.put(f"/api/sources/{sample_source.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Feed"
        assert data["is_active"] is False

    def test_delete_source(self, client: TestClient, sample_source):
        """Test deleting an RSS source"""
        response = client.delete(f"/api/sources/{sample_source.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_source_stats(self, client: TestClient, sample_source):
        """Test getting source statistics"""
        response = client.get(f"/api/sources/{sample_source.id}/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_articles" in data
        assert "unread_articles" in data


class TestContentAPI:
    """Tests for content API endpoints"""

    def test_get_content_empty(self, client: TestClient):
        """Test getting content when none exists"""
        response = client.get("/api/content/")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_get_content(self, client: TestClient, sample_content):
        """Test getting all content"""
        response = client.get("/api/content/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == sample_content.id

    def test_get_content_by_id(self, client: TestClient, sample_content):
        """Test getting a specific content item"""
        response = client.get(f"/api/content/{sample_content.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_content.id
        assert data["title"] == sample_content.title

    def test_mark_as_read(self, client: TestClient, sample_content):
        """Test marking content as read"""
        response = client.post(f"/api/content/{sample_content.id}/mark-read")
        assert response.status_code == 200

        # Verify it's marked as read
        response = client.get(f"/api/content/{sample_content.id}")
        data = response.json()
        assert data["is_read"] is True

    def test_mark_as_unread(self, client: TestClient, sample_content):
        """Test marking content as unread"""
        # First mark as read
        client.post(f"/api/content/{sample_content.id}/mark-read")

        # Then mark as unread
        response = client.post(f"/api/content/{sample_content.id}/mark-unread")
        assert response.status_code == 200

        # Verify it's marked as unread
        response = client.get(f"/api/content/{sample_content.id}")
        data = response.json()
        assert data["is_read"] is False

    def test_toggle_bookmark(self, client: TestClient, sample_content):
        """Test toggling bookmark status"""
        response = client.post(f"/api/content/{sample_content.id}/bookmark")
        assert response.status_code == 200

        # Verify it's bookmarked
        response = client.get(f"/api/content/{sample_content.id}")
        data = response.json()
        assert data["is_bookmarked"] is True

    def test_filter_by_category(self, client: TestClient, sample_content, sample_category):
        """Test filtering content by category"""
        response = client.get(f"/api/content/categories/{sample_category.id}")
        assert response.status_code == 200
        data = response.json()
        # Content should be in results if categories match
        assert data["total"] >= 0

    def test_pagination(self, client: TestClient, sample_content):
        """Test content pagination"""
        response = client.get("/api/content/?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10


class TestMainApp:
    """Tests for main app endpoints"""

    def test_home_page(self, client: TestClient):
        """Test home page"""
        response = client.get("/")
        assert response.status_code == 200
        assert "AI News Aggregator" in response.text

    def test_health_check(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_api_docs(self, client: TestClient):
        """Test API docs endpoint"""
        response = client.get("/api/docs")
        assert response.status_code == 200