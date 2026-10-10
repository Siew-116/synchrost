"""Products and inventory router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Product, StockMovement, User
from app.schemas import ProductCreate, ProductUpdate, ProductResponse
from app.utils.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/", response_model=List[ProductResponse])
def list_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Product).filter(Product.user_id == current_user.id).order_by(Product.created_at.desc()).all()


@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_product = Product(**product.model_dump(), user_id=current_user.id)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    # Record initial stock as a movement
    if db_product.available_stock > 0:
        movement = StockMovement(
            product_id=db_product.id,
            movement_type="initial",
            quantity_change=db_product.available_stock,
            reference="Initial stock",
            notes="Initial stock when product created",
        )
        db.add(movement)
        db.commit()

    return db_product


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    old_stock = product.available_stock
    for field, value in product_in.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    # Record stock adjustment
    if product_in.available_stock is not None and product_in.available_stock != old_stock:
        diff = product_in.available_stock - old_stock
        movement = StockMovement(
            product_id=product.id,
            movement_type="adjust",
            quantity_change=diff,
            reference="Manual adjustment",
            notes=f"Stock adjusted from {old_stock} to {product_in.available_stock}",
        )
        db.add(movement)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Delete associated stock movements first (avoid NOT NULL constraint violation)
    from app.models import StockMovement
    db.query(StockMovement).filter(StockMovement.product_id == product_id).delete()

    # Soft-check: don't allow deleting products with active order items
    from app.models import OrderItem, Order, OrderStatus
    active_items = db.query(OrderItem).join(Order).filter(
        OrderItem.product_id == product_id,
        Order.user_id == current_user.id,
        Order.status.in_([OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PAID,
                          OrderStatus.PACKED, OrderStatus.DISPATCHED]),
    ).count()
    if active_items > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete product with {active_items} active order item(s). Cancel or complete those orders first."
        )

    db.delete(product)
    db.commit()
    return {"detail": "Product deleted"}


@router.get("/{product_id}/movements")
def get_stock_movements(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    movements = db.query(StockMovement).filter(StockMovement.product_id == product_id).order_by(
        StockMovement.created_at.desc()
    ).all()
    return [
        {
            "id": m.id,
            "movement_type": m.movement_type,
            "quantity_change": m.quantity_change,
            "reference": m.reference,
            "notes": m.notes,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in movements
    ]


@router.get("/alerts/low-stock")
def low_stock_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    products = db.query(Product).filter(
        Product.user_id == current_user.id,
        Product.is_active == True,
        Product.available_stock <= Product.low_stock_threshold,
    ).all()
    return [
        {
            "product_id": p.id,
            "name": p.name,
            "available_stock": p.available_stock,
            "low_stock_threshold": p.low_stock_threshold,
        }
        for p in products
    ]
