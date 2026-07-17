from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.products import Product as ProductModel
from app.models.reviews import Review as ReviewModel


async def calculate_product_rating(db: AsyncSession, product_id: int):
    result = await db.execute(
        select(func.avg(ReviewModel.grade)).where(
            ReviewModel.product_id == product_id,
            ReviewModel.is_active == True
        )
    )

    avg_rating = result.scalar() or 0.0
    product = await db.get(ProductModel, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found or inactive'
        )

    product.rating = avg_rating
    await db.commit()
