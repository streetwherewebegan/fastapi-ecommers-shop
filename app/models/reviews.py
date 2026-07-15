from sqlalchemy import (
    Integer, 
    Text, 
    DateTime, 
    Boolean, 
    ForeignKey, 
    CheckConstraint, 
    func
)
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base


class Review(Base):
    __tablename__ = 'reviews'

    __table_args__ = (
        CheckConstraint(
            'grade >= 1 AND grade <= 5',
            name='check_grade',
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.id'))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment_date: Mapped[datetime] =  mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    grade: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)