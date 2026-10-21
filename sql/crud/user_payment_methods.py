from datetime import datetime
from sqlalchemy import and_, asc, desc, or_
from sqlalchemy.orm import Session
from sql.models.user_payment_methods import UserPaymentMethods
from enumerations.user_payment_methods import Type, StatusType
from sql.models import users, payment_preference
from datetime import timedelta


# Create
def _create(db: Session, data: UserPaymentMethods):
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


# Get
def _get_by_id(db: Session, _id):
    return db.query(UserPaymentMethods).filter(UserPaymentMethods.id == _id).first()


# Update
def _update(
    db: Session,
    record: UserPaymentMethods,
    result: UserPaymentMethods,
):
    if result.status != "":
        record.status = result.status

    if result.payment_preference is not None and result.payment_preference != 0:
        record.payment_preference = result.payment_preference

    if result.user_id is not None and result.user_id != 0:
        record.user_id = result.user_id

    if result.is_default:
        record.is_default = result.is_default
    
    if result.updated_by != 0:
        record.updated_by = result.updated_by

    current_date = datetime.now()
    record.updated_at = current_date
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# _get_approved_payment_method
def _get_approved_payment_method(
    db: Session,
    user_id=None,
    payment_type=Type.PAYSAFE,
):
    return (
        db.query(UserPaymentMethods)
        .filter(
            UserPaymentMethods.user_id == user_id,
            UserPaymentMethods.payment_method_type == payment_type,
            UserPaymentMethods.deleted_at == None,
            UserPaymentMethods.status == StatusType.APPROVED,
        )
        .first()
    )


# _get_approved_pending_payment_method
def _get_approved_pending_payment_method(
    db: Session,
    user_id=None,
    payment_type=Type.PAYSAFE,
):
    return (
        db.query(UserPaymentMethods)
        .filter(
            UserPaymentMethods.user_id == user_id,
            UserPaymentMethods.payment_method_type == payment_type,
            UserPaymentMethods.deleted_at == None,
            UserPaymentMethods.status.in_([StatusType.PENDING, StatusType.APPROVED]),
        )
        .first()
    )


# Check user with payment type in table
def check_user_with_pyment_type(db: Session, preference_id, payment_method_type):
    return (
        db.query(UserPaymentMethods)
        .filter(
            UserPaymentMethods.payment_preference_id == preference_id,
            UserPaymentMethods.payment_method_type == payment_method_type,
            UserPaymentMethods.status == StatusType.APPROVED,
        )
        .first()
    )


# Soft Delete
def _soft_delete(
    db: Session,
    record: UserPaymentMethods,
    user,
):
    record.status = StatusType.DISABLED
    record.is_default = False
    record.deleted_by = user.id
    current_date = datetime.now()
    record.deleted_at = current_date
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# Disable records by preference id
def _change_disable_status(
    db: Session,
    payment_preference_id: int,
    user,
):
    records = (
        db.query(UserPaymentMethods)
        .filter(UserPaymentMethods.payment_preference_id == payment_preference_id)
        .all()
    )
    for record in records:
        _soft_delete(db, record, user)
    return True


# List Auth merchants
def _list_user_payment_methods(
    db: Session,
    filter=None,
    order_by="id",
    status=None,
    payment_method_type=None,
    order_direction=None,
    user_id=None,
    payment_preference_id=None,
    page: int = 1,
    limit=25,
    start_date=None,
    end_date=None,
):

    query = (
        db.query(UserPaymentMethods)
        .join(users.User, users.User.id == UserPaymentMethods.user_id, isouter=True)
        .join(
            payment_preference.PaymentPreference,
            payment_preference.PaymentPreference.id
            == UserPaymentMethods.payment_preference_id,
        )
    )

    if filter and filter != "":
        search = "%{}%".format(filter.strip())
        query = query.filter(
            or_(
                UserPaymentMethods.payment_preference_id.like(search),
                UserPaymentMethods.payment_method_type.like(search),
                UserPaymentMethods.user_id.like(search),
                UserPaymentMethods.id.like(search),
                UserPaymentMethods.status.like(search),
                users.User.id.like(search),
                users.User.username.like(search),
                users.User.first_name.like(search),
                users.User.last_name.like(search),
            ),
        )

    if user_id is not None and user_id != 0:
        query = query.filter(UserPaymentMethods.user_id == user_id)

    if payment_method_type and payment_method_type != "":
        query = query.filter(
            UserPaymentMethods.payment_method_type == payment_method_type
        )

    if payment_preference_id is not None and payment_preference_id != 0:
        query = query.filter(
            UserPaymentMethods.payment_preference_id == payment_preference_id
        )
    if status and payment_preference_id != "":
        query = query.filter(UserPaymentMethods.status == status)

    if start_date is not None:
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            end_date = end_date + timedelta(days=1) - timedelta(seconds=1)

        query = query.filter(UserPaymentMethods.created_at >= start_date).filter(
            UserPaymentMethods.created_at <= end_date
        )

    if order_by and order_by != "":
        direction = asc if order_direction == "asc" else desc
        query = query.order_by(direction(getattr(UserPaymentMethods, order_by)))

    total_items = query.count()

    if page and limit:
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

    current_items = query.count()

    payment_methods = query.all()

    return {
        "page": page,
        "limit": limit,
        "items": current_items,
        "total_items": total_items,
        "payment_methods": payment_methods,
    }

def _get_pending_approved_payment_method_by_id(
    db: Session,
    _id:int,
)->UserPaymentMethods:
    return (
        db.query(UserPaymentMethods)
        .filter(
            UserPaymentMethods.id == _id,
            UserPaymentMethods.deleted_at == None,
            UserPaymentMethods.status.in_([StatusType.PENDING, StatusType.APPROVED]),
        )
        .first()
    )

def _get_user_active_payment_method_by_preferece(
    db: Session,
    preference_id,
    payment_type=None,
    is_default=None
):    
    query = db.query(UserPaymentMethods).filter(
           UserPaymentMethods.payment_preference_id == preference_id,
            UserPaymentMethods.deleted_at == None,
            UserPaymentMethods.status == StatusType.APPROVED
        )
    
    if payment_type is not None and payment_type != "":
        query = query.filter(UserPaymentMethods.payment_method_type == payment_type)
        
    if is_default is True:
        query = query.filter(UserPaymentMethods.is_default == is_default)
    record =  query.all()
    return record

def set_default_payment_method(db: Session, record: UserPaymentMethods, is_default:bool, user_id)->UserPaymentMethods:
    record.is_default = is_default
    record.updated_by = user_id
    record.updated_at = datetime.now()
    db.add(record)
    db.commit()
    db.refresh(record)
    return record