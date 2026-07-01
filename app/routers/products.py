from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select, and_, update 
from sqlalchemy.orm import Session

from app.schemas import ProductCreate, Product as ProductSchema

from app.models.categories import Category as CategoryModel
from app.models.products import Product as ProductModel

from app.db_depends import get_db


router = APIRouter(
    prefix='/products',
    tags=['products']
)

@router.get('/', response_model=list[ProductSchema], status_code=status.HTTP_200_OK)
async def get_all_products(db: Session = Depends(get_db)):
    """
    Возвращает список всех товаров.
    """
    stmt = select(ProductModel).where(ProductModel.is_active == True)
    products = db.scalars(stmt).all()
    return products

@router.post('/', response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def crete_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Создаёт новый товар.
    """
    stmt = select(CategoryModel).where(CategoryModel.id == product.category_id,
                                       CategoryModel.is_active == True)
    category = db.scalars(stmt).first()
    if category is None:
        raise HTTPException(status_code=400, detail='Category not found or inactive')
    
    db_product = ProductModel(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get('/category/{category_id}', response_model=list[ProductSchema], status_code=status.HTTP_200_OK)
async def get_product_by_category(category_id: int, db: Session = Depends(get_db)):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    category_stmt = select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.is_active == True)
    db_category = db.scalars(category_stmt).first()
    if db_category is None:
        raise HTTPException(status_code=400, detail='Category not found or inactive')
    stmt = select(ProductModel).where(ProductModel.category_id == category_id)
    products = db.scalars(stmt).all()
    return products

@router.get('/{product_id}', response_model=ProductSchema, status_code=status.HTTP_200_OK)
async def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    """
    Возвращает детальную информацию о товаре по его ID.
    """
    stmt = select(ProductModel).where(and_(ProductModel.id == product_id, ProductModel.is_active == True))
    product = db.scalars(stmt).first()
    
    if product is None:
        raise HTTPException(status_code=404, detail='Product not found or inactive')
    
    category_stmt = select(CategoryModel).where(CategoryModel.id == product.category_id, CategoryModel.is_active == True)
    category = db.scalars(category_stmt).first()
    
    if category is None:
        raise HTTPException(status_code=400, detail='Category not found or inactive')
    

    return product

@router.put('/{product_id}', response_model=ProductSchema, status_code=status.HTTP_200_OK)
async def update_product(product_id: int, product_create: ProductCreate, db: Session = Depends(get_db)):
    """
    Обновляет товар по его ID.
    """
    product_stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    db_product = db.scalars(product_stmt).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail='Product not found or inactive')
    
    category_stmt = select(CategoryModel).where(CategoryModel.id == db_product.category_id, CategoryModel.is_active == True)
    db_category = db.scalars(category_stmt).first()
    
    if db_category is None:
        raise HTTPException(status_code=400, detail='Category not found or inactive')
    
    db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(**product_create.model_dump())
    )

    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete('/{product_id}', status_code=status.HTTP_200_OK)
async def delete_product_by_id(product_id: int, db: Session = Depends(get_db)):
    """
    Удаляет товар логически по его ID.
    """
    stmt = select(ProductModel).where(ProductModel.id == product_id)
    product = db.scalars(stmt).first()
    if product is None:
        raise HTTPException(status_code=404, detail='Product not found or inactive')
    
    db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(is_active=False)
    )
    db.commit()

    return {'status': 'success', 'message': 'Product marked as inactive'}