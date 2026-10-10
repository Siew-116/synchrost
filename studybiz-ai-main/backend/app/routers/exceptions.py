"""Business exceptions router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import BusinessException, ExceptionStatus, User
from app.schemas import ExceptionCreate, ExceptionUpdate, ExceptionResponse
from app.utils.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/exceptions", tags=["exceptions"])


@router.get("/", response_model=List[ExceptionResponse])
def list_exceptions(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(BusinessException).filter(BusinessException.user_id == current_user.id)
    if status_filter:
        try:
            status_enum = ExceptionStatus(status_filter)
            q = q.filter(BusinessException.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_filter}")
    return q.order_by(BusinessException.created_at.desc()).all()


@router.post("/", response_model=ExceptionResponse)
def create_exception(
    exc: ExceptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_exc = BusinessException(**exc.model_dump(), user_id=current_user.id)
    db.add(db_exc)
    db.commit()
    db.refresh(db_exc)
    return db_exc


@router.get("/{exc_id}", response_model=ExceptionResponse)
def get_exception(
    exc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exc = db.query(BusinessException).filter(
        BusinessException.id == exc_id,
        BusinessException.user_id == current_user.id,
    ).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")
    return exc


@router.put("/{exc_id}", response_model=ExceptionResponse)
def update_exception(
    exc_id: int,
    exc_in: ExceptionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exc = db.query(BusinessException).filter(
        BusinessException.id == exc_id,
        BusinessException.user_id == current_user.id,
    ).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")

    for field, value in exc_in.model_dump(exclude_unset=True).items():
        setattr(exc, field, value)

    if exc_in.status == ExceptionStatus.RESOLVED or exc_in.status == ExceptionStatus.CLOSED:
        exc.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(exc)
    return exc


@router.delete("/{exc_id}")
def delete_exception(
    exc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exc = db.query(BusinessException).filter(
        BusinessException.id == exc_id,
        BusinessException.user_id == current_user.id,
    ).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")
    db.delete(exc)
    db.commit()
    return {"detail": "Exception deleted"}
