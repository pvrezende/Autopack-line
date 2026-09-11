from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self) -> None:
        self.repository = ProductRepository()

    def list(self, db: Session) -> list[Product]:
        return self.repository.list(db)

    def get(self, db: Session, product_id: int) -> Product:
        product = self.repository.get(db, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
        return product

    def create(self, db: Session, payload: ProductCreate) -> Product:
        product = Product(**payload.model_dump())
        try:
            return self.repository.create(db, product)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU ou EAN já cadastrado") from exc

    def update(self, db: Session, product_id: int, payload: ProductUpdate) -> Product:
        product = self.get(db, product_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        try:
            db.commit()
            db.refresh(product)
            return product
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU ou EAN já cadastrado") from exc
