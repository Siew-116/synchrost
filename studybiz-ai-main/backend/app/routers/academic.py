"""Academic events router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import AcademicEvent, User
from app.schemas import AcademicEventCreate, AcademicEventUpdate, AcademicEventResponse
from app.utils.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/academic", tags=["academic"])


@router.get("/", response_model=List[AcademicEventResponse])
def list_events(
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(AcademicEvent).filter(AcademicEvent.user_id == current_user.id)
    if event_type:
        q = q.filter(AcademicEvent.event_type == event_type)
    if start_date:
        q = q.filter(AcademicEvent.start_datetime >= datetime.fromisoformat(start_date))
    if end_date:
        q = q.filter(AcademicEvent.start_datetime <= datetime.fromisoformat(end_date))
    return q.order_by(AcademicEvent.start_datetime.asc()).all()


@router.post("/", response_model=AcademicEventResponse)
def create_event(
    event: AcademicEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_event = AcademicEvent(**event.model_dump(), user_id=current_user.id)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@router.get("/{event_id}", response_model=AcademicEventResponse)
def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(AcademicEvent).filter(
        AcademicEvent.id == event_id,
        AcademicEvent.user_id == current_user.id,
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/{event_id}", response_model=AcademicEventResponse)
def update_event(
    event_id: int,
    event_in: AcademicEventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(AcademicEvent).filter(
        AcademicEvent.id == event_id,
        AcademicEvent.user_id == current_user.id,
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    for field, value in event_in.model_dump(exclude_unset=True).items():
        setattr(event, field, value)

    if event_in.is_completed and not event.completed_at:
        event.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(AcademicEvent).filter(
        AcademicEvent.id == event_id,
        AcademicEvent.user_id == current_user.id,
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
    return {"detail": "Event deleted"}
