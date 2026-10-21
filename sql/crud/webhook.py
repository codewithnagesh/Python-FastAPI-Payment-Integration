from sql.models import webhook
from sqlalchemy.orm import Session


def _create(db: Session, data):
    new_data = webhook.Webhook(data=str(data))
    db.add(new_data)
    db.commit()
    db.refresh(new_data)
    return True
