# This module defines CRUD (Create, Read, Update, Delete) operations for transactions
# in the payment API service. It provides database operations for managing transaction records.

from sqlalchemy.orm import Session  # SQLAlchemy session for database operations
from datetime import timedelta  # For date/time calculations
from sql.models.transactions import Transactions  # Transactions model
from sqlalchemy import or_, desc, asc  # SQLAlchemy query operators
from sql.models import users, invoice  # Related models for joins


def _create(db: Session, data: Transactions):
    """
    Creates a new transaction record in the database.
    
    Args:
        db (Session): Database session
        data (Transactions): Transaction data to create
        
    Returns:
        Transactions: The created transaction record
    """
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


def _get_by_id(db: Session, _id):
    """
    Retrieves a transaction by its ID.
    
    Args:
        db (Session): Database session
        _id (int): Transaction ID to search for
        
    Returns:
        Transactions: The transaction record if found, None otherwise
    """
    return db.query(Transactions).filter(Transactions.id == _id).first()


def _get_by_payment_transaction_id(db: Session, _payment_transaction_id):
    """
    Retrieves a transaction by the external payment processor's transaction ID.
    
    Args:
        db (Session): Database session
        _payment_transaction_id (str): External payment processor's transaction ID
        
    Returns:
        Transactions: The most recent transaction with the given payment transaction ID
    """
    return (
        db.query(Transactions)
        .filter(Transactions.payment_transaction_id == _payment_transaction_id)
        .order_by(desc(Transactions.id))
        .first()
    )


def _get_by_payment_merchantRefNum(db: Session, _merchant_ref_num):
    """
    Retrieves a transaction by merchant reference number.
    
    Args:
        db (Session): Database session
        _merchant_ref_num (str): Merchant reference number to search for
        
    Returns:
        Transactions: The transaction record if found, None otherwise
    """
    return (
        db.query(Transactions)
        .filter(Transactions.payment_reference_number == _merchant_ref_num)
        .first()
    )


# # Update
def _update(db: Session, record: Transactions, result: Transactions):
    if hasattr(result, "status") and result.status != "":
        record.status = result.status

        record.updated_at = result.updated_at
        db.add(record)
        db.commit()
        db.refresh(record)
        return record


def _get_by_paysafe_transactions_id_or_reference_number(
    db: Session, payment_transaction_id, reference_number
) -> Transactions:
    return (
        db.query(Transactions)
        .filter(
            or_(
                Transactions.payment_transaction_id == payment_transaction_id,
                Transactions.payment_reference_number == reference_number,
            )
        )
        .order_by(desc(Transactions.id))
        .first()
    )


# Delete
def _delete(db: Session, record: Transactions):
    db.delete(record)
    db.commit()
    return True


# Check user_payment_method_id in table
def check_user_payment_method_id(db: Session, _id):
    return (
        db.query(Transactions)
        .filter(Transactions.user_payment_method_id == _id)
        .first()
    )


# Check contact_payment_profile_id in table
def check_contact_payment_profile_id(db: Session, _id):
    return (
        db.query(Transactions)
        .filter(Transactions.contact_payment_profile_id == _id)
        .first()
    )


# Get Transaction listing
def get_all_transactions(
    db: Session,
    filter=None,
    order_by=None,
    order_direction=None,
    payment_method_type=None,
    user_id=None,
    user_payment_method_id=None,
    contact_payment_profile_id=None,
    invoice_id=None,
    page: int = 1,
    limit=25,
    start_date=None,
    end_date=None,
) -> list:
    query = (
        db.query(Transactions)
        .join(users.User, users.User.id == Transactions.user_id)
        .join(invoice.Invoice, invoice.Invoice.id == Transactions.invoice_id)
    )
    if filter:
        if filter is not None and filter != "":
            inv = filter.lower().strip()
            if "inv-" in inv:
                filter = inv.replace("inv-", "")
                search = "%{}%".format(filter)
            else:
                search = "%{}%".format(filter.strip())
            query = query.filter(
                or_(
                    Transactions.id.like(search),
                    Transactions.payment_method_type.like(search),
                    Transactions.payment_transaction_id.like(search),
                    Transactions.user_payment_method_id.like(search),
                    Transactions.payment_reference_number.like(search),
                    Transactions.amount.like(search),
                    Transactions.status.like(search),
                    users.User.id.like(search),
                    users.User.first_name.like(search),
                    users.User.last_name.like(search),
                    users.User.username.like(search),
                    invoice.Invoice.id.like(search),
                    invoice.Invoice.invoice_number.like(search),
                )
            )
    if payment_method_type:
        query = query.filter(Transactions.payment_method_type == payment_method_type)

    if user_id and user_id > 0:
        query = query.filter(Transactions.user_id == user_id)

    if user_payment_method_id and user_payment_method_id > 0:
        query = query.filter(
            Transactions.user_payment_method_id == user_payment_method_id
        )

    if contact_payment_profile_id and contact_payment_profile_id > 0:
        query = query.filter(
            Transactions.contact_payment_profile_id == contact_payment_profile_id
        )

    if invoice_id and invoice_id > 0:
        query = query.filter(Transactions.invoice_id == invoice_id)

    if start_date is not None:
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            end_date = end_date + timedelta(days=1) - timedelta(seconds=1)

        query = query.filter(Transactions.created_at >= start_date).filter(
            Transactions.created_at <= end_date
        )
    if order_by is not None and order_by != "":
        direction = asc if order_direction == "asc" else desc
        if order_by == "invoice_number":
            query = query.order_by(direction(invoice.Invoice.invoice_number))
        elif order_by == "username":
            query = query.order_by(direction(users.User.username))
        elif order_by == "user_name":
            query = query.order_by(direction(users.User.first_name))
        else:
            query = query.order_by(direction(getattr(Transactions, order_by)))

    total_items = query.count()

    if page and limit:
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

    current_items = query.count()

    transaction_list = query.all()

    return {
        "limit": limit,
        "page": page,
        "item": current_items,
        "total_items": total_items,
        "transaction_list": transaction_list,
    }
