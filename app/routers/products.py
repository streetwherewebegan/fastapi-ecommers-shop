from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
#from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.products import Product as ProductModel
from app.models.categories import Category as CategoryModel
from app.schemas import Product as ProductSchema, ProductCreate
from app.db_depends import get_async_db

router = APIRouter(
    prefix='/products',
    tags=['products']
)

@router.get('/', response_model=list[ProductSchema])
async def get_all_products(db: AsyncSession = Depends(get_async_db)):
    '''
    Возвращает список всех активных товаров.
    '''
    stmt =  select(ProductModel).join(CategoryModel).where(ProductModel.is_active == True,
                                                       CategoryModel.is_active == True,
                                                       ProductModel.stock > 0)
    products = (await db.scalars(stmt)).all()    
    return products

@router.post('/', response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_async_db)):
    '''
    Создаёт новый товар.
    '''
    stmt = select(CategoryModel).where(CategoryModel.id == product.category_id,
                                    CategoryModel.is_active == True)
    category = (await db.scalars(stmt)).first()

    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Category not found or inactive')

    db_product = ProductModel(**product.model_dump(exclude_unset=True))
    db.add(db_product)
    await db.commit()
    return db_product

@router.get('/category/{category_id}', response_model=list[ProductSchema])
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    '''
    Возвращает список активных товаров в указанной категории по её ID.
    '''
    category_stmt = select(CategoryModel).where(CategoryModel.id == category_id,
                                    CategoryModel.is_active == True)
    category = (await db.scalars(category_stmt)).first()

    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Category not found or inactive')

    product_stmt = select(ProductModel).where(ProductModel.category_id == category_id,
                                   ProductModel.is_active == True)
    products = (await db.scalars(product_stmt)).all()
    return products

@router.get('/{product_id}', response_model=ProductSchema)
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    '''
    Возвращает детальную информацию о товаре по его ID.
    '''
    product_stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    product = (await db.scalars(product_stmt)).first()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product not found or inactive')

    category_stmt = select(CategoryModel).where(CategoryModel.id == product.category_id,
                                    CategoryModel.is_active == True)
    category = (await db.scalars(category_stmt)).first()

    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Category not found or inactive')

    return product

@router.put('/{product_id}', response_model=ProductSchema)
async def update_product(product_id: int, product: ProductCreate, db: AsyncSession = Depends(get_async_db)):
    '''
    Обновляет товар по его ID.
    '''
    product_stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    db_product = (await db.scalars(product_stmt)).first()

    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product not found or inactive')
    
    category_stmt = select(CategoryModel).where(CategoryModel.id == product.category_id,
                                    CategoryModel.is_active == True)
    category = (await db.scalars(category_stmt)).first()

    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Category not found or inactive')

    updated_product = product.model_dump(exclude_unset=True)
    await db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(**updated_product)
    )
    await db.commit()
    return db_product

@router.delete('/{product_id}', status_code=status.HTTP_200_OK)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    '''
    Удаляет товар по его ID (логическое удаление).
    '''
    stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    product = (await db.scalars(stmt)).first()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Product not found or inactive')

    product.is_active = False
    await db.commit()

    return product