class TestAuth:
    def test_register_success(self, api_client, clean_db):
        """Успешная регистрация"""
        response = api_client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"

    def test_login_success(self, api_client, test_user):
        """Успешный вход"""
        response = api_client.post(
            "/auth/login", json={"email": test_user["email"], "password": "testpass123"}
        )
        assert response.status_code == 200
        assert "access_token" in response.cookies

    def test_create_category_unauthorized(self, api_client):
        """Создание категории без авторизации возвращает 401"""
        response = api_client.post("/categories", json={"name": "Technology"})
        assert response.status_code == 401
