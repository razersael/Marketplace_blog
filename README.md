# Marketplace Blog API

API-сервис для блога на основе **FastAPI + SQLAlchemy (async)** с поддержкой:
- JWT-аутентификации (через HTTP-only cookie);
- управления пользователями;
- CRUD-операций с категориями и постами;
- полнотекстового поиска по заголовку и содержанию (PostgreSQL full-text search);
- загрузки изображений через MinIO (S3-совместимое хранилище);
- архивации удалённых постов;
- асинхронной отправки email через Celery + RabbitMQ

- ## 🚀 Установка и запуск
# Настрой переменные окружения
cp .env.example .env
# Укажи DATABASE_URL, S3_ACCESS_KEY, S3_SECRET_KEY и т.д.

# Запусти в Docker
docker-compose up --build

# Открой Swagger UI
http://localhost:8000/docs

com
📡 API Эндпоинты
Категория	Эндпоинт	Метод	Описание	Авторизация
Auth	/auth/register	POST	Регистрация пользователя	❌
/auth/login	POST	Вход (установка cookie)	❌
/auth/logout	POST	Выход (очистка cookie)	✅
Categories	/categories	GET	Получение списка категорий	✅
/categories	POST	Создание категории	✅
Posts	/posts	GET	Получение списка постов (с поиском и фильтрацией)	✅
/posts/{post_id}	GET	Получение поста по ID	✅
/posts	POST	Создание поста	✅
/posts/{post_id}	PUT	Обновление поста	✅
/posts/{post_id}	DELETE	Удаление поста (в архив)	✅
Images	/images/upload	POST	Загрузка изображения в MinIO	✅

📝 Примеры запросов и ответов
Регистрация пользователя
POST /auth/register

json
{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "strongpassword123"
}

Ответ (201 Created):

json
{
  "id": 1,
  "email": "user@example.com",
  "username": "john_doe",
  "created_at": "2026-01-23T10:00:00.000Z",
  "is_active": true
}

Вход (Login)
POST /auth/login

json
{
  "email": "user@example.com",
  "password": "strongpassword123"
}

Ответ (200 OK):

json
{
  "message": "Login successful",
  "user_id": 1
}

Токен access_token автоматически сохраняется в HTTP-only cookie.

Выход (Logout)
POST /auth/logout

Ответ (200 OK):

json
{
  "message": "Logout successful"
}

Cookie с токеном удаляется.

Создание категории
POST /categories

json
{
  "name": "Technology",
  "description": "Posts about technology and innovation"
}

Ответ (201 Created):

json
{
  "id": 1,
  "name": "Technology",
  "description": "Posts about technology and innovation",
  "created_at": "2026-01-23T10:00:00.000Z"
}

Получение списка категорий
GET /categories

Ответ (200 OK):

json
{
  "items": [
    {
      "id": 1,
      "name": "Technology",
      "description": "Posts about technology and innovation",
      "created_at": "2026-01-23T10:00:00.000Z"
    }
  ],
  "total": 1
}

Создание поста
POST /posts

json
{
  "title": "The Future of AI",
  "content": "Artificial intelligence is transforming our world...",
  "category_id": 1,
  "image_url": "https://minio.example.com/uploads/image.jpg"
}

Ответ (201 Created):

json
{
  "id": 1,
  "title": "The Future of AI",
  "content": "Artificial intelligence is transforming our world...",
  "image_url": "https://minio.example.com/uploads/image.jpg",
  "category_id": 1,
  "author_id": 1,
  "created_at": "2026-01-23T10:05:00.000Z",
  "updated_at": "2026-01-23T10:05:00.000Z"
}

Получение постов (с поиском и фильтрацией)
GET /posts?search=artificial&category_id=1&page=1&page_size=10

Ответ (200 OK):

json
{
  "items": [
    {
      "id": 1,
      "title": "The Future of AI",
      "content": "Artificial intelligence is transforming our world...",
      "image_url": null,
      "category_id": 1,
      "author_id": 1,
      "created_at": "2026-01-23T10:05:00.000Z",
      "updated_at": "2026-01-23T10:05:00.000Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}

Параметры поиска:

search - поиск по заголовку и содержанию (полнотекстовый)

category_id - фильтр по категории

page - номер страницы

page_size - элементов на странице (макс. 50)

Обновление поста
PUT /posts/1

json
{
  "title": "The Future of AI — 2026 Edition",
  "content": "Updated content with new insights..."
}

Ответ (200 OK):

json
{
  "id": 1,
  "title": "The Future of AI — 2026 Edition",
  "content": "Updated content with new insights...",
  "image_url": null,
  "category_id": 1,
  "author_id": 1,
  "created_at": "2026-01-23T10:05:00.000Z",
  "updated_at": "2026-01-23T10:10:00.000Z"
}

Удаление поста (перенос в архив)
DELETE /posts/1

Ответ (204 No Content) - тело ответа пустое

Пост удаляется из основной таблицы и сохраняется в deleted_posts с timestamp удаления.

Загрузка изображения
POST /images/upload

Request: multipart/form-data с полем file

Ответ (201 Created):

json
{
  "image_url": "http://localhost:9000/marketplace-blog/uploads/abc123_image.jpg"
}

Запуск тестов
# 1. Настройте тестовое окружение
cp .env.test.example .env.test

# 2. Убедитесь что тестовая БД запущена
docker ps | grep test_db

# 3. Запустите тесты
pytest -v


Tехнологии
🐍 FastAPI

🗄️ PostgreSQL + SQLAlchemy (async)

🔒 JWT Authentication (cookies)

☁️ S3 file storage

⚙️ Celery + RabbitMQ (отправка email)
