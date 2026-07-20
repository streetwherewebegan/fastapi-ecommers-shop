from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import get_current_seller
from app.db_depends import get_async_db
from app.models.categories import Category as CategoryModel
from app.models.products import Product as ProductModel
from app.models.reviews import Review as ReviewModel
from app.models.users import User as UserModel
from app.schemas import (
    Product as ProductSchema, 
    Review as ReviewSchema,
    ProductCreate, 
    ProductList,
)


router = APIRouter(
    prefix='/products',
    tags=['products']
)

@router.get('/', response_model=ProductList)
async def get_all_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: int | None = Query(None, description='ID категории для фильтрации'),
    min_price: int | None = Query(None, ge=0, description='Минимальная цена товара'),
    max_price: int | None = Query(None, ge=0,description='Максимальная цена товара'),
    in_stock: bool | None = Query(
        None, description='true — только товары в наличии, false — только без остатка'),
    seller_id: int | None = Query(None, description='ID продавца для фильтрации'),
    sort_by: Literal['id', 'created_at'] = Query(
        'id', description='Cортировка даты'),
    order: Literal['asc', 'desc'] = Query('desc', description='Направление сортировки'),
    db: AsyncSession = Depends(get_async_db)
):
    '''
    Возвращает список всех активных товаров с поддержкой фильтров.
    '''
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='min_price не может быть больше max_price'
        )
    
    filters = [ProductModel.is_active == True]

    if category_id is not None:
        filters.append(ProductModel.category_id == category_id)
    if min_price is not None:
        filters.append(ProductModel.price >= min_price)
    if max_price is not None:
        filters.append(ProductModel.price <= max_price)
    if in_stock is not None:
        filters.append(ProductModel.stock > 0 if in_stock else ProductModel.stock == 0)
    if seller_id is not None:
        filters.append(ProductModel.seller_id == seller_id)

    total_stmt = select(func.count()).select_from(ProductModel).where(*filters)
    total = await db.scalar(total_stmt) or 0

    sorting_parameters = (ProductModel.id if sort_by == 'id' else ProductModel.created_at)

    if order == 'desc':
        sorting_parameters = sorting_parameters.desc()

    products_stmt = (
        select(ProductModel)
        .where(*filters)
        .order_by(sorting_parameters)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await db.scalars(products_stmt)).all()

    return {
        'items': items,
        'total': total,
        'page': page,
        'page_size': page_size
    }


@router.post('/', response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller)
    ):
    '''
    Создаёт новый товар, привязанный к текущему продавцу
    '''
    category_result = await db.scalars(select(CategoryModel).where(
        CategoryModel.id == product.category_id,
        CategoryModel.is_active == True
    ))

    if not category_result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Category not found or inactive'
        )

    db_product = ProductModel(**product.model_dump(), seller_id = current_user.id)

    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product

@router.get('/category/{category_id}', response_model=list[ProductSchema])
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    '''
    Возвращает список активных товаров в указанной категории по её ID
    '''
    category_result = await db.scalars(select(CategoryModel).where(
        CategoryModel.id == category_id,
        CategoryModel.is_active == True
    ))
    db_category = category_result.first()

    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Category not found or inactive'
        )

    products_result = await db.scalars(select(ProductModel).where(
        ProductModel.category_id == category_id,
        ProductModel.is_active == True
    ))
    db_products = products_result.all()
    return db_products

@router.get('/{product_id}', response_model=ProductSchema)
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    '''
    Возвращает детальную информацию о товаре по его ID
    '''
    product_result = await db.scalars(select(ProductModel).where(
        ProductModel.id == product_id,
        ProductModel.is_active == True
    ))
    db_product = product_result.first()

    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found or inactive'
        )

    category_result = await db.scalars(select(CategoryModel).where(
        CategoryModel.id == db_product.category_id,
        CategoryModel.is_active == True
    ))
    category = category_result.first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Category not found or inactive'
        )
    return db_product

@router.get('/{product_id}/reviews/', response_model=list[ReviewSchema])
async def get_product_reviews(product_id: int, db: AsyncSession = Depends(get_async_db)):
    '''
    Возвращает список активных отзывов для указанного товара
    '''
    product_result = await db.scalars(select(ProductModel).where(
        ProductModel.id == product_id,
        ProductModel.is_active == True
    ))
    db_product = product_result.first()

    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found or inactive'
        )

    reviews_result = await db.scalars(select(ReviewModel).where(
        ReviewModel.product_id == product_id,
        ReviewModel.is_active == True
    ))
    db_reviews = reviews_result.all()
    return db_reviews

@router.put('/{product_id}', response_model=ProductSchema)
async def update_product(
    product_id: int,
    product: ProductCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller)):
    '''
    Обновляет товар по его ID
    '''
    result = await db.scalars(select(ProductModel).where(
        ProductModel.id == product_id,
        ProductModel.is_active == True
    ))
    db_product = result.first()

    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found or inactive'
        )

    if db_product.seller_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You can only update your own products'
        )

    category_result = await db.scalars(select(CategoryModel).where(
        CategoryModel.id == product.category_id,
        CategoryModel.is_active == True
    ))

    if not category_result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Category not found or inactive'
        )

    updated_product = product.model_dump()

    await db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(**updated_product)
    )
    await db.commit()
    await db.refresh(db_product)
    return db_product

@router.delete('/{product_id}', status_code=status.HTTP_200_OK)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller)):
    '''
    Удаляет товар по его ID (логическое удаление)
    '''
    result = await db.scalars(select(ProductModel).where(
        ProductModel.id == product_id,
        ProductModel.is_active == True
    ))
    db_product = result.first()

    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found or inactive'
        )

    if db_product.seller_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You can only delete your own products'
        )

    await db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(is_active=False)
    )
    await db.commit()
    return db_product