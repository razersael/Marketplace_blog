from celery import Celery

from src.marketplace_blog.config import settings

celery_app = Celery(
    "marketplace_blog",
    broker=settings.rabbitmq_url,
    backend=None,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

celery_app.autodiscover_tasks(["src.marketplace_blog.tasks"])
