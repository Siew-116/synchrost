"""Supplier Summary API."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.database import get_db, Campaign
from app.services.agent import AgentTools
import csv
import io

router = APIRouter(prefix="/api/supplier", tags=["supplier"])


@router.get("/summary/{campaign_id}")
def get_supplier_summary(campaign_id: int, db: Session = Depends(get_db)):
    tools = AgentTools(db)
    summary = tools.generate_supplier_summary(campaign_id)
    return summary


@router.get("/summary/{campaign_id}/csv")
def download_supplier_csv(campaign_id: int, db: Session = Depends(get_db)):
    tools = AgentTools(db)
    summary = tools.generate_supplier_summary(campaign_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Campaign", summary["campaign_name"]])
    writer.writerow(["Generated At", summary["generated_at"]])
    writer.writerow(["Is Final", "Yes" if summary["is_final"] else "No"])
    writer.writerow([])
    writer.writerow(["Variant", "Quantity"])
    for variant, qty in summary["variants"].items():
        writer.writerow([variant, qty])
    writer.writerow(["Total", summary["total_units"]])
    writer.writerow([])
    writer.writerow(["Excluded (Cancelled)", summary["excluded_cancelled"]])
    writer.writerow(["Unresolved Exceptions", summary["unresolved_exceptions"]])

    filename = f"supplier_summary_{campaign_id}.csv"
    return PlainTextResponse(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
