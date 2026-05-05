from app.models.admin import Api
from app.repositories.base import RepositoryBase
from app.schemas.apis import ApiCreate, ApiUpdate


class ApiRepository(RepositoryBase[Api, ApiCreate, ApiUpdate]):
    def __init__(self):
        super().__init__(model=Api)


api_repository = ApiRepository()
