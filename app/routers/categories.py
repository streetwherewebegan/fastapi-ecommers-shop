from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import is_admin
from app.db_depends import get_async_db
from app.models.categories import Category as CategoryModel
from app.models.users import User as UserModel
from app.schemas import Category as CategorySchema, CategoryCreate


router = APIRouter(
    prefix='/categories',
    tags=['categories'],
)

@router.get('/', response_model=list[CategorySchema], status_code=status.HTTP_200_OK)
async def get_all_categories(db: AsyncSession = Depends(get_async_db)):
    '''
    Возвращает список всех категорий товаров
    '''
    result = await db.scalars(select(CategoryModel).where(
        CategoryModel.is_active == True
    ))
    db_categories = result.all()
    return db_categories

@router.post('/', response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_async_db),
    _: UserModel =  Depends(is_admin)):
    '''
    Создаёт новую категорию
    '''
    if category.parent_id is not None:
        result = await db.scalars(select(CategoryModel).where(
            CategoryModel.id == category.parent_id,
            CategoryModel.is_active == True
        ))
        parent = result.first()

        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Parent category not found.'
            )

    db_category = CategoryModel(**category.model_dump())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category

@router.put('/{category_id}', response_model=CategorySchema, status_code=status.HTTP_200_OK)
async def update_category(
    category_id: int,
    category: CategoryCreate,
    db: AsyncSession = Depends(get_async_db),
    _: UserModel = Depends(is_admin)):
    '''
    Обновляет категорию по её ID
    '''
    result = await db.scalars(select(CategoryModel).where(
        CategoryModel.id == category_id,
        CategoryModel.is_active == True
    ))
    db_category = result.first()

    if db_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Category not found'
        )

    if category.parent_id is not None:
        parent_result = await db.scalars(select(CategoryModel).where(
            CategoryModel.id == category.parent_id,
            CategoryModel.is_active == True
        ))
        parent = parent_result.first()

        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Parent category not found'
            )

        if parent.id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Category cannot be its own parent'
            )

    update_data = category.model_dump(exclude_unset=True)

    await db.execute(
        update(CategoryModel)
        .where(CategoryModel.id == category_id)
        .values(**update_data)
    )
    await db.commit()
    return db_category

@router.delete('/{category_id}', status_code=status.HTTP_200_OK)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_async_db),
    _: UserModel = Depends(is_admin)):
    '''
    Удаляет категорию по её ID
    '''
    result = await db.scalars(select(CategoryModel).where(
        CategoryModel.id == category_id,
        CategoryModel.is_active == True
    ))
    db_category = result.first()

    if db_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Category not found or inactive.'
        )

    await db.execute(
        update(CategoryModel)
        .where(CategoryModel.id == category_id)
        .values(is_active = False)
        )
    await db.commit()
    return db_category