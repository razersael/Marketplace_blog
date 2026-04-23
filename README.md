# FastAPI Marketplace Blog API

API-сервис для блога на основе **FastAPI + SQLAlchemy (async)** с поддержкой:
- JWT-аутентификации (через cookie);
- управления пользователями;
- CRUD-операций с категориями и постами;
- поиска по тексту (PostgreSQL full-text search);
- загрузки изображений через S3 presigned URLs;
- архивации удалённых постов.

---

## Установка и запуск

```
# Настрой переменные окружения
cp .env.example .env
# Укажи DATABASE_URL, S3_ACCESS_KEY, S3_SECRET_KEY и т.д.

# Запусти в Docker
docker-compose up --build

# Открой Swagger UI
http://localhost:8000/docs
```
| Категория      | Эндпоинт             | Метод  | Описание                               | Авторизация |
| -------------- | -------------------- | ------ | -------------------------------------- | ----------- |
| **Auth**       | `/auth/register`     | POST   | Регистрация пользователя               | ❌           |
|                | `/auth/login`        | POST   | Логин, установка access/refresh cookie | ❌           |
|                | `/auth/logout`       | POST   | Выход (очистка cookie)                 | ✅           |
| **Categories** | `/categories/create` | POST   | Создание категории                     | ✅           |
|                | `/categories/`       | GET    | Получение списка категорий             | ✅           |
| **Posts**      | `/posts/create`      | POST   | Создание поста                         | ✅           |
|                | `/posts/`            | GET    | Получение списка постов                | ✅           |
|                | `/posts/{post_id}`   | PUT    | Обновление поста                       | ✅           |
|                | `/posts/{post_id}`   | DELETE | Удаление поста (в архив)               | ✅           |
| **Images**     | `/image/presigned`   | GET    | Получить presigned URL для загрузки    | ✅           |

### Аутентификация

Авторизация реализована через JWT-токены в HTTP-only cookies:

access_token — действует короткое время;


Пример cookie-ответа:
```json
{
  "message": "authenticated"
}
```
### Примеры запросов и ответов

#### Регистрация пользователя

POST `/auth/register`
```json
{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "strongpassword123"
}
```
Ответ:
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "john_doe",
  "created_at": "2026-01-23T10:00:00.000Z",
  "is_active": true
}
```
#### Вход (login)

POST `/auth/login`
```json
{
  "email": "user@example.com",
  "password": "strongpassword123"
}
```
Ответ:
```json
{
  "message": "Login successful",
  "user_id": 1
}
```
`После успешного входа токены access_token и refresh_token сохраняются в cookies.`
#### Выход (logout)

POST `/auth/logout`
Ответ:
```json
{
  "message": "Logout successful"
}
```
#### Создание категории

POST `/categories/create`
```json
{
  "name": "Technology",
  "description": "Posts about technology and innovation"
}
```
Ответ:
```json
{
  "id": 1,
  "name": "Technology",
  "description": "Posts about technology and innovation",
  "created_at": "2026-01-23T10:00:00.000Z"
}
```
#### Получение списка категорий

GET `/categories/`
Ответ:
```json
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
```
#### Создание поста

POST `/posts/create`
```json
{
  "title": "The Future of AI",
  "content": "Artificial intelligence is transforming our world...",
  "category_id": 1,
  "image_url": "https://minio.example.com/uploads/image.jpg"
}
```
Ответ:
```json
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
```
#### Получение постов (с фильтрацией и поиском)

GET `/posts/?search=ai&category_id=1&page_number=1&page_size=10`
Ответ:
```json
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
```
#### Обновление поста

PUT `/posts/1`
```json
{
  "title": "The Future of AI — 2026 Edition",
  "content": "Updated content with new insights..."
}
```
Ответ:
```json
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
```
#### Удаление поста (перенос в архив)

DELETE `/posts/1`

Пост удаляется из основной таблицы и сохраняется в deleted_posts с timestamp удаления.

#### Загрузка изображения


POST /images/upload
Request: multipart/form-data с полем file

Ответ:
```json
{
  "image_url": "http://localhost:9000/marketplace-blog/uploads/abc123_image.jpg"
}
```

### Tехнологии

🐍 FastAPI

🗄️ PostgreSQL + SQLAlchemy (async)

🔒 JWT Authentication (cookies)

☁️ S3 file storage

⚙️ Celery + RabbitMQ (отправка email)
