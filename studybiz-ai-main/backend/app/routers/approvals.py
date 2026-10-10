"""Approval queue router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json
from app.database import get_db
from app.models import ApprovalRequest, User
from app.schemas import ApprovalRequestResponse, ApprovalDecision
from app.utils.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("/", response_model=List[ApprovalRequestResponse])
def list_approvals(
    status_filter: str = "pending",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(ApprovalRequest).filter(ApprovalRequest.user_id == current_user.id)
    if status_filter:
        q = q.filter(ApprovalRequest.status == status_filter)
    return q.order_by(ApprovalRequest.created_at.desc()).all()


@router.post("/", response_model=ApprovalRequestResponse)
def create_approval(
    action_type: str,
    description: str,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    req = ApprovalRequest(
        user_id=current_user.id,
        action_type=action_type,
        description=description,
        payload=json.dumps(payload),
        status="pending",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@router.put("/{approval_id}/decide", response_model=ApprovalRequestResponse)
def decide_approval(
    approval_id: int,
    decision: ApprovalDecision,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    req = db.query(ApprovalRequest).filter(
        ApprovalRequest.id == approval_id,
        ApprovalRequest.user_id == current_user.id,
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Approval already resolved with status: {req.status}")

    req.status = "approved" if decision.approved else "rejected"
    req.resolved_at = datetime.utcnow()
    req.resolved_by = current_user.email
    if decision.note:
        req.result = decision.note

    db.commit()
    db.refresh(req)
    return req
