from fastapi_mail import ConnectionConfig
import os

ORIGINS = [

    'http://localhost:3000', 
    'http://localhost:5173'
    ]
REFERRERS = [
    'http://localhost',
    'http://localhost:3000/',
    'http://localhost:5173/'
    ]

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("mail_username"),
    MAIL_PASSWORD=os.getenv("mail_password"),
    MAIL_PORT=465,
    MAIL_SERVER=os.getenv("mail_server"),
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    MAIL_FROM=os.getenv("mail_from")
)