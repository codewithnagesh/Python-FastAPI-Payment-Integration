from sqlalchemy.orm import Session
from sql.models.transaction_refund_details import TransactionRefundDetails


def _create(db: Session, data: TransactionRefundDetails):
    db.add(data)
    db.commit()
    db.refresh(data)
    return data
