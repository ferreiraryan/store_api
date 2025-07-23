# Como precisa ficar:
from motor.motor_asyncio import AsyncIOMotorClient
from store.core.config import settings


class MongoClient:
    def __init__(self) -> None:
        self.client = AsyncIOMotorClient(
            settings.DATABASE_URL,
            uuidRepresentation="standard",  # <--- ADICIONE ISSO AQUI
        )

    def get(self):
        return self.client


db_client = MongoClient()
