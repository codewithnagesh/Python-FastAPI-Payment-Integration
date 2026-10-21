from sqlalchemy.orm import Session
from sql.models.user_payment_method_options import UserPaymentMethodOptions


# Create
def _create(db: Session, data: UserPaymentMethodOptions):
    db.add(data)
    db.commit()
    db.refresh(data)
    return True


# Create
def _get_by_user_payment_method_id(db: Session, user_payment_method_id):
    return (
        db.query(UserPaymentMethodOptions)
        .filter(
            UserPaymentMethodOptions.user_payment_method_id == user_payment_method_id
        )
        .all()
    )


# Delete
def _delete(db: Session, user_payment_method_id):
    list = (
         db.query(UserPaymentMethodOptions)
        .filter(
            UserPaymentMethodOptions.user_payment_method_id == user_payment_method_id
        )
        .all()
    )
    for data in list:
        db.delete(data)
        db.commit()
    return True
