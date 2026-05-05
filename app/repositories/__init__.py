from app.repositories.user import user_repository
from app.repositories.role import role_repository
from app.repositories.menu import menu_repository
from app.repositories.api import api_repository
from app.repositories.dept import dept_repository
from app.repositories.auditlog import auditlog_repository
from app.repositories.chat import chat_repository

__all__ = [
    "user_repository",
    "role_repository",
    "menu_repository",
    "api_repository",
    "dept_repository",
    "auditlog_repository",
    "chat_repository",
]
