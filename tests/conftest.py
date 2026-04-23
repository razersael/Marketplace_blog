# tests/conftest.py
import os
import subprocess
import sys
import time

import psycopg2
import pytest
import requests
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

env_test_path = os.path.join(os.path.dirname(__file__), "..", ".env.test")

if not os.path.exists(env_test_path):
    raise FileNotFoundError(
        f"❌ Файл {env_test_path} не найден!\nСоздайте его на основе .env.test.example"
    )

load_dotenv(env_test_path)
print(f"✅ Загружен конфиг из {env_test_path}")


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8001")
TEST_SERVER_PORT = os.environ.get("TEST_SERVER_PORT", "8001")


class ApiClient:
    """Обёртка над requests.Session для работы с API"""

    def __init__(self):
        self.session = requests.Session()

    def request(self, method, url, **kwargs):
        full_url = f"{API_BASE_URL}{url}"
        return self.session.request(method, full_url, **kwargs)

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def put(self, url, **kwargs):
        return self.request("PUT", url, **kwargs)

    def patch(self, url, **kwargs):
        return self.request("PATCH", url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)


def get_db_connection():
    """Возвращает соединение с тестовой БД"""
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    )


def wait_for_db():
    """Ждёт пока БД станет доступной"""
    timeout = 10
    start = time.time()
    while time.time() - start < timeout:
        try:
            conn = get_db_connection()
            conn.close()
            return True
        except Exception:
            time.sleep(0.5)
    return False


def create_tables():
    """Создаёт таблицы в тестовой БД"""
    from sqlalchemy import create_engine, text

    sync_url = f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['POSTGRES_DB']}"
    engine = create_engine(sync_url, echo=False)

    from src.marketplace_blog.models.base import Base

    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
            conn.commit()
        except Exception as e:
            print(f"⚠️ Could not create extensions: {e}")

    Base.metadata.create_all(bind=engine)
    engine.dispose()
    print("✅ Таблицы созданы")


def create_search_trigger():
    """Создаёт триггер для обновления search_vector"""
    try:
        conn = get_db_connection()
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute("""
                    CREATE
                    OR REPLACE FUNCTION update_post_search_vector()
            RETURNS TRIGGER AS $$
                    BEGIN
                NEW.search_vector
                    := to_tsvector('russian',
                    COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.content, '')
                );
                    RETURN NEW;
                    END;
            $$
                    LANGUAGE plpgsql;
                    """)

        cur.execute("""
            DROP TRIGGER IF EXISTS trigger_update_search_vector ON posts;
            CREATE TRIGGER trigger_update_search_vector
                BEFORE INSERT OR UPDATE ON posts
                FOR EACH ROW
                EXECUTE FUNCTION update_post_search_vector();
        """)

        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Could not create trigger: {e}")


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Подготовка БД: создание таблиц и триггеров"""
    if not wait_for_db():
        raise RuntimeError("❌ База данных не доступна")

    create_tables()

    create_search_trigger()

    yield


@pytest.fixture(autouse=True)
def clean_db():
    """Очищает таблицы после каждого теста"""
    conn = get_db_connection()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                  AND tablename NOT LIKE 'alembic%'
                """)
    tables = [row[0] for row in cur.fetchall()]

    if tables:
        order = ["deleted_posts", "posts", "categories", "users"]
        for table in order:
            if table in tables:
                cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")

    cur.close()
    conn.close()


@pytest.fixture(scope="session", autouse=True)
def start_server():
    """Запускает тестовый сервер с нужными переменными окружения"""
    try:
        r = requests.get(f"{API_BASE_URL}/docs", timeout=1)
        if r.status_code == 200:
            print("✅ Сервер уже запущен")
            yield
            return
    except requests.ConnectionError:
        pass

    env = os.environ.copy()

    env["TESTING"] = "true"
    env["DATABASE_URL"] = (
        f"postgresql+asyncpg://{env['POSTGRES_USER']}:{env['POSTGRES_PASSWORD']}@{env['DB_HOST']}:{env['DB_PORT']}/{env['POSTGRES_DB']}"
    )

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.marketplace_blog.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        TEST_SERVER_PORT,
        "--log-level",
        "warning",
    ]

    proc = subprocess.Popen(
        cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    timeout = 15
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{API_BASE_URL}/docs", timeout=1)
            if r.status_code == 200:
                print("✅ Сервер запущен")
                break
        except requests.ConnectionError:
            time.sleep(0.5)
    else:
        proc.terminate()
        raise RuntimeError("❌ Сервер не запустился")

    yield proc

    print("🛑 Останавливаем сервер...")
    proc.terminate()
    proc.wait()


# ============ Фикстуры для тестов ============
@pytest.fixture
def api_client():
    """Базовый API клиент"""
    return ApiClient()


@pytest.fixture
def test_user(api_client, clean_db):
    """Создаёт тестового пользователя"""
    import random

    unique = random.randint(1000, 99999)
    email = f"test_{unique}@example.com"
    username = f"testuser_{unique}"

    print(f"Creating user: {email}")

    response = api_client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": "testpass123"},
    )

    if response.status_code != 201:
        print(f"❌Failed to create user: Status {response.status_code}")
        print(f"Response: {response.text}")

        unique = random.randint(100000, 999999)
        email = f"test_{unique}@example.com"
        username = f"testuser_{unique}"

        response = api_client.post(
            "/auth/register",
            json={"email": email, "username": username, "password": "testpass123"},
        )

    assert response.status_code == 201, f"Failed to create user: {response.text}"
    return response.json()


@pytest.fixture
def auth_api_client(api_client, test_user):
    """Авторизованный API клиент"""
    response = api_client.post(
        "/auth/login", json={"email": test_user["email"], "password": "testpass123"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"

    api_client.session.cookies.update(response.cookies)
    return api_client


@pytest.fixture
def test_category(auth_api_client):
    """Создаёт тестовую категорию"""
    import random

    response = auth_api_client.post(
        "/categories",
        json={
            "name": f"Test Category {random.randint(1000, 9999)}",
            "description": "Test category description",
        },
    )
    assert response.status_code == 201, f"Failed to create category: {response.text}"
    return response.json()


@pytest.fixture
def test_post(auth_api_client, test_category):
    """Создаёт тестовый пост"""
    import random

    response = auth_api_client.post(
        "/posts",
        json={
            "title": f"Test Post {random.randint(1000, 9999)}",
            "content": "Test content for post",
            "category_id": test_category["id"],
        },
    )
    assert response.status_code == 201, f"Failed to create post: {response.text}"
    return response.json()
