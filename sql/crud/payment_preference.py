from datetime import datetime
from sqlalchemy.orm import Session
from sql.models.payment_preference import PaymentPreference


# Create
def _create(db: Session, data: PaymentPreference):
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


# Get
def _get(db: Session, id: int):
    return db.query(PaymentPreference).filter(PaymentPreference.id == id).first()


# Get preference by userId with active true status
def _get_by_user(db: Session, user_id: int):
    return (
        db.query(PaymentPreference)
        .filter(
            PaymentPreference.user_id == user_id,
            PaymentPreference.active == True,
        )
        .all()
    )


# Get preference by userId with active true status
def _get_active_preferance_by_user(db: Session, user_id: int, payment_method_type: str):
    return (
        db.query(PaymentPreference)
        .filter(
            PaymentPreference.user_id == user_id,
            PaymentPreference.payment_method_type == payment_method_type,
            PaymentPreference.active == True,
        )
        .first()
    )


def _get_preferance_by_user_with_type(db: Session, user_id: int, preference_type):
    return (
        db.query(PaymentPreference)
        .filter(
            PaymentPreference.user_id == user_id,
            PaymentPreference.preference_type == preference_type,
        )
        .first()
    )


def _edit_preference_status(
    db: Session,
    record: PaymentPreference,
    result: PaymentPreference,
):
    if hasattr(result, "active"):
        record.active = result.active
        record.updated_by = result.updated_by
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _inactive_preference_status(db: Session, record: PaymentPreference, user_id=None):
    record.active = False
    record.updated_by = user_id
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
