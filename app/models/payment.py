# app/models/payment.py

from sqlalchemy import Column, String, Integer, Float, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime
import enum

class PaymentStatus(str, enum.Enum):
    ready = "ready"
    paid = "paid"
    cancelled = "cancelled"
    failed = "failed"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    imp_uid = Column(String, unique=True, index=True)
    merchant_uid = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.ready)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="payments")
