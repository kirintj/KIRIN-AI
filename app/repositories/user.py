from app.models.admin import User
from app.repositories.base import RepositoryBase
from app.schemas.users import UserCreate, UserUpdate


class UserRepository(RepositoryBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(model=User)

    async def get_by_email(self, email: str) -> User | None:
        return await self.model.filter(email=email).first()

    async def get_by_username(self, username: str) -> User | None:
        return await self.model.filter(username=username).first()


user_repository = UserRepository()
