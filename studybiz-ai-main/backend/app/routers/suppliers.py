"""Suppliers router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Supplier, PurchaseOrder, User
from app.schemas import SupplierCreate, SupplierResponse
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@router.get("/", response_model=List[SupplierResponse])
def list_suppliers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Supplier).filter(Supplier.user_id == current_user.id).order_by(Supplier.created_at.desc()).all()


@router.post("/", response_model=SupplierResponse)
def create_supplier(
    supplier: SupplierCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_supplier = Supplier(**supplier.model_dump(), user_id=current_user.id)
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.user_id == current_user.id,
    ).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    supplier_in: SupplierCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.user_id == current_user.id,
    ).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    for field, value in supplier_in.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.user_id == current_user.id,
    ).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    db.delete(supplier)
    db.commit()
    return {"detail": "Supplier deleted"}
