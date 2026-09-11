from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.product_service import ProductService
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.services.audit_service import write_audit

router = APIRouter(prefix="/products", tags=["Products"])
service = ProductService()


@router.get("", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return service.list(db)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return service.get(db, product_id)


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), actor: User = Depends(require_roles("ADMIN"))):
    item = service.create(db, payload)
    write_audit(db, "PRODUCT_CREATED", actor, "PRODUCT", item.id, {"sku": item.sku, "ean": item.ean})
    return item


@router.put("/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db), actor: User = Depends(require_roles("ADMIN"))):
    item = service.update(db, product_id, payload)
    write_audit(db, "PRODUCT_UPDATED", actor, "PRODUCT", item.id, {"sku": item.sku, "active": item.active})
    return item
