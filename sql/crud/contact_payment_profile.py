from datetime import datetime
from sqlalchemy.orm import Session
from sql.models.contact_payment_profile import ContactPaymentProfile
from sql.models import users
from sqlalchemy import asc, desc, or_


# Create
def _create(db: Session, data: ContactPaymentProfile):
    data.created_at = datetime.now()
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


# Get
def _get(db: Session, id):
    return (
        db.query(ContactPaymentProfile).filter(ContactPaymentProfile.id == id).first()
    )


# find by contact payment profile by contact id and payment profile
def _find_by_user_id_and_payment_profile_id(
    db: Session, user_id, payment_profile_id
):
    return (
        db.query(ContactPaymentProfile)
        .filter(
            ContactPaymentProfile.user_id == user_id,
            ContactPaymentProfile.id == payment_profile_id,
        )
        .first()
    )


# Get
def _get_by_user_id(db: Session, user_id):
    return (
        db.query(ContactPaymentProfile)
        .filter(ContactPaymentProfile.user_id == user_id)
        .first()
    )


# Get
def get_by_profile_id(db: Session, _profile_id):
    return (
        db.query(ContactPaymentProfile)
        .filter(ContactPaymentProfile.payment_profile_id == _profile_id)
        .first()
    )


# Update
def _update(
    db: Session,
    record: ContactPaymentProfile,
    result: ContactPaymentProfile,
):
    if hasattr(result, "user_id"):
        if result.user_id is not None and result.user_id != 0:
            record.user_id = result.user_id

    if hasattr(result, "profile_id"):
        if result.profile_id is not None and result.profile_id != 0:
            if record.profile_id != result.profile_id:
                if _check_profile_id(db, result.profile_id):
                    raise PermissionError("Profile id already exist")
                record.profile_id = result.profile_id

    if hasattr(result, "payment_profile_id"):
        if result.payment_profile_id != "":
            record.payment_profile_id = result.payment_profile_id

    if hasattr(result, "reference_number"):
        if result.reference_number != "":
            record.reference_number = result.reference_number
    current_date = datetime.now()
    record.updated_at = current_date
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# Delete
def _delete(db: Session, data: ContactPaymentProfile):
    db.delete(data)
    db.commit()
    return True


# Check ProfileId
def _check_profile_id(db: Session, profile_id):
    return (
        db.query(ContactPaymentProfile)
        .filter(ContactPaymentProfile.profile_id == profile_id)
        .first()
    )


# Check user id
def _find_by_user_id(db: Session, user_id):
    return (
        db.query(ContactPaymentProfile)
        .filter(ContactPaymentProfile.user_id == user_id)
        .first()
    )


def _get_all_by_user_id(db: Session, user_id):
    return (
        db.query(ContactPaymentProfile)
        .filter(ContactPaymentProfile.user_id == user_id)
        .all()
    )


# Get all
def _get_all(
    db: Session,
    filter=None,
    order_by=None,
    order_direction=None,
    user_id=None,
    page=1,
    limit=25,
):
    query = (
        db.query(ContactPaymentProfile)
        .join(users.User, users.User.id == ContactPaymentProfile.user_id)
    )

    if filter:
        if filter is not None and filter != "":
            search = "%{}%".format(filter)
            query = query.filter(
                or_(
                    # ContactPaymentProfile table
                    ContactPaymentProfile.profile_id.like(search),
                    ContactPaymentProfile.payment_profile_id.like(search),
                    ContactPaymentProfile.reference_number.like(search),
                    # User table
                    users.User.first_name.like(search),
                    users.User.last_name.like(search),
                    users.User.username.like(search),
                )
            )

    if user_id and user_id > 0:
        query = query.filter(users.User.id == user_id)

    if order_by is not None and order_by != "":
        if order_direction == "asc":
            query = query.order_by(asc(getattr(ContactPaymentProfile, order_by)))
        else:
            query = query.order_by(desc(getattr(ContactPaymentProfile, order_by)))

    total_items = query.count()

    if page is not None and limit is not None:
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

    current_items = query.count()

    profiles = query.all()

    return {
        "limit": limit,
        "page": page,
        "current_items": current_items,
        "total_items": total_items,
        "profiles": profiles,
    }
