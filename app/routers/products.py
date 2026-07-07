from fastapi import APIRouter

router = APIRouter(
    prefix='/products',
    tags=['products']
)

@router.get('/')
async def get_all_products():
    """
    Возвращает список всех товаров.
    """
    return {'message': '#'}

@router.post('/')
async def crete_product():
    """
    Создаёт новый товар.
    """
    return {'message': '#'}

@router.get('/category/{category_id}')
async def get_product_by_category(category_id: int):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    return {'message': '#'}

@router.get('/{product_id}')
async def get_product_by_id(product_id: int):
    """
    Возвращает детальную информацию о товаре по его ID.
    """
    return {'message': '#'}

@router.put('/{product_id}')
async def update_product(product_id: int):
    """
    Обновляет товар по его ID.
    """
    return {'message': '#'}

@router.delete('/{product_id}')
async def delete_product_by_id(product_id):
    """
    Удаляет товар по его ID.
    """
    return {'message': '#'}