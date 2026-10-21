from datetime import datetime
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from sql.models.contact_payment_profile_details import ContactPaymentProfileDetails
import sql.crud.contact_payment_profile as contact_payment_profile_crud
from sql.models.contact_payment_profile import ContactPaymentProfile


# Create
def _create(
    db: Session,
    data: ContactPaymentProfileDetails,
    contact_payment_profile_id,
):
    data.contact_payment_profile_id = contact_payment_profile_id
    data.created_at = datetime.now()
    db.add(data)
    db.commit()
    db.refresh(data)
    return True


# Get
def get(db: Session, _id):
    return (
        db.query(ContactPaymentProfileDetails)
        .filter(ContactPaymentProfileDetails.id == _id)
        .first()
    )
