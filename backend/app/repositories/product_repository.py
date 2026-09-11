from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.product import Product


class ProductRepository:
    def list(self, db: Session) -> list[Product]:
        return list(db.scalars(select(Product).order_by(Product.id)).all())

    def get(self, db: Session, product_id: int) -> Product | None:
        return db.get(Product, product_id)

    def get_by_sku(self, db: Session, sku: str) -> Product | None:
        return db.scalar(select(Product).where(Product.sku == sku))

    def get_by_ean(self, db: Session, ean: str) -> Product | None:
        return db.scalar(select(Product).where(Product.ean == ean))

    def create(self, db: Session, product: Product) -> Product:
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    def delete(self, db: Session, product: Product) -> None:
        db.delete(product)
        db.commit()
