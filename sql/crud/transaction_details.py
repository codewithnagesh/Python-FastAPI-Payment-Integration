from datetime import datetime
from sqlalchemy.orm import Session
from sql.models.transaction_details import TransactionDetails


# Create
def _create(db: Session, data: TransactionDetails):
    db.add(data)
    db.commit()
    db.refresh(data)
    return True


# Delete
def _delete(db: Session, transaction_id):
    list = (
        db.query(TransactionDetails).filter_by(transaction_id == transaction_id).all()
    )
    for data in list:
        db.delete(data)
        db.commit()
    return True
