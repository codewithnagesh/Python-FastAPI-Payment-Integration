from sqlalchemy.orm import Session
from sql.models.refund_items import RefundItems as RefundItemsModel


def _create(db: Session, refund_item: RefundItemsModel):
    db.add(refund_item)
    db.commit()
    db.refresh(refund_item)
    return refund_item

