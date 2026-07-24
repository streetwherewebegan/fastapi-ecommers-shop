from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.orders import Order as OrderModel, OrderItem

router = APIRouter(
    prefix='/orders',
    tags=['orders'],
)

async def _load_order_with_items(db: AsyncSession, order_id: int) -> OrderModel | None:
    result = await db.scalars(
        select(OrderModel)
        .options(
            selectinload(OrderModel.items).selectinload(OrderItem.product)
        )
        .where(OrderModel.id == order_id)
    )
    return result.first()

