from datetime import datetime, timezone
from typing import List
from uuid import UUID

import pymongo
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from store.core.exceptions import DatabaseError, NotFoundException
from store.db.mongo import db_client
from store.models.product import ProductModel
from store.schemas.product import ProductIn, ProductOut, ProductUpdate, ProductUpdateOut


class ProductUsecase:
    def __init__(self) -> None:
        self.client: AsyncIOMotorClient = db_client.get()
        self.database: AsyncIOMotorDatabase = self.client.get_database()
        self.collection = self.database.get_collection("products")

    async def create(self, body: ProductIn) -> ProductOut:
        product_model = ProductModel(**body.model_dump())
        try:
            await self.collection.insert_one(product_model.model_dump())
        except PyMongoError as e:
            raise DatabaseError(message=f"Error inserting product in database: {e}")

        return ProductOut(**product_model.model_dump())

    async def get(self, id: UUID) -> ProductOut:
        result = await self.collection.find_one({"id": id})

        if not result:
            raise NotFoundException(message=f"Product not found with filter: {id}")

        return ProductOut(**result)

    async def query(
        self, min_price: float = None, max_price: float = None
    ) -> List[ProductOut]:
        filter_query = {}
        price_filter = {}

        if min_price is not None:
            price_filter["$gt"] = min_price

        if max_price is not None:
            price_filter["$lt"] = max_price

        if price_filter:
            filter_query["price"] = price_filter

        products = []
        async for product in self.collection.find(filter_query):
            products.append(ProductOut(**product))

        return products

    async def update(self, id: UUID, body: ProductUpdate) -> ProductUpdateOut:
        await self.get(id=id)

        update_data = body.model_dump(exclude_unset=True)

        if "updated_at" not in update_data:
            update_data["updated_at"] = datetime.now(timezone.utc)

        result = await self.collection.find_one_and_update(
            filter={"id": id},
            update={"$set": update_data},
            return_document=pymongo.ReturnDocument.AFTER,
        )

        return ProductUpdateOut(**result)

    async def delete(self, id: UUID) -> bool:
        product = await self.collection.find_one({"id": id})
        if not product:
            raise NotFoundException(message=f"Product not found with filter: {id}")

        result = await self.collection.delete_one({"id": id})

        return True if result.deleted_count > 0 else False


product_usecase = ProductUsecase()
