# This module defines the UtilityService class, which provides utility functions
# for payment processing, including Paysafe API integration, settlement management,
# and invoice comparison for refund processing.

import base64  # For encoding/decoding authentication credentials
import locale  # For number formatting
import requests  # HTTP client for API requests
from decouple import config  # For environment variable management
from datetime import datetime  # For date and time operations
from sql.crud import (
    invoice as invoice_crud,  # CRUD operations for invoices
    transaction_settlement as transaction_settlement_crud,  # CRUD operations for settlements
    appointment as appointment_crud  # CRUD operations for appointments
)
from sql.schemas.user_payment_methods import UserSchema  # Schema for user data serialization

class UtilityService:
    """
    Service class providing utility functions for payment processing.
    
    This service handles Paysafe API integration, settlement management,
    and various utility functions for payment operations.
    """
    
    def __init__(self):
        """
        Initializes the UtilityService with Paysafe configuration.
        
        Sets up the Paysafe API configuration based on the environment
        (test or live) and prepares authentication headers.
        """
        self._user_schema = UserSchema()  # Schema for user data serialization
        self.client = requests  # HTTP client for API requests
        
        # Set the environment to "test" or "live" to select the corresponding configuration
        self.environment = config("PAYSAFE_ENVIRONMENT")
        self.unit_multiplier = int(config("PAYSAFE_CURRENCY_BASE_UNITS_MULTIPLIER"))
        
        # Set base URL and API key based on the environment
        if self.environment == "LIVE":
            self.base_url = config("PAYSAFE_LIVE_HOST_URL")
            self.paysafe_key = config("PAYSAFE_LIVE_API_PRIVATE_KEY").encode("utf-8")
            self.paysafe_simlator = config("PAYSAFE_LIVE_SIMULATOR").encode("utf-8")
        else:  # Default to test environment
            self.base_url = config("PAYSAFE_TEST_HOST_URL")
            self.paysafe_key = config("PAYSAFE_TEST_API_PRIVATE_KEY").encode("utf-8")
            self.paysafe_simlator = config("PAYSAFE_TEST_SIMULATOR").encode("utf-8")

        # Prepare authentication headers for Paysafe API requests
        self.headers = {
            "Simulator": self.paysafe_simlator,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Basic {base64.b64encode(self.paysafe_key).decode('utf-8')}",
        }

    def _base64_encode(self, sample_string: str):
        sample_string_bytes = sample_string.encode("ascii")
        base64_bytes = base64.b64encode(sample_string_bytes)
        base64_string = base64_bytes.decode("ascii")
        return base64_string

    def _base64_decode(self, sample_string: str):
        return base64.b64decode(sample_string).decode("UTF-8")

    def _number_format(num, places=0):
        return locale.format_string("%.*f", (places, num), True)

    def _parse_prefix(line, fmt):
        try:
            t = time.strptime(line, fmt)
        except ValueError as v:
            if len(v.args) > 0 and v.args[0].startswith("unconverted data remains: "):
                line = line[: -(len(v.args[0]) - 26)]
                t = time.strptime(line, fmt)
            else:
                raise
        return t

    def _remove_timezone(self, time_Str: str):
        add_time = time_Str
        if len(add_time) > 20:
            add_time = add_time[:-5]
        return add_time

    # Get Settlement by transaction id
    def get_settlement_by_transaction_id(self, db, transaction_id):
        try:
            t_settlement = transaction_settlement_crud._find_by_transaction_id(
                db, transaction_id
            )
            if not t_settlement:
                raise PermissionError(
                    "Settlement detail not available for this transaction!"
                )

            a_settlement = self._paysafeSettlementGetApi(
                t_settlement.payment_settlement_id
            )
            if a_settlement:
                a_settlement["amount"] = a_settlement["amount"] / self.unit_multiplier
                a_settlement["availableToRefund"] = (
                    a_settlement["availableToRefund"] / self.unit_multiplier
                )
                t_settlement.refundable_amount = a_settlement["availableToRefund"]
                t_settlement.status = a_settlement["status"]
                t_settlement.updated_at = datetime.now()
                db.add(t_settlement)
                db.commit()
                db.refresh(t_settlement)

            return a_settlement
        except Exception as e:
            raise PermissionError(e)

    def _paysafeSettlementGetApi(self, settlement_id):
        try:
            response = self.client.get(
                self.base_url + f"/paymenthub/v1/settlements/{settlement_id}",
                headers=self.headers,
            )
            if not response.status_code in [200, 201]:
                data = response.json()
                error_message = data["error"]["message"]
                error_code = data["error"]["code"]
                raise PermissionError(f"{error_code}: {error_message}")
            return response.json()

        except Exception as e:
            raise PermissionError(e)

    def _invoice_comparission(self, db, original_invoice, refund_invoice):
        
        valid_refund_item_list = []
        appointment_service = {}
        tax = None
        original_invoice_tax = original_invoice["tax_rate"]
        appointment_id = original_invoice["appointment_id"]
        appointment = appointment_crud.get_appointment(db, appointment_id)
        if ("invoice_service" in refund_invoice and len(refund_invoice["invoice_service"]) != 0) and (appointment_id is not None and appointment_id != 0 and appointment_id == refund_invoice["invoice_service"][0]["appointment_id"]):
            cost_tax = appointment.cost_tax if appointment.cost_tax is not None else 0
            appointment_service = {
                "price" : appointment.cost,
                "is_taxable" : True if cost_tax != 0 else False,
                "tax_rate" : (cost_tax / appointment.cost) * self.unit_multiplier,
                "total_amount" : appointment.cost + cost_tax
            }
            valid_refund_item_list.append(appointment_service)

        if "invoice_items" in refund_invoice and len(refund_invoice["invoice_items"]) != 0:
            valid_refund_item = {}
            for refund_item in refund_invoice["invoice_items"]:
                for original_item in original_invoice["invoice_items"]:
                    if refund_item["id"] == original_item["id"]:
                        if refund_item["quantity"] > original_item["quantity"]:
                            raise ValueError(f"Item quantity exceeds original quantity for item ID {refund_item['id']}.")

                        valid_refund_item = original_item
                        break

                if valid_refund_item:
                    original_item_price = valid_refund_item["price"]            
                    is_taxable = valid_refund_item.get("is_taxable", False)
                    refund_item_quantity = refund_item["quantity"]
                    
                    if is_taxable:
                        tax = (original_item_price * original_invoice_tax) / self.unit_multiplier
                    else :
                        tax = 0  

                    refund_item["price"] = original_item_price
                    refund_item["is_taxable"] = is_taxable if is_taxable else False
                    refund_item["tax_rate"] = original_invoice_tax
                    refund_item["total_amount"] = (refund_item_quantity*  original_item_price) + tax * refund_item_quantity
                    valid_refund_item_list.append(refund_item)
                          
        refund_invoice = {
            "id": refund_invoice["id"],
            "invoice_items": valid_refund_item_list,
            "total_refund_amount": sum(item["total_amount"] for item in valid_refund_item_list),
        }

        return refund_invoice