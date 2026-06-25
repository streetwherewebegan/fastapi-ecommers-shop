# import sys
# from pathlib import Path

# sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.models.categories import Category
from app.models.products import Product
from sqlalchemy.schema import CreateTable


if __name__ == "__main__":
    #print(CreateTable(Category.__table__))
    #print(CreateTable(Product.__table__))
    pass