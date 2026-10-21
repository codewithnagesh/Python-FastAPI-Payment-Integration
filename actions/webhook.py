# This module defines the WebhookService class, which handles webhook processing
# for payment events from Paysafe, including transaction updates, settlement notifications,
# and refund processing through webhook callbacks.

import json  # For JSON data processing
import proto.payments_proto.paysafe_webhook.paysafe_webhook_pb2_grpc  # Paysafe webhook gRPC definitions
import proto.payments_proto.paysafe_webhook.paysafe_webhook_pb2  # Paysafe webhook protobuf definitions
import proto.invoice_proto.zapier_webhook_logs.zapier_webhook_logs_pb2  # Zapier webhook protobuf definitions
import proto.invoice_proto.zapier_webhook_logs.zapier_webhook_logs_pb2_grpc  # Zapier webhook gRPC definitions
from marshmallow import EXCLUDE  # Used for schema validation
from datetime import datetime  # For date and time operations
from helper.connection import ConnectionChannel  # gRPC connection management
from sql.crud import (
    webhook,  # CRUD operations for webhook data
    transactions as transactions_crud,  # CRUD operations for transactions
    transaction_details as transaction_detail_crud,  # CRUD operations for transaction details
    transaction_refunds as transaction_refund_crud,  # CRUD operations for refunds
    transaction_refund_details as transaction_refund_detail_crud,  # CRUD operations for refund details
    transaction_settlement as transaction_settlement_crud,  # CRUD operations for settlements
    invoice as invoice_crud,  # CRUD operations for invoices
)
from sql.schemas.transaction_details import CreateTransactionDetailsSchema  # Schema for transaction details
from sql.schemas.transactions import TransactionSchema, UpdateTransactionSchema  # Schemas for transactions
from sql.schemas.transaction_refund_details import CreateRefundDetailSchema  # Schema for refund details
from ..utility_service import UtilityService  # Utility service for payment operations


class WebhookService(
    proto.payments_proto.paysafe_webhook.paysafe_webhook_pb2_grpc.WebhookServiceServicer
):
    """
    gRPC service for processing Paysafe webhook events.
    
    This service handles incoming webhook notifications from Paysafe for various
    payment events including transactions, settlements, and refunds.
    """
    
    def __init__(self, db):
        """
        Initializes the WebhookService with the required dependencies.
        
        Args:
            db: The database session object for performing database operations.
        """
        self.__db = db  # Database session
        self.__transaction_schema = TransactionSchema()  # Schema for transaction data
        self.__create_transaction_detail_schema = CreateTransactionDetailsSchema()  # Schema for creating transaction details
        self.__update_transaction_schema = UpdateTransactionSchema()  # Schema for updating transactions
        self.__create_refund_detail_schema = CreateRefundDetailSchema()  # Schema for creating refund details
        self.__utility_service = UtilityService()  # Utility service for payment operations

    def __del__(self):
        """
        Destructor to ensure the database session is closed when the service is destroyed.
        """
        self.__db.close()

    def CreateWebhook(self, request, context):
        data = request.message
        webhook._create(self.__db, str(data))
        self.__db.close()
        return proto.payments_proto.paysafe_webhook.paysafe_webhook_pb2.CreateWebhookResponse(
            message="Webhook created successfully"
        )

    def PaysafeWebhookInfo(self, request, context):
        request_body = json.loads(request.webhook_response)
        if request_body is not None and "type" in request_body:
            if request_body["type"].lower() == "settlement":
                self._updateTransactionSettlementInfo(request_body)
            elif request_body["type"].lower() == "refund":
                self._updateRefundTransactionInfo(request_body)
            elif request_body["type"].lower() == "payment":
                self._updateTransactionInfo(request_body)
            else:
                raise PermissionError("Invalid webhook configration!")
        else:
            raise PermissionError("Invalid webhook request!")

        return proto.payments_proto.paysafe_webhook.paysafe_webhook_pb2.PaysafeWebhookInfoResponse(
            webhook_response=request.webhook_response
        )

    # Update Call
    def _updateTransactionInfo(self, param):
        try:
            payload_data = param["payload"]
            record = transactions_crud._get_by_payment_transaction_id(
                self.__db, payload_data["id"]
            )
            if not record:
                record = transactions_crud._get_by_payment_merchantRefNum(
                    self.__db, payload_data["merchantRefNum"]
                )
                if not record:
                    raise PermissionError("Transaction Record not found!")

            payload_data["updated_at"] = payload_data["txnTime"]

            result = self.__update_transaction_schema.load(
                payload_data, session=self.__db, unknown=EXCLUDE
            )

            result_up = transactions_crud._update(self.__db, record, result)
            invoice = invoice_crud.get_invoice(self.__db, result_up.invoice_id)
            if invoice :
                invoice_status = self._updateInvoiceStatus(result_up.status)
                invoice_crud._invoice_update(self.__db, invoice, invoice_status, result_up.id, True)

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

            del payload_data["updated_at"]
            param["source"] = param["payload"]["source"]
            for key, value in param.items():
                if key == "attemptNumber" or key == "type" or key == "source":
                    transaction_detail = {
                        "transaction_id": record.id,
                        "key": key,
                        "value": str(value),
                        "created_at": payload_data["txnTime"],
                    }
                    result = self.__create_transaction_detail_schema.load(
                        transaction_detail, session=self.__db, unknown=EXCLUDE
                    )
                    transaction_detail_crud._create(self.__db, result)

            del param["source"]
            return True
        except Exception as e:
            self.__del__()
            raise PermissionError(e)
        
    def _updateInvoiceStatus(self, status):
        invoice_status = ""
        if status.lower() == "completed":
            invoice_status = "paid"
        elif status.lower() == "pending":
            invoice_status = "pending_transaction" 
        elif status.lower() == "failed":
            invoice_status = "failed_transaction"  
        elif status.lower() == "authorized":
            invoice_status = "pending_transaction"  
        elif status.lower() == "pending approval":
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

    def _updateRefundTransactionInfo(self, param):
        try:
            payload = param["payload"]
            record = transaction_refund_crud._find_by_payment_refund_id(
                self.__db, payload["id"]
            )
            if not record:
                raise PermissionError("Record Not Found!")

            refund = transaction_refund_crud._update(
                self.__db, record, payload["status"]
            )
            if refund is not None:
                self.__utility_service.get_settlement_by_transaction_id(
                    self.__db, refund.transaction_id
                )
                for key, value in param.items():
                    if key != "payload":
                        refund_detail = {
                            "transaction_refund_id": refund.id,
                            "key": key,
                            "value": str(value),
                            "created_at": refund.updated_at.isoformat(),
                        }
                        result = self.__create_refund_detail_schema.load(
                            refund_detail, session=self.__db, unknown=EXCLUDE
                        )
                        transaction_refund_detail_crud._create(
                            self.__db,
                            result,
                        )
                return True
            else:
                return False
        except Exception as e:
            self.__del__()
            raise PermissionError(e)

    def _updateTransactionSettlementInfo(self, param):
        try:
            payload = param["payload"]
            record = transaction_settlement_crud._find_by_payment_settlement_id(
                self.__db, payload["id"]
            )
            if not record:
                raise PermissionError("Record Not Found!")

            transaction_settlement_crud._update(self.__db, record, payload["status"])
            return True
        except Exception as e:
            self.__del__()
            raise PermissionError(e)
