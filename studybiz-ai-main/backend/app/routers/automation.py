"""Automation router — recurring jobs and scheduled tasks."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import AutomationJob, AutomationRun, Notification, User, Order, OrderStatus
from app.schemas import AutomationJobResponse, AutomationJobUpdate
from app.utils.auth import get_current_user
from datetime import datetime, timedelta
from app.config import settings

router = APIRouter(prefix="/api/automation", tags=["automation"])

# Default automation job templates
DEFAULT_JOBS = [
    {"name": "Daily Academic Briefing", "job_type": "daily_academic_briefing", "schedule_cron": "0 7 * * *"},
    {"name": "Daily Business Briefing", "job_type": "daily_business_briefing", "schedule_cron": "0 8 * * *"},
    {"name": "Upcoming Exam Warning", "job_type": "exam_warning", "schedule_cron": "0 6 * * *"},
    {"name": "Assignment Deadline Warning", "job_type": "assignment_deadline_warning", "schedule_cron": "0 6 * * *"},
    {"name": "Pending Payment Review", "job_type": "pending_payment_review", "schedule_cron": "0 9 * * *"},
    {"name": "Orders Ready to Package", "job_type": "orders_ready_to_pack", "schedule_cron": "0 9 * * *"},
    {"name": "Shipping Cutoff Check", "job_type": "shipping_cutoff_check", "schedule_cron": "0 14 * * *"},
    {"name": "Inventory Shortage Warning", "job_type": "inventory_shortage_warning", "schedule_cron": "0 10 * * *"},
    {"name": "Supplier Arrival Follow-up", "job_type": "supplier_arrival_followup", "schedule_cron": "0 11 * * *"},
    {"name": "Weekly Sales & Profit Summary", "job_type": "weekly_sales_summary", "schedule_cron": "0 9 * * 1"},
]


@router.get("/", response_model=List[AutomationJobResponse])
def list_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jobs = db.query(AutomationJob).filter(AutomationJob.user_id == current_user.id).all()

    # Initialize default jobs if none exist
    if not jobs:
        for template in DEFAULT_JOBS:
            job = AutomationJob(
                user_id=current_user.id,
                name=template["name"],
                job_type=template["job_type"],
                schedule_cron=template["schedule_cron"],
                is_enabled=True,
            )
            db.add(job)
        db.commit()
        jobs = db.query(AutomationJob).filter(AutomationJob.user_id == current_user.id).all()

    return jobs


@router.put("/{job_id}", response_model=AutomationJobResponse)
def update_job(
    job_id: int,
    job_in: AutomationJobUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(AutomationJob).filter(
        AutomationJob.id == job_id,
        AutomationJob.user_id == current_user.id,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Automation job not found")

    for field, value in job_in.model_dump(exclude_unset=True).items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/run-now")
def run_job_now(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually trigger an automation job."""
    job = db.query(AutomationJob).filter(
        AutomationJob.id == job_id,
        AutomationJob.user_id == current_user.id,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Automation job not found")

    # Execute the job
    run = AutomationRun(
        job_id=job.id,
        started_at=datetime.utcnow(),
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Generate notification based on job type
    notif_title = ""
    notif_message = ""

    if job.job_type == "daily_academic_briefing":
        from app.agent.tools import AgentTools
        tools = AgentTools(db, current_user)
        schedule = tools.get_academic_schedule(days_ahead=1)
        notif_title = "📚 Daily Academic Briefing"
        notif_message = f"You have {len(schedule)} academic event(s) today."

    elif job.job_type == "daily_business_briefing":
        from app.agent.tools import AgentTools
        tools = AgentTools(db, current_user)
        tasks = tools.get_business_tasks()
        notif_title = "📦 Daily Business Briefing"
        notif_message = (f"{tasks['paid_orders_needing_packing']} orders to pack, "
                        f"{tasks['packed_orders_needing_dispatch']} ready to dispatch, "
                        f"{tasks['open_exceptions']} open exceptions.")

    elif job.job_type == "pending_payment_review":
        from app.agent.tools import AgentTools
        tools = AgentTools(db, current_user)
        summary = tools.get_payment_summary()
        notif_title = "💰 Pending Payment Review"
        notif_message = f"Outstanding payments: RM {summary['outstanding_payments']}"

    elif job.job_type == "inventory_shortage_warning":
        from app.agent.tools import AgentTools
        tools = AgentTools(db, current_user)
        inv = tools.get_inventory_status()
        low = [p for p in inv if p.get("is_low_stock")]
        notif_title = "⚠️ Inventory Shortage Warning"
        notif_message = f"{len(low)} product(s) are low on stock."

    elif job.job_type == "weekly_sales_summary":
        from app.routers.finance import get_summary
        from app.schemas import FinanceSummary
        notif_title = "📊 Weekly Sales Summary"
        notif_message = "Weekly sales summary generated. Check the Finance page."

    else:
        notif_title = f"🔔 {job.name}"
        notif_message = f"Automation job '{job.name}' executed successfully."

    if notif_title:
        notif = Notification(
            user_id=current_user.id,
            title=notif_title,
            message=notif_message,
            category="automation",
            is_read=False,
        )
        db.add(notif)

    # Update job status
    run.completed_at = datetime.utcnow()
    run.status = "success"
    run.result = notif_message

    job.last_run = datetime.utcnow()
    job.last_status = "success"
    job.next_run = datetime.utcnow() + timedelta(hours=24)

    db.commit()

    return {"detail": "Job executed successfully", "notification": notif_title, "message": notif_message}


@router.get("/{job_id}/runs")
def get_job_runs(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(AutomationJob).filter(
        AutomationJob.id == job_id,
        AutomationJob.user_id == current_user.id,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Automation job not found")

    runs = db.query(AutomationRun).filter(AutomationRun.job_id == job_id).order_by(
        AutomationRun.started_at.desc()
    ).limit(50).all()

    return [
        {
            "id": r.id,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "status": r.status,
            "result": r.result,
            "error": r.error,
        }
        for r in runs
    ]
