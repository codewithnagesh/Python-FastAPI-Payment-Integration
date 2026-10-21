from sqlalchemy.orm import Session
from sql.models.transaction_refunds import TransactionRefund
from sqlalchemy import or_, desc
from datetime import datetime


def _create(db: Session, data: TransactionRefund) -> TransactionRefund:
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


def _find_by_id(db: Session, _id) -> TransactionRefund:
    return db.query(TransactionRefund).filter(TransactionRefund.id == _id).first()


def _find_by_transaction_id(db: Session, transaction_id: int) -> TransactionRefund:
    return (
        db.query(TransactionRefund)
        .filter(TransactionRefund.transaction_id == transaction_id)
        .first()
    )


def _find_by_payment_refund_id(db: Session, payment_refund_id) -> TransactionRefund:
    return (
        db.query(TransactionRefund)
        .filter(TransactionRefund.payment_refund_id == payment_refund_id)
        .order_by(desc(TransactionRefund.id))
        .first()
    )


def _find_by_paysafe_refund_id_or_reference_number(
    db: Session, payment_refund_id, reference_number
) -> TransactionRefund:
    return (
        db.query(TransactionRefund)
        .filter(
            or_(
                TransactionRefund.payment_refund_id == payment_refund_id,
                TransactionRefund.reference_number == reference_number,
            )
        )
        .order_by(desc(TransactionRefund.id))
        .first()
    )


def _update(db: Session, record: TransactionRefund, status):
    record.status = status
    record.updated_at = datetime.now()
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
