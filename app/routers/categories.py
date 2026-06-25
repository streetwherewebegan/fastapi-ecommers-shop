from fastapi import APIRouter

router = APIRouter(
    prefix='/categories',
    tags=['categories'],
)


@router.get('/')
async def get_all_categories():
    '''
    Возвращает список всех категорий товаров
    '''
    return {"message": '#'}

@router.post('/')
async def create_category():
    '''
    Создаёт новую категорию
    '''
    return {"message": '#'}

@router.put('/{category_id}')
async def update_category(category_id: int):
    '''
    Обновляет категорию по её ID
    '''
    return {"message": '#'}

@router.delete('/{category_id}')
async def delete_category(categpry_id: int):
    '''
    Удаляет категорию по её ID
    '''
    return {"message": '#'}