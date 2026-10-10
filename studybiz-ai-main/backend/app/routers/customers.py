"""Customers router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Customer, User
from app.schemas import CustomerCreate, CustomerUpdate, CustomerResponse
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("/", response_model=List[CustomerResponse])
def list_customers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Customer).filter(Customer.user_id == current_user.id).order_by(Customer.created_at.desc()).all()


@router.post("/", response_model=CustomerResponse)
def create_customer(
    customer: CustomerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_customer = Customer(**customer.model_dump(), user_id=current_user.id)
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.user_id == current_user.id,
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    customer_in: CustomerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.user_id == current_user.id,
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    for field, value in customer_in.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.user_id == current_user.id,
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    db.delete(customer)
    db.commit()
    return {"detail": "Customer deleted"}
