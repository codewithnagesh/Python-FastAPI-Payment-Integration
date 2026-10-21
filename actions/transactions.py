from google.protobuf.json_format import MessageToDict
from marshmallow import EXCLUDE
from datetime import datetime
import time, socket, base64, requests, json, ast
from decouple import config
import proto.invoice_proto
import proto.invoice_proto.zapier_webhook_logs
import proto.invoice_proto.zapier_webhook_logs.zapier_webhook_logs_pb2
import proto.invoice_proto.zapier_webhook_logs.zapier_webhook_logs_pb2_grpc
import proto.payments_proto.transactions.transactions_pb2
import proto.payments_proto.transactions.transactions_pb2_grpc
from helper.camel_to_snake import CamelToSnake
from helper.interceptor import RequestHeaderValidatorInterceptor
from voter.transaction import TransactionVoter
from voter.transaction_refund import TransactionRefundVoter
from sql.crud import (
    user as user_crud,
    contact as contact_crud,
    invoice as invoice_crud,
    contact_payment_profile as contact_payment_profile_crud,
    transactions as transactions_crud,
    transaction_details as transaction_detail_crud,
    transaction_refunds as transaction_refund_crud,
    transaction_refund_details as transaction_refund_detail_crud,
    transaction_settlement as transaction_settlement_crud,
    refund_items as refund_item_crud,
)
from actions.user_payment_methods import UserPaymentMethodService
from sql.models.payment_preference import PreferenceType
from sql.models.user_payment_methods import Type
from sql.schemas.transaction_details import CreateTransactionDetailsSchema
from sql.schemas.contact_payment_profile import ContactPaymentProfileSchema
from sql.schemas.transaction_refund_details import (
    RefundDetailSchema,
    CreateRefundDetailSchema,
)
from sql.schemas.transaction_settlement import CreateSettlementSchema

from sql.schemas.transactions import (
    TransactionSchema,
    CreateTransactionSchema,
)
from sql.schemas.transaction_refunds import (
    RefundProcessSchema,
    TransactionRefundSchema,
)
from sql.schemas.refund_items import CreateRefundItemsSchema
from sql.schemas.invoice import InvoiceSchema

from helper.connection import ConnectionChannel
from .utility_service import UtilityService
from .paysafe.paysafe import PaysafeService
from .authnet.authnet import AuthnetService


class TransactionService(
    proto.payments_proto.transactions.transactions_pb2_grpc.TransactionServiceServicer
):
    def __init__(self, db):
        self.__db = db
        self.__camel_to_snake = CamelToSnake()
        self.__interceptor = RequestHeaderValidatorInterceptor()
        self.__user_payment_method_service = UserPaymentMethodService(db)
        self.__transaction_schema = TransactionSchema()
        self.__transaction_schema_list = TransactionSchema(many=True)
        self.__create_transaction_schema = CreateTransactionSchema()
        self.__create_user_transaction_detail_schema = CreateTransactionDetailsSchema()
        self.__contact_payment_profile_schema = ContactPaymentProfileSchema()
        self.__refund_process_schema = RefundProcessSchema()
        self.__create_refund_detail_schema = CreateRefundDetailSchema()
        self.__create_settlement_schema = CreateSettlementSchema()
        self.__refund_schema = TransactionRefundSchema()
        self.__transaction_voter = TransactionVoter()
        self.__transaction_refund_voter = TransactionRefundVoter()
        self.__utility_service = UtilityService()
        self.__refund_items_schema = CreateRefundItemsSchema()
        self.__invoice_schema = InvoiceSchema()
        self.__paysafe_service = PaysafeService()
        self.__authnet_service = AuthnetService()
        self.unit_multiplier = int(config("PAYSAFE_CURRENCY_BASE_UNITS_MULTIPLIER"))

    def __del__(self):
        self.__db.close()

    def _getValueByKeyForArray(self, key, items):
        for item in items:
            if item.key == key:
                return item.value
        return None

    def ProfilePayment(self, request, context):
        try:
            if not self.__transaction_voter._default(self.__db, "add", None):
                raise PermissionError("Access denied!")

            user = user_crud.get_user(self.__db, request.user_id)
            if user is None:
                raise PermissionError("Invalid user id!")

            invoice = invoice_crud.get_invoice(self.__db, request.invoice_id)
            if invoice is None:
                raise PermissionError("Invalid Invoice id!")

            if invoice.paid_invoice_date != "" and (
                invoice.status == "paid"
                or invoice.status == "paid_offline"
                or invoice.status == "cancelled"
            ):
                raise PermissionError("Invoice is already paid/cancelled!")

            if not invoice.user_id == user.id:
                raise PermissionError(
                    "Invoice and user details provided do not match!"
                )

            contact_payment_profile = (
                contact_payment_profile_crud._find_by_user_id_and_payment_profile_id(
                    self.__db, user.id, invoice.payment_profile_id
                )
            )
            if contact_payment_profile is None:
                raise PermissionError("Contact payment profile does not exist!")

            payment_method = (
                self.__user_payment_method_service._approved_payment_method(
                    invoice.user, contact_payment_profile.payment_method_type
                )
            )

            if payment_method.payment_method_type == Type.AUTHNET:

                if payment_method.payment_method_options:
                    auth_login_id = self.__authnet_service.GetSecureAuthAccess("auth_transaction_key" ,self._getValueByKeyForArray(
                        "auth_login_id", payment_method.payment_method_options
                    ))
                    auth_transaction_key = self.__authnet_service.GetSecureAuthAccess("auth_transaction_key" ,self._getValueByKeyForArray(
                        "auth_transaction_key", payment_method.payment_method_options
                    ))

                payload = {
                    "apiLoginId": auth_login_id,
                    "transactionKey": auth_transaction_key,
                    "profileId": contact_payment_profile.profile_id,
                    "paymentProfileId": contact_payment_profile.payment_profile_id,
                    "refNumber": contact_payment_profile.reference_number,
                    "amount": invoice.total_invoice_amount,
                    "transactionType": "authCaptureTransaction",
                }

                response = self.__authnet_service.ChargeCustomerProfile(payload)
                payment_response = self.__paymentApi(
                    response,
                    payment_method,
                    contact_payment_profile.id,
                    invoice,
                )

                if response["messages"]["resultCode"] == "Error":
                    errorText = ""
                    if ("transactionResponse" in response and "errors" in response["transactionResponse"]):
                       errorText = response["transactionResponse"]["errors"]["error"]["errorText"]

                    error_message = response["messages"]["message"]["text"]
                    error_code = response["messages"]["message"]["code"]
                    raise PermissionError(error_code + ": " + error_message + ", " + errorText)

            elif payment_method.payment_method_type == Type.PAYSAFE:

                if payment_method.payment_method_options:
                    account_currency = self._getValueByKeyForArray(
                        "account_currency", payment_method.payment_method_options
                    )
                    account_id = self._getValueByKeyForArray(
                        "account_number", payment_method.payment_method_options
                    )
                else:
                    raise PermissionError("Unable to find Payment currency/accountId!")

                if contact_payment_profile.profile_details:
                    paymentHandleToken = self._getValueByKeyForArray(
                        "paymentHandleToken", contact_payment_profile.profile_details
                    )
                else:
                    raise PermissionError("Unable to find Payment Handle Token!")

                hostname = socket.gethostname()
                payload = {
                    "accountId": str(account_id),
                    "merchantRefNum": contact_payment_profile.reference_number,
                    "amount": int(invoice.total_invoice_amount * self.unit_multiplier),
                    "currencyCode": account_currency,
                    "dupCheck": False,  # False for recurring payment, True for duplicate chack in 90 Days
                    "settleWithAuth": True,  # For settalment
                    "paymentHandleToken": paymentHandleToken,
                    "description": f"Invoice={invoice.id}, Appointment={invoice.appointment_id}",
                    "customerIp": socket.gethostbyname(hostname),
                }

                response = self.__paysafe_service.PaymentRequestAPI(payload)
                payment_response = self.__paymentApi(
                    response.json(),
                    payment_method,
                    contact_payment_profile.id,
                    invoice,
                )
                if not response.status_code in [200, 201]:
                    data = response.json()
                    error_message = data["error"]["message"]
                    error_code = data["error"]["code"]
                    raise PermissionError(error_code + ": " + error_message)

            else:
                raise PermissionError("Invalid payment method!")

            return proto.payments_proto.transactions.transactions_pb2.PaymentResponse(
                response=json.dumps(payment_response)
            )

        except Exception as e:
            raise PermissionError(e)

    def CheckoutPayment(self, request, context):
        try:
            data = MessageToDict(request.payment_detail)

            invoice = invoice_crud.get_invoice(self.__db, data["invoiceId"])
            if invoice is None:
                raise PermissionError("Invalid Invoice id!")

            if invoice.paid_invoice_date != "" and (
                invoice.status == "paid"
                or invoice.status == "paid_offline"
                or invoice.status == "cancelled"
            ):
                raise PermissionError("Invoice is already paid/cancelled!")

            invoice_user = user_crud.get_user(self.__db, invoice.user_id)
            payment_method = (
                self.__user_payment_method_service._approved_payment_method(
                    invoice_user, request.payment_method
                )
            )
            if payment_method.payment_method_type == Type.PAYSAFE:

                if payment_method.payment_method_options:
                    account_currency = self._getValueByKeyForArray(
                        "account_currency", payment_method.payment_method_options
                    )
                    account_id = self._getValueByKeyForArray(
                        "account_number", payment_method.payment_method_options
                    )
                else:
                    raise PermissionError("Unable to find Payment currency/accountId!")

                hostname = socket.gethostname()

                payload = {
                    "accountId": str(account_id),
                    "merchantRefNum": data["merchantRefNum"],
                    "amount": int(invoice.total_invoice_amount * self.unit_multiplier),
                    "currencyCode": account_currency,
                    "dupCheck": False,  # False for recurring payment, True for duplicate chack in 90 Days
                    "settleWithAuth": True,  # For settalment
                    "paymentHandleToken": data["paymentHandleToken"],
                    "description": f"Invoice={invoice.id}, Appointment={invoice.appointment_id}",
                    "customerIp": socket.gethostbyname(hostname),
                }

                response = self.__paysafe_service.PaymentRequestAPI(payload)
                payment_response = self.__paymentApi(
                    response.json(),
                    payment_method,
                    None,
                    invoice,
                )
                if not response.status_code in [200, 201]:
                    data = response.json()
                    error_message = data["error"]["message"]
                    error_code = data["error"]["code"]
                    raise PermissionError(error_code + ": " + error_message)

            elif payment_method.payment_method_type == Type.AUTHNET:
                if payment_method.payment_method_options:
                    auth_login_id = self.__authnet_service.GetSecureAuthAccess("auth_transaction_key" ,self._getValueByKeyForArray(
                        "auth_login_id", payment_method.payment_method_options
                    ))
                    auth_transaction_key = self.__authnet_service.GetSecureAuthAccess("auth_transaction_key" ,self._getValueByKeyForArray(
                        "auth_transaction_key", payment_method.payment_method_options
                    ))

                payload = {
                    "invoiceId": invoice.id,
                    "invoiceNumber": invoice.invoice_number,
                    "invoiceDiscription": invoice.customer_note,
                    "UserId": invoice.contact_detail.id,
                    "contactType": "individual",
                    "contactEmail": invoice.contact_detail.email,
                    "firstName": invoice.contact_detail.first_name,
                    "lastName": invoice.contact_detail.last_name,
                    "apiLoginId": auth_login_id,
                    "transactionKey": auth_transaction_key,
                    "cardNumber": data.get("cardNumber", None),
                    "dataDescriptor": data["dataDescriptor"],
                    "dataValue": data["dataValue"],
                    "authPayMethod": data["authPayMethod"],
                    "amount": invoice.total_invoice_amount,
                    "transactionType": "authCaptureTransaction",
                }

                response = self.__authnet_service.ChargeCreditCard(payload)
                payment_response = self.__paymentApi(
                    response,
                    payment_method,
                    None,
                    invoice,
                )

                if response["messages"]["resultCode"] == "Error":
                    errorText = ""
                    if ("transactionResponse" in response and "errors" in response["transactionResponse"]):
                       errorText = response["transactionResponse"]["errors"]["error"]["errorText"]

                    error_message = response["messages"]["message"]["text"]
                    error_code = response["messages"]["message"]["code"]
                    raise PermissionError(error_code + ": " + error_message + ", " + errorText)
            else:
                raise PermissionError("Invalid payment method!")

            return proto.payments_proto.transactions.transactions_pb2.PaymentResponse(
                response=json.dumps(payment_response)
            )

        except Exception as e:
            raise PermissionError(e)

    def __paymentApi(
        self,
        payment_response,
        payment_method=None,
        contact_payment_profile_id=None,
        invoice=None,
    ):
        try:

            transaction = self.__createTransaction(
                payment_response,
                payment_method,
                contact_payment_profile_id,
                invoice,
            )

            if transaction and transaction.status is not None:
                invoice_status = self._updateInvoiceStatus(transaction.status)

                invoice_crud._invoice_update(
                    self.__db, invoice, invoice_status, transaction.id, True
                )
                
                if invoice_status == "paid" or invoice_status == "paid_offline":
                    # Send the invoice details to zapier as a notification (webhook).
                    channel = ConnectionChannel.grpc_invoice_channel()
                    stub = proto.invoice_proto.zapier_webhook_logs.zapier_webhook_logs_pb2_grpc.ZapierWebhookLogsServiceStub(
                        channel
                    ) 
                    stub.SendInvoiceDataToZapier(
                        proto.invoice_proto.zapier_webhook_logs.zapier_webhook_logs_pb2.SendInvoiceDataToZapierRequest( 
                            invoice_id=invoice.id
                        )
                    )
                    # Send the invoice details to zapier as a notification (webhook).

            self.__db.close()
            return payment_response

        except Exception as e:
            self.__del__()
            raise PermissionError(e)

    # Create Call
    def __createTransaction(
        self,
        request,
        payment_method,
        contact_payment_profile_id,
        invoice,
    ):
        try:
            request_data = {}

            if payment_method.payment_method_type == Type.PAYSAFE:
                request["merchantRefNum"] = request.get("merchantRefNum", None)
                request["id"] = request.get("id", None)
                request["txnTime"] = request.get("txnTime", f"{datetime.now()}")
                request["status"] = request.get("status", "FAILED")
                if "amount" in request:
                    request["amount"] = request["amount"] / self.unit_multiplier
                else:
                    request["amount"] = invoice.total_invoice_amount

            elif payment_method.payment_method_type == Type.AUTHNET:
                
                # if (
                #     request["transactionResponse"]["messages"]["message"]["code"]
                #     is not None
                # ):
                #     transCode = request["transactionResponse"]["messages"]["message"][
                #         "code"
                #     ]
                # else:
                #     transCode = request["transactionResponse"]["messages"]["code"]
                if request["transactionResponse"]["responseCode"] and request["transactionResponse"]["responseCode"] != "":
                    transCode = request["transactionResponse"]["responseCode"]
                else:
                    transCode = request["transactionResponse"]["messages"]["message"]["code"]

                request["merchantRefNum"] = request.get("refId", None)
                request["id"] = request["transactionResponse"].get("transId", None)
                request["txnTime"] = f"{datetime.now()}"
                request["status"] = self._authnetBasedTrasactionStatus(transCode)
                request["amount"] = invoice.total_invoice_amount

            request_data["payment_transaction_id"] = request["id"]
            request_data["payment_reference_number"] = request["merchantRefNum"]
            request_data["payment_method_type"] = payment_method.payment_method_type
            request_data["user_payment_method_id"] = payment_method.id
            request_data["contact_payment_profile_id"] = contact_payment_profile_id
            request_data["user_id"] = invoice.user_id
            request_data["invoice_id"] = invoice.id
            request_data["amount"] = request["amount"]
            request_data["status"] = request["status"]
            request_data["created_at"] = request["txnTime"]

            result = self.__create_transaction_schema.load(
                request_data, session=self.__db, unknown=EXCLUDE
            )
            transaction_data = transactions_crud._create(self.__db, result)

            transaction_details = []

            for key, value in request.items():
                if (
                    key != "id"
                    and key != "amount"
                    and key != "status"
                    and key != "txnTime"
                    and key != "merchantRefNum"
                ):
                    if key == "settlements":
                        settlement = {}
                        for item in value:
                            settlement["payment_method_type"] = (
                                transaction_data.payment_method_type
                            )
                            settlement["transaction_id"] = transaction_data.id
                            settlement["payment_settlement_id"] = item["id"]
                            settlement["payment_reference_number"] = item[
                                "merchantRefNum"
                            ]
                            settlement["amount"] = item["amount"] / self.unit_multiplier
                            settlement["status"] = item["status"]
                            settlement["refundable_amount"] = (
                                item["availableToRefund"] / self.unit_multiplier
                            )
                            settlement["created_at"] = (
                                transaction_data.created_at.isoformat()
                            )
                            settlement_data = self.__create_settlement_schema.load(
                                settlement, session=self.__db, unknown=EXCLUDE
                            )
                            transaction_settlement_crud._create(
                                self.__db, settlement_data
                            )
                    else:
                        transaction_details.append({"key": key, "value": str(value)})

            for transaction_detail in transaction_details:
                transaction_detail["transaction_id"] = transaction_data.id
                transaction_detail["created_at"] = request["txnTime"]
                result = self.__create_user_transaction_detail_schema.load(
                    transaction_detail, session=self.__db, unknown=EXCLUDE
                )
                transaction_detail_crud._create(self.__db, result)

            return transaction_data
        except Exception as e:
            self.__del__()
            raise PermissionError(e)

    # Get Call
    def ReadTransaction(self, request, context):
        try:
            transaction = transactions_crud._get_by_id(self.__db, request.id)
            if not transaction:
                raise PermissionError("Transaction not found!")

            if not self.__transaction_voter._default(self.__db, "view", transaction):
                raise PermissionError("Access denied!")

            result = self.__transaction_schema.dump(transaction)
            self.__db.close()
            return proto.payments_proto.transactions.transactions_pb2.ReadTransactionResponse(
                transaction=result
            )
        except Exception as e:
            self.__del__()
            raise PermissionError(e)

    def RefundTransaction(self, request, context):
        try:
            if not self.__transaction_refund_voter._default(self.__db, "add", None):
                raise PermissionError("Access denied!")
            transaction = transactions_crud._get_by_id(
                self.__db, request.transaction_id
            )
            if not transaction:
                raise PermissionError("Transaction details found for the refund!")

            if request.payment_method_type == transaction.payment_method_type:
                if request.payment_method_type == Type.PAYSAFE:
                    if transaction.status == "COMPLETED":
                        settlement = (
                            transaction_settlement_crud._find_by_transaction_id(
                                self.__db, transaction.id
                            )
                        )
                        if settlement and settlement.status == "COMPLETED":
                            request_amount = round(request.amount, 2)
                            refund_transaction = self._refundProcessPaysafeApi(
                                transaction, settlement, request_amount
                            )

                            self.__db.close()
                            return proto.payments_proto.transactions.transactions_pb2.RefundTransactionResponse(
                                response=json.dumps(refund_transaction)
                            )
                        else:
                            raise PermissionError(
                                "Settlement details could not be found for this transaction or settlement was not completed!"
                            )
                    else:
                        raise PermissionError(
                            "Transaction is not completed please wait!"
                        )
                else:  ## elif when we will put more payment method
                    raise PermissionError(
                        "Transaction method type and method not active!"
                    )
            else:
                raise PermissionError("Transaction method type not metched!")
        except Exception as e:
            self.__del__()
            raise PermissionError(e)

    def ReadRefund(self, request, context):
        refund_details = self._readRefundPaysafeApiDetails(request.refund_id)
        return proto.payments_proto.transactions.transactions_pb2.ReadRefundResponse(
            response=json.dumps(refund_details)
        )

    def CancelRefund(self, request, context):
        try:
            refund_record = transaction_refund_crud._find_by_id(self.__db, request.id)
            if not refund_record:
                raise PermissionError("Provided details not found!")

            if refund_record.status.upper() == "CANCELLED":
                raise PermissionError(
                    "Your requested record has already been cancelled!"
                )
            elif refund_record.status.upper() == "COMPLETED":
                raise PermissionError(
                    "Your requested record has already been refunded!"
                )

            if not self.__transaction_refund_voter._default(
                self.__db, "cancel", refund_record
            ):
                raise PermissionError("Access denied!")

            logged_in_user = self.__interceptor._get_logged_in_user()
            t_user_id = refund_record.transaction.user.id

            if (
                logged_in_user.id != refund_record.transaction.user.id
            ):
                raise PermissionError("You are not authorized to perform this action!")

            refund_details = self._cancelRefundPaysafeApi(
                refund_record.payment_refund_id
            )

            transaction_refund = transaction_refund_crud._update(
                self.__db, refund_record, refund_details["status"]
            )
            if transaction_refund:
                self.__utility_service.get_settlement_by_transaction_id(
                    self.__db, transaction_refund.transaction_id
                )
                transaction_refund_details = []
                for key, value in refund_details.items():
                    if (
                        key != "id"
                        and key != "amount"
                        and key != "status"
                        and key != "txnTime"
                        and key != "merchantRefNum"
                    ):
                        transaction_refund_details.append(
                            {"key": key, "value": str(value)}
                        )

                for transaction_refund_detail in transaction_refund_details:
                    if transaction_refund_detail is not None:
                        transaction_refund_detail["transaction_refund_id"] = (
                            transaction_refund.id
                        )
                        transaction_refund_detail["created_at"] = (
                            transaction_refund.updated_at.isoformat()
                        )
                        result = self.__create_refund_detail_schema.load(
                            transaction_refund_detail,
                            session=self.__db,
                            unknown=EXCLUDE,
                        )
                        transaction_refund_detail_crud._create(self.__db, result)

                return proto.payments_proto.transactions.transactions_pb2.CancelRefundResponse(
                    response=json.dumps(refund_details)
                )
        except Exception as e:
            self.__del__()
            raise PermissionError(e)

    def _refundProcessPaysafeApi(self, transaction, settlement, amount, refund_items = None):
        try:
            params = {
                "merchantRefNum": settlement.payment_reference_number,
                "amount": int(amount * self.unit_multiplier),
                "dupCheck": False,
            }

            response = self.__paysafe_service.RefundProcessApi(
                settlement.payment_settlement_id, params
            )
            refund_transaction = response.json()

            self._addRefundDetail(refund_transaction, transaction, settlement, amount, refund_items)

            if not response.status_code in [200, 201]:
                data = response.json()
                error_message = data["error"]["message"]
                error_code = data["error"]["code"]
                raise PermissionError(error_code + ": " + error_message)
            else:
                return refund_transaction
        except Exception as e:
            self.__del__()
            raise PermissionError(e)

    # Get Refund transaction by refundId
    def _readRefundPaysafeApiDetails(self, refund_id):
        try:
            response = self.__paysafe_service.ReadRefundPaysafeAPI(refund_id)
            if not response.status_code in [200, 201]:
                data = response.json()
                error_message = data["error"]["message"]
                error_code = data["error"]["code"]
                raise PermissionError(error_code + ": " + error_message)
            else:
                refund_transaction = response.json()
            return refund_transaction

        except Exception as e:
            self.__del__()
            raise PermissionError(e)

    # Cancel Refund transaction paymenthub/v1/refunds/{refundId}
    def _cancelRefundPaysafeApi(self, refund_id):
        try:
            payload = {"status": "CANCELLED"}

            response = self.__paysafe_service.CancelRefundProcessApi(refund_id, payload)
            if not response.status_code in [200, 201]:
                data = response.json()
                error_message = data["error"]["message"]
                error_code = data["error"]["code"]
                raise PermissionError(error_code + ": " + error_message)
            else:
                refund_transaction = response.json()
            return refund_transaction

        except Exception as e:
            self.__del__()
            raise PermissionError(e)

    # Get Refund transaction /paymenthub/v1/refunds?merchantRefNum=45"
    def _listRefundPaysafeApi(self, merchantRefNum):
        try:
            response = self.__paysafe_service.ListRefundPaysafeApi(merchantRefNum)
            if not response.status_code in [200, 201]:
                data = response.json()
                error_message = data["error"]["message"]
                error_code = data["error"]["code"]
                raise PermissionError(error_code + ": " + error_message)
            else:
                refund_transactions = response.json()
            return refund_transactions

        except Exception as e:
            self.__del__()
            raise PermissionError(e)

    def ReadRefundByTransactionId(self, request, context):
        transaction = transactions_crud._get_by_id(self.__db, request.transaction_id)

        if not transaction:
            raise PermissionError("Provided transaction details mismatched!")

        refund = transaction_refund_crud._find_by_transaction_id(
            self.__db, transaction.id
        )

        if not self.__transaction_refund_voter._default(self.__db, "view", refund):
            raise PermissionError("Access denied!")

        if not refund:
            raise PermissionError("Refund not found!")
        refund = self.__refund_schema.dump(refund)
        return proto.payments_proto.transactions.transactions_pb2.ReadRefundByTransactionIdResponse(
            refund=refund
        )

    def ListTransactions(self, request, context):
        try:
            logged_in_user = self.__interceptor._get_logged_in_user()
            user_id = request.user_id

            start_date = None
            if hasattr(request, "start_date"):
                if request.start_date != "":
                    start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
            end_date = None
            if hasattr(request, "end_date"):
                if request.end_date != "":
                    end_date = datetime.strptime(request.end_date, "%Y-%m-%d")

            transactions = transactions_crud.get_all_transactions(
                self.__db,
                filter=request.filter,
                order_by=request.order_by,
                order_direction=request.order_direction,
                payment_method_type=request.payment_method_type,
                user_id=user_id,
                user_payment_method_id=request.user_payment_method_id,
                contact_payment_profile_id=request.contact_payment_profile_id,
                invoice_id=request.invoice_id,
                page=request.page,
                limit=request.limit,
                start_date=start_date,
                end_date=end_date,
            )

            transaction_list = []
            if "transaction_list" in transactions:
                transaction_list = self.__transaction_schema_list.dump(
                    transactions["transaction_list"]
                )

            meta = {
                "page": transactions["page"],
                "limit": transactions["limit"],
                "current_items": transactions["item"],
                "total_items": transactions["total_items"],
            }

            return proto.payments_proto.transactions.transactions_pb2.ListTransactionsResponse(
                meta=meta, transactions=transaction_list
            )

        except Exception as e:
            self.__del__()
            raise PermissionError(e)

    # Read Settlement by Transaction Id
    def ReadSettlementByTransactionId(self, request, context):
        try:
            transaction = transactions_crud._get_by_id(
                self.__db, request.transaction_id
            )

            if not transaction:
                raise PermissionError("Provided transaction details mismatched!")

            if not self.__transaction_voter._default(self.__db, "view", transaction):
                raise PermissionError("Access denied!")

            if transaction.status != "COMPLETED":
                raise PermissionError("Your transaction is not completed!")

            if transaction.payment_method_type == Type.PAYSAFE:
                settlement = self.__utility_service.get_settlement_by_transaction_id(self.__db, transaction.id)

            elif transaction.payment_method_type == Type.AUTHNET:
                payment_method = self.__user_payment_method_service._approved_payment_method(transaction.user, transaction.payment_method_type)

                if payment_method.payment_method_options:
                    auth_login_id = self.__authnet_service.GetSecureAuthAccess("auth_transaction_key" ,self._getValueByKeyForArray(
                        "auth_login_id", payment_method.payment_method_options
                    ))
                    auth_transaction_key = self.__authnet_service.GetSecureAuthAccess("auth_transaction_key" ,self._getValueByKeyForArray(
                        "auth_transaction_key", payment_method.payment_method_options
                    ))

                payload = {
                    "apiLoginId": auth_login_id,
                    "transactionKey": auth_transaction_key,
                    "refTransId": transaction.payment_transaction_id,
                }
                settlement = self.__authnet_service.ReadTransactionInfo(payload)

            elif transaction.payment_method_type == Type.JUPITER:
                return True
            else:
                raise PermissionError("Unsupported payment method type!")

            return proto.payments_proto.transactions.transactions_pb2.ReadSettlementByTransactionIdResponse(
                settlement=json.dumps(settlement)
            )

        except Exception as e:
            self.__del__()
            raise PermissionError(e)

    # Add Refund Details
    def _addRefundDetail(self, refund_transaction, transaction, settlement=None, amount=None, refund_items=None):
        logged_in_user = self.__interceptor._get_logged_in_user()
        if transaction.payment_method_type == Type.PAYSAFE:
            refund_transaction["merchantRefNum"] = refund_transaction.get("merchantRefNum", settlement.payment_reference_number)
            refund_transaction["id"] = refund_transaction.get("id", None)
            refund_transaction["txnTime"] = refund_transaction.get("txnTime", f"{datetime.now()}")
            refund_transaction["status"] = refund_transaction.get("status", "FAILED")
            refund_transaction["transaction_settlement_id"] = settlement.id
            if "amount" in refund_transaction:
                refund_transaction["amount"] = (refund_transaction["amount"] / self.unit_multiplier)
            else:
                refund_transaction["amount"] = amount

        elif transaction.payment_method_type == Type.AUTHNET:
            if refund_transaction["transactionResponse"]["responseCode"] is not None:
                transCode = refund_transaction["transactionResponse"]["responseCode"]
            else:
                transCode = refund_transaction["transactionResponse"]["messages"][
                    "message"
                ]["code"]
            refund_transaction["merchantRefNum"] = refund_transaction.get("refId", None)
            refund_transaction["id"] = refund_transaction["transactionResponse"].get(
                "transId", None
            )
            refund_transaction["txnTime"] = f"{datetime.now()}"
            refund_transaction["status"] = self._authnetBasedTrasactionStatus(transCode)
            refund_transaction["amount"] = amount

        refund_details = {
            "payment_refund_id": refund_transaction["id"],
            "payment_method_type": transaction.payment_method_type,
            "transaction_id": transaction.id,
            "transaction_settlement_id": refund_transaction.get("transaction_settlement_id", None),
            "status": refund_transaction["status"],
            "amount": refund_transaction["amount"],
            "invoice_id":transaction.invoice_id,
            "reference_number": refund_transaction["merchantRefNum"],
            "created_by": logged_in_user.id,
            "created_at": refund_transaction["txnTime"],
        }
        refund_process = self.__refund_process_schema.load(
            refund_details, session=self.__db, unknown=EXCLUDE
        )
        refund_data = transaction_refund_crud._create(self.__db, refund_process)
        if refund_data:
            transaction_refund_details = []
            for key, value in refund_transaction.items():
                if (
                    key != "id"
                    and key != "amount"
                    and key != "status"
                    and key != "txnTime"
                    and key != "merchantRefNum"
                    and key != "transaction_settlement_id"
                ):
                    transaction_refund_details.append({"key": key, "value": str(value)})

            for transaction_refund_detail in transaction_refund_details:
                if transaction_refund_detail is not None:
                    transaction_refund_detail["transaction_refund_id"] = refund_data.id
                    transaction_refund_detail["created_at"] = (
                        refund_data.created_at.isoformat()
                    )
                    result = self.__create_refund_detail_schema.load(
                        transaction_refund_detail,
                        session=self.__db,
                        unknown=EXCLUDE,
                    )
                    transaction_refund_detail_crud._create(self.__db, result)

            if refund_items is not None and len(refund_items) > 0:
                self._addRefundItems(self.__db, refund_items, refund_data)
        return refund_data

    # Update Invoice status based in transaction
    def _authnetBasedTrasactionStatus(self, code):
        if code == "1":
            return "COMPLETED"  # "APPROVED"
        elif code == "2":
            return "DECLINED"
        elif code == "4":
            return "IN PROGRESS"
        else:
            return "FAILED"

    def _updateInvoiceStatus(self, status):
        invoice_status = ""
        if status.lower() == "completed" or status.lower() == "Successful.":
            invoice_status = "paid"
        elif status.lower() == "pending":
            invoice_status = "pending_transaction"
        elif status.lower() == "failed":
            invoice_status = "failed_transaction"
        elif status.lower() == "authorized":
            invoice_status = "pending_transaction"
        elif status.lower() == "pending_approval":
            invoice_status = "pending_transaction"
        elif status.lower() == "declined":
            invoice_status = "failed_transaction"
        elif status.lower() == "refunded":
            invoice_status = "refunded_transaction"
        elif status.lower() == "canceled":
            invoice_status = "failed_transaction"
        elif status.lower() == "in progress":
            invoice_status = "panding_transaction"
        elif status.lower() == "settled":
            invoice_status = "paid"
        else:
            invoice_status = "pending_transaction"

        return invoice_status

    def PartiallyRefundInvoiceItems(self, request, context):
        try:
            request_data = self.__camel_to_snake._decode_keys(
                MessageToDict(request.refund_invoice)
            )

            transaction = transactions_crud._get_by_id(
                self.__db, request.transaction_id
            )

            if not transaction:
                raise PermissionError("Provided transaction details mismatched!")

            if not self.__transaction_voter._default(self.__db, "view", transaction):
                raise PermissionError("Access denied!")

            invoice = invoice_crud.get_invoice(self.__db, request_data["id"])

            if invoice and transaction.invoice_id != invoice.id:
                raise PermissionError(
                    "Provided invoice details mismatched with transaction details!"
                )

            invoice_data = self.__invoice_schema.dump(invoice)

            if "tax_rate" not in invoice_data:
                invoice_data["tax_rate"] == 0
            response = self.__utility_service._invoice_comparission(
                self.__db, invoice_data, request_data
            )

            transaction = transactions_crud._get_by_id(
                self.__db, invoice_data["payment_transaction_id"]
            )

            if len(response["invoice_items"]) == 0:
                raise PermissionError("Please provice valid return item details!")

            refund_amount = response["total_refund_amount"]
            if refund_amount and refund_amount != request_data["total_refund_amount"]:
                raise PermissionError("Provided total refund amount mismatched!")

            if transaction.payment_method_type == Type.AUTHNET:
                payment_method = (
                    self.__user_payment_method_service._approved_payment_method(
                        invoice.user, transaction.payment_method_type
                    )
                )

                if payment_method.payment_method_options:
                    auth_login_id = self.__authnet_service.GetSecureAuthAccess("auth_transaction_key" ,self._getValueByKeyForArray(
                        "auth_login_id", payment_method.payment_method_options
                    ))
                    auth_transaction_key = self.__authnet_service.GetSecureAuthAccess("auth_transaction_key" ,self._getValueByKeyForArray(
                        "auth_transaction_key", payment_method.payment_method_options
                    ))

                payload = {
                    "apiLoginId": auth_login_id,
                    "transactionKey": auth_transaction_key,
                    "refTransId": transaction.payment_transaction_id,
                    "transaction_amount": transaction.amount,
                    "amount": round(refund_amount, 2),
                    "transactionType": "refundTransaction",
                    "authPayMethod": "creditCard"
                }
                
                refund_response = self.__authnet_service.RefundTransaction(payload)
                
                self._addRefundDetail(
                    refund_response,
                    transaction=transaction,
                    amount=refund_amount,
                    refund_items=response["invoice_items"],
                )
                if refund_response["messages"]["resultCode"] == "Error":
                    errorText = ""
                    if ("transactionResponse" in refund_response and "errors" in refund_response["transactionResponse"]):
                       errorText = refund_response["transactionResponse"]["errors"]["error"]["errorText"]

                    error_message = refund_response["messages"]["message"]["text"]
                    error_code = refund_response["messages"]["message"]["code"]
                    
                    raise PermissionError(error_code + ": " + error_message + ", " + errorText)
                
                return proto.payments_proto.transactions.transactions_pb2.RefundTransactionResponse(
                    response=json.dumps(refund_response)
                )
            elif transaction.payment_method_type == Type.PAYSAFE:

                settlement = transaction_settlement_crud._find_by_transaction_id(
                    self.__db, transaction.id
                )
                if settlement:
                    if settlement.status == "COMPLETED":
                        request_amount = round(refund_amount, 2)
                        refund_response = self._refundProcessPaysafeApi(
                           transaction, settlement, request_amount, response["invoice_items"]
                        )

                        return proto.payments_proto.transactions.transactions_pb2.RefundTransactionResponse(
                            response=json.dumps(refund_response)
                        )
                    else:
                        raise PermissionError("Settlement has not completed!")
                else:
                    raise PermissionError(
                        "Settlement details has not found for this transaction!"
                    )
            else:
                raise PermissionError("Unsupported payment method!")

        except Exception as e:
            self.__del__()
            raise PermissionError(e)

    def _addRefundItems(self, db, refund_items, refund_data):
        for item in refund_items:
            refund_items = {
                "transaction_refund_id": refund_data.id,
                "invoice_item_id": item.get("id", None),
                "quantity": item.get("quantity", 0),
                "price": item.get("price", 0),
                "tax_rate": item.get("tax_rate", 0),
                "is_taxable": item.get("is_taxable", False),
                "total_amount": item.get("total_amount", 0),
                "created_at": refund_data.created_at.isoformat(),
            }
            refund_item = self.__refund_items_schema.load(
                refund_items, session=db, unknown=EXCLUDE
            )
            refund_item_crud._create(db, refund_item)
        return True
