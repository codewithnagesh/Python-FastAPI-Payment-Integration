from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from sql.models.user_payment_method_approvals import UserPaymentMethodApproval
from datetime import datetime
from enumerations.user_payment_method_approvals import StatusType, PaymentType


def _create(db: Session, data: UserPaymentMethodApproval):
    db.add(data)
    db.commit()
    db.refresh(data)
    return True


def _get_by_id(db: Session, _id):
    return (
        db.query(UserPaymentMethodApproval)
        .filter(UserPaymentMethodApproval.id == _id)
        .first()
    )


def _get_by_user_and_method(db: Session, user_id, method):
    return (
        db.query(UserPaymentMethodApproval)
        .filter(
            UserPaymentMethodApproval.user_id == user_id,
            UserPaymentMethodApproval.payment_method_type == method,
        )
        .first()
    )


def _get_approvals_by_user(db: Session, user_id)->list:
    return (
        db.query(UserPaymentMethodApproval)
        .filter(
            UserPaymentMethodApproval.user_id == user_id,
            UserPaymentMethodApproval.status == StatusType.APPROVED,
        )
        .all()
    )


def _set_default(db: Session, approval: UserPaymentMethodApproval, is_default):
    approval.is_default = is_default
    db.add(approval)
    db.commit()
    db.refresh(approval)

def _is_approved_user(db: Session, user_id, method):
    return (
        db.query(UserPaymentMethodApproval)
        .filter(
            UserPaymentMethodApproval.user_id == user_id,
            UserPaymentMethodApproval.payment_method_type == method,
            UserPaymentMethodApproval.status == StatusType.APPROVED,
        )
        .first()
    )


def check_user(db: Session, user_id):
    return (
        db.query(UserPaymentMethodApproval)
        .filter(UserPaymentMethodApproval.user_id == user_id)
        .first()
    )


def _check_approval_by_user(db: Session, user_id, payment_method_type):
    return (
        db.query(UserPaymentMethodApproval)
        .filter(UserPaymentMethodApproval.user_id == user_id)
        .filter(UserPaymentMethodApproval.payment_method_type == payment_method_type)
        .first()
    )


def _edit_status(
    db: Session, record: UserPaymentMethodApproval, result: UserPaymentMethodApproval
):
    if hasattr(result, "status"):
        current_date = datetime.now()
        if result.status == StatusType.APPROVED:
            record.approved_at = current_date
        record.status = result.status
        record.updated_at = current_date

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# Get all approvals list
def _get_all_approvals_list(
    db: Session,
    filter=None,
    order_by="id",
    order_direction="asc",
    limit=25,
    page=1,
    user_id: int = None,
    payment_method_type=None,
    status=None,
    is_default: str = ""
):
    query = db.query(UserPaymentMethodApproval)

    # short by payment_method_type
    if filter is not None and filter != "":
        search = filter
        query = query.filter(UserPaymentMethodApproval.status.contains(search))

    # short order_by
    if order_by is not None and order_by != "":
        if order_direction == "asc":
            query = query.order_by(
                asc(
                    getattr(
                        UserPaymentMethodApproval,
                        order_by,
                    )
                )
            )
        else:
            query = query.order_by(
                desc(
                    getattr(
                        UserPaymentMethodApproval,
                        order_by,
                    )
                )
            )

    # filter by payment_method_type
    if payment_method_type is not None and payment_method_type != "":
        query = query.filter(
            UserPaymentMethodApproval.payment_method_type == payment_method_type
        )

    # filter by status
    if status is not None and status != "":
        query = query.filter(UserPaymentMethodApproval.status == status)

    # filter by user_id
    if user_id is not None and user_id != 0:
        query = query.filter(UserPaymentMethodApproval.user_id == user_id)

    if is_default and is_default != "":
        default = True if is_default == "true" else False
        query = query.filter(UserPaymentMethodApproval.is_default == default)
    
    total_items = query.count()

    if limit is not None:
        query = query.limit(limit)
        offset = (int(page) - 1) * limit
        query = query.offset(offset)

    current_items = query.count()

    approvals_list = query.all()

    return {
        "limit": limit,
        "page": page,
        "item": current_items,
        "total_items": total_items,
        "approvals_list": approvals_list,
    }

def read_approved_payment_methods(db: Session, user_id):
    return (
        db.query(UserPaymentMethodApproval)
        .filter(
            UserPaymentMethodApproval.user_id == user_id,
            UserPaymentMethodApproval.status == StatusType.APPROVED,
        )
        .all()
    )