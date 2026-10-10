"""Campaigns API - group buy management."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db, Campaign, Product, ProductVariant, Order

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


class VariantCreate(BaseModel):
    attributes: str
    available_quantity: int = 30


class ProductCreate(BaseModel):
    name: str
    description: str = ""
    price: float
    stock_limit: int = 100
    variants: list[VariantCreate] = []


class CampaignCreate(BaseModel):
    name: str
    description: str = ""
    payment_instructions: str = "Bank transfer details will be provided after order confirmation."
    opens_at: str | None = None
    closes_at: str | None = None
    late_order_policy: str = "allow_with_approval"
    cancellation_policy: str = "before_payment"
    supplier_lead_time_days: int = 14
    product: ProductCreate


@router.get("")
def list_campaigns(db: Session = Depends(get_db)):
    campaigns = db.query(Campaign).all()
    result = []
    for c in campaigns:
        total_orders = db.query(Order).filter(Order.campaign_id == c.id).count()
        result.append({
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "status": c.status,
            "opens_at": c.opens_at.isoformat() if c.opens_at else None,
            "closes_at": c.closes_at.isoformat() if c.closes_at else None,
            "payment_instructions": c.payment_instructions,
            "late_order_policy": c.late_order_policy,
            "cancellation_policy": c.cancellation_policy,
            "supplier_lead_time_days": c.supplier_lead_time_days,
            "total_orders": total_orders,
        })
    return result


@router.get("/{campaign_id}")
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")

    products = db.query(Product).filter(Product.campaign_id == c.id).all()
    product_list = []
    for p in products:
        variants = db.query(ProductVariant).filter(ProductVariant.product_id == p.id).all()
        product_list.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "stock_limit": p.stock_limit,
            "variants": [{
                "id": v.id,
                "attributes": v.attributes,
                "available_quantity": v.available_quantity,
            } for v in variants],
        })

    # Variant totals
    from app.services.agent import AgentTools
    tools = AgentTools(db)
    totals = tools.calculate_group_buy_totals(c.id)

    return {
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "status": c.status,
        "opens_at": c.opens_at.isoformat() if c.opens_at else None,
        "closes_at": c.closes_at.isoformat() if c.closes_at else None,
        "payment_instructions": c.payment_instructions,
        "late_order_policy": c.late_order_policy,
        "cancellation_policy": c.cancellation_policy,
        "supplier_lead_time_days": c.supplier_lead_time_days,
        "products": product_list,
        "variant_totals": totals,
    }


@router.post("")
def create_campaign(data: CampaignCreate, db: Session = Depends(get_db)):
    from datetime import datetime, timezone

    campaign = Campaign(
        name=data.name,
        description=data.description,
        status="open",
        opens_at=datetime.fromisoformat(data.opens_at) if data.opens_at else datetime.now(timezone.utc),
        closes_at=datetime.fromisoformat(data.closes_at) if data.closes_at else None,
        payment_instructions=data.payment_instructions,
        late_order_policy=data.late_order_policy,
        cancellation_policy=data.cancellation_policy,
        supplier_lead_time_days=data.supplier_lead_time_days,
    )
    db.add(campaign)
    db.flush()

    product = Product(
        campaign_id=campaign.id,
        name=data.product.name,
        description=data.product.description,
        price=data.product.price,
        stock_limit=data.product.stock_limit,
    )
    db.add(product)
    db.flush()

    for v in data.product.variants:
        variant = ProductVariant(
            product_id=product.id,
            attributes=v.attributes,
            available_quantity=v.available_quantity,
        )
        db.add(variant)

    db.commit()
    return {"id": campaign.id, "name": campaign.name, "status": "created"}


@router.post("/{campaign_id}/close")
def close_campaign(campaign_id: int, db: Session = Depends(get_db)):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    c.status = "closed"
    db.commit()
    return {"id": c.id, "status": c.status}
