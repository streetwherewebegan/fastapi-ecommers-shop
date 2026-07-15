from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reviews import Review as ReviewModel
from app.models.products import Product as ProductModel
from app.schemas import Review as ReviewSchema, ReviewCreate
from app.auth import get_current_user
from app.db_depends import get_async_db
from app.models.users import User as UserModel

router = APIRouter(
    prefix='/reviews',
    tags=['reviews'],
)

@router.get('/', response_model=list[ReviewSchema], status_code=status.HTTP_200_OK)
async def get_reviews(db: AsyncSession = Depends(get_async_db)):
    '''
    Возвращает список всех активных отзывов о товарах.
    '''
    result = await db.scalars(select(ReviewModel).where(ReviewModel.is_active == True))
    reviews = result.all()
    return reviews

@router.post('/reviews', response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review(
    review: ReviewCreate, 
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
    ):
    '''
    Создаёт новый отзыв для указанного товара.
    '''
    result = await db.scalars(select(ProductModel).where(
        ProductModel.id == review.product_id,
        ProductModel.is_active == True
    ))
    db_product = result.first()
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Product not found or inactive')
    
    if current_user.role != 'buyer':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='Only buyers can perform this action.')


    db_review = ReviewModel(**review.model_dump(), user_id=current_user.id)
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    return db_review