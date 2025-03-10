from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.payment import PaymentCreate, PaymentOut
from app.services.payment_service import create_payment, verify_payment
from app.api import deps

router = APIRouter()

@router.post("/payments", response_model=PaymentOut)
def initiate_payment(
    payment_in: PaymentCreate,
    db: Session = Depends(deps.get_db)
):
    payment = create_payment(db, payment_in)
    return payment

@router.post("/payments/verify")
def confirm_payment(
    imp_uid: str,
    merchant_uid: str,
    db: Session = Depends(deps.get_db)
):
    is_verified = verify_payment(db, imp_uid, merchant_uid)
    if not is_verified:
        raise HTTPException(status_code=400, detail="Payment verification failed.")
    return {"msg": "Payment verified successfully"}
