from email.message import EmailMessage
from smtplib import SMTP  # ← меняем импорт

from src.marketplace_blog.config import settings
from src.marketplace_blog.tasks.celery_app import celery_app


@celery_app.task
def send_welcome_email(email: str, username: str):
    """Отправляет приветственное письмо"""
    message = EmailMessage()
    message["From"] = settings.email_from
    message["To"] = email
    message["Subject"] = "Добро пожаловать на Marketplace Blog!"

    message.set_content(
        f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h1>Привет, {username}!</h1>
            <p>Спасибо за регистрацию на <strong>Marketplace Blog</strong>!</p>
            <p>Теперь ты можешь:</p>
            <ul>
                <li>Создавать посты</li>
                <li>Добавлять категории</li>
                <li>Загружать изображения</li>
            </ul>
            <br>
            <p>С уважением,<br>Команда Marketplace Blog</p>
        </body>
    </html>
    """,
        subtype="html",
    )

    try:
        with SMTP(host=settings.smtp_host, port=settings.smtp_port) as server:
            server.send_message(message)

        print(f"Письмо отправлено на {email}")
        return {"status": "success", "email": email}

    except Exception as e:
        print(f"Ошибка отправки письма на {email}: {e}")
        return {"status": "error", "error": str(e)}
