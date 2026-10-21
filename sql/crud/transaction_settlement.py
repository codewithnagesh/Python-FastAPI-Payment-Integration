from sqlalchemy.orm import Session
from sql.models.transaction_settlement import TransactionSettlement
from sqlalchemy import or_, desc
from datetime import datetime
from typing import List


# Create new Settlement
def _create(db: Session, data: TransactionSettlement) -> TransactionSettlement:
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


# Find Settlement by Transaction ID
def _find_by_transaction_id(db: Session, transaction_id: int) -> TransactionSettlement:
    return (
        db.query(TransactionSettlement)
        .filter(TransactionSettlement.transaction_id == transaction_id)
        .first()
    )


# Find Settlement by Paysafe Settlement ID
def _find_by_payment_settlement_id(
    db: Session, payment_settlement_id
) -> TransactionSettlement:
    return (
        db.query(TransactionSettlement)
        .filter(TransactionSettlement.payment_settlement_id == payment_settlement_id)
        .order_by(desc(TransactionSettlement.id))
        .first()
    )


# Update Settlement status
def _update(db: Session, record: TransactionSettlement, status):
    record.status = status
    record.updated_at = datetime.now()
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
