class TestCategories:
    def test_get_empty_categories(self, auth_api_client):
        """Получение пустого списка категорий (требуется авторизация)"""
        response = auth_api_client.get("/categories")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_create_category_success(self, auth_api_client):
        """Успешное создание категории"""
        response = auth_api_client.post(
            "/categories", json={"name": "Technology", "description": "Tech posts"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Technology"
        assert "id" in data
