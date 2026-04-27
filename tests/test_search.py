import time


class TestSearch:
    """Тесты поиска постов"""

    def test_search_by_title(self, auth_api_client, test_category, clean_db):
        """Поиск по заголовку"""
        unique_title = f"UniquePythonPost_{int(time.time())}"
        create_response = auth_api_client.post(
            "/posts",
            json={
                "title": unique_title,
                "content": "Test content for unique post",
                "category_id": test_category["id"],
            },
        )
        assert (
            create_response.status_code == 201
        ), f"Failed to create post: {create_response.text}"
        created_post = create_response.json()

        time.sleep(0.5)

        search_response = auth_api_client.get(f"/posts?search={unique_title}")
        assert (
            search_response.status_code == 200
        ), f"Search failed: {search_response.text}"
        data = search_response.json()
        assert data["total"] > 0, f"No posts found for search term '{unique_title}'"
        found = any(post["id"] == created_post["id"] for post in data["items"])
        assert found, f"Created post {created_post['id']} not found in search results"

    def test_search_by_content(self, auth_api_client, test_category, clean_db):
        """Поиск по содержанию"""
        unique_content = f"UniqueDatabaseContent_{int(time.time())}"
        create_response = auth_api_client.post(
            "/posts",
            json={
                "title": "Test Post",
                "content": unique_content,
                "category_id": test_category["id"],
            },
        )
        assert (
            create_response.status_code == 201
        ), f"Failed to create post: {create_response.text}"
        created_post = create_response.json()

        time.sleep(0.5)

        search_response = auth_api_client.get(f"/posts?search={unique_content}")
        assert search_response.status_code == 200
        data = search_response.json()
        assert (
            data["total"] > 0
        ), f"No posts found for search content '{unique_content}'"
        found = any(post["id"] == created_post["id"] for post in data["items"])
        assert found, f"Created post {created_post['id']} not found in search results"

    def test_search_pagination(self, auth_api_client, test_category, clean_db):
        """Поиск с пагинацией"""
        common_word = f"PaginationTest_{int(time.time())}"
        created_posts = []

        for i in range(15):
            response = auth_api_client.post(
                "/posts",
                json={
                    "title": f"{common_word} Post {i}",
                    "content": f"Content for pagination test post {i}",
                    "category_id": test_category["id"],
                },
            )
            assert response.status_code == 201, f"Failed to create post {i}"
            created_posts.append(response.json())

        time.sleep(0.5)

        assert len(created_posts) == 15, f"Only {len(created_posts)} posts created"

        response = auth_api_client.get(
            f"/posts?search={common_word}&page=1&page_size=5"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["items"]) <= 5
        assert data["total"] == 15, f"Expected 15 posts, got {data['total']}"

        response_page2 = auth_api_client.get(
            f"/posts?search={common_word}&page=2&page_size=5"
        )
        assert response_page2.status_code == 200
        data_page2 = response_page2.json()
        assert data_page2["page"] == 2

    def test_search_partial_word(self, auth_api_client, test_category, clean_db):
        """Поиск по части слова"""
        full_word = f"FullTextSearch_{int(time.time())}"
        create_response = auth_api_client.post(
            "/posts",
            json={
                "title": full_word,
                "content": "Content for full-text search test",
                "category_id": test_category["id"],
            },
        )
        assert create_response.status_code == 201

        time.sleep(0.5)

        response_full = auth_api_client.get(f"/posts?search={full_word}")
        assert response_full.status_code == 200

        partial_word = full_word[:10]
        response_partial = auth_api_client.get(f"/posts?search={partial_word}")
        assert response_partial.status_code == 200

    def test_search_with_multiple_words(self, auth_api_client, test_category, clean_db):
        """Поиск по нескольким словам"""
        unique_phrase = f"multiple words test {int(time.time())}"
        create_response = auth_api_client.post(
            "/posts",
            json={
                "title": unique_phrase,
                "content": "Content with multiple words for testing search functionality",
                "category_id": test_category["id"],
            },
        )
        assert create_response.status_code == 201

        time.sleep(0.5)

        response = auth_api_client.get(f"/posts?search={unique_phrase}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0, f"No posts found for phrase '{unique_phrase}'"

    def test_search_with_pagination_and_category(
        self, auth_api_client, test_category, clean_db
    ):
        """Комплексный поиск: пагинация + категория + поиск"""
        cat2_response = auth_api_client.post(
            "/categories",
            json={
                "name": f"AnotherCat_{int(time.time())}",
                "description": "Another category",
            },
        )
        assert cat2_response.status_code == 201
        second_category = cat2_response.json()

        common_word = f"ComplexSearch_{int(time.time())}"
        posts_in_cat1 = []
        posts_in_cat2 = []

        for i in range(10):
            category_id = test_category["id"] if i < 5 else second_category["id"]
            response = auth_api_client.post(
                "/posts",
                json={
                    "title": f"{common_word} post {i}",
                    "content": f"Content for complex search post {i}",
                    "category_id": category_id,
                },
            )
            assert response.status_code == 201
            if i < 5:
                posts_in_cat1.append(response.json())
            else:
                posts_in_cat2.append(response.json())

        time.sleep(0.5)

        response = auth_api_client.get(
            f"/posts?search={common_word}&category_id={test_category['id']}&page=1&page_size=3"
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

        for post in data["items"]:
            assert post["category_id"] == test_category["id"]

        assert data["total"] == len(
            posts_in_cat1
        ), f"Expected {len(posts_in_cat1)} posts, got {data['total']}"
        assert len(data["items"]) == min(3, len(posts_in_cat1))
        assert data["page_size"] == 3
