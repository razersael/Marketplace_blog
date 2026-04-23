class TestPosts:
    def test_create_post_success(self, auth_api_client, test_category):
        """Успешное создание поста"""
        response = auth_api_client.post(
            "/posts",
            json={
                "title": "My First Post",
                "content": "Post content",
                "category_id": test_category["id"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My First Post"
        assert data["content"] == "Post content"

    def test_get_post_list_empty(self, auth_api_client):
        """Получение пустого списка постов (требуется авторизация)"""
        response = auth_api_client.get("/posts")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
