# This module defines the AuthnetService class, which handles integration with the Authorize.Net API
# for payment processing, including creating transactions, managing customer profiles, refunds, and more.

import requests
from decouple import config  # For environment variable management
from authorizenet import apicontractsv1  # Authorize.Net API contracts
from authorizenet.apicontrollers import (
    createTransactionController,
    createCustomerProfileController,
    createCustomerPaymentProfileController,
)  # Controllers for Authorize.Net operations


class AuthnetService:
    """
    Service class for interacting with the Authorize.Net API.

    This class provides methods for creating transactions, managing customer profiles,
    refunds, and other payment-related operations using the Authorize.Net API.
    """

    def __init__(self):
        """
        Initializes the AuthnetService with the required configuration.

        The configuration is loaded from environment variables, and the appropriate
        base URL and API credentials are set based on the environment (test or live).
        """
        self.client = requests  # HTTP client for making API requests

        # Set the environment to "test" or "live" to select the corresponding configuration.
        self.environment = config("AUTH_ENVIRONMENT")

        # Set base URL and API key based on the environment
        if self.environment == "LIVE":
            self.base_url = config("AUTH_LIVE_URL")
            self.version = config("AUTH_LIVE_VERSION")
            self.client_id = config("AUTH_LIVE_CLIENT_ID")
            self.client_secret = config("AUTH_LIVE_CLIENT_SECRET")
        else:  # Default to test environment
            self.base_url = config("AUTH_TEST_URL")
            self.version = config("AUTH_TEST_VERSION")
            self.client_id = config("AUTH_TEST_CLIENT_ID")
            self.client_secret = config("AUTH_TEST_CLIENT_SECRET")

    def MerchantAuthenticationType(self, request):
        """
        Creates a MerchantAuthenticationType object for Authorize.Net API requests.

        Args:
            request (dict): A dictionary containing API login ID and transaction key.

        Returns:
            apicontractsv1.merchantAuthenticationType: The merchant authentication object.
        """
        merchantAuth = apicontractsv1.merchantAuthenticationType()
        merchantAuth.name = request["apiLoginId"]
        merchantAuth.transactionKey = request["transactionKey"]
        return merchantAuth

    def PaymentNonceType(self, data):
        """
        Creates an opaqueDataType object for payment nonce.

        Args:
            data (dict): A dictionary containing data descriptor and data value.

        Returns:
            apicontractsv1.opaqueDataType: The opaque data object.
        """
        opaqueData = apicontractsv1.opaqueDataType()
        opaqueData.dataDescriptor = data["dataDescriptor"].strip()
        opaqueData.dataValue = data["dataValue"].strip() if data["dataValue"] else None
        return opaqueData

    def ExecuteWithApiResponse(self, controller):
        """
        Executes an API controller and retrieves the response.

        Args:
            controller: The API controller to execute.

        Returns:
            dict: The response from the API, converted to a dictionary.

        Raises:
            Exception: If the response is null or contains errors.
        """
        controller.execute()
        response = controller.getresponse()

        if response is not None:
            return self.convert_to_dict(response)
        else:
            return {
                "status_code": 422,
                "message": "Null Response",
                "response": [],
            }

    def CreateCustomerProfile(self, customerDetails):
        """
        Creates a customer profile in Authorize.Net.

        Args:
            customerDetails (dict): A dictionary containing customer details.

        Returns:
            dict: The response from the API.
        """
        merchantAuth = self.MerchantAuthenticationType(customerDetails)

        createCustomerProfile = apicontractsv1.createCustomerProfileRequest()
        createCustomerProfile.merchantAuthentication = merchantAuth
        customerName = f"{customerDetails['firstName']} {customerDetails['lastName']}"
        createCustomerProfile.profile = apicontractsv1.customerProfileType(
            customerDetails["merchantCustomerId"], customerName, customerDetails["email"]
        )

        controller = createCustomerProfileController(createCustomerProfile)
        return self.ExecuteWithApiResponse(controller)

    def CreateCustomerPaymentProfile(self, customerDetail):
        """
        Creates a customer payment profile in Authorize.Net.

        Args:
            customerDetail (dict): A dictionary containing payment profile details.

        Returns:
            dict: The response from the API.
        """
        merchantAuth = self.MerchantAuthenticationType(customerDetail)

        # Set the transaction's refId
        refId = f"ref{int(time.time() * 1000)}"

        opaqueData = self.PaymentNonceType(customerDetail)

        payment = apicontractsv1.paymentType()
        if customerDetail["authPayMethod"] == "AcceptJs":
            payment.opaqueData = opaqueData
        else:
            raise PermissionError("Wrong Payment Method")

        billTo = apicontractsv1.customerAddressType()
        billTo.firstName = customerDetail["firstName"]
        billTo.lastName = customerDetail["lastName"]

        profile = apicontractsv1.customerPaymentProfileType()
        profile.payment = payment
        profile.billTo = billTo

        createCustomerPaymentProfile = (
            apicontractsv1.createCustomerPaymentProfileRequest()
        )
        createCustomerPaymentProfile.merchantAuthentication = merchantAuth
        createCustomerPaymentProfile.paymentProfile = profile
        createCustomerPaymentProfile.refId = refId
        createCustomerPaymentProfile.customerProfileId = str(
            customerDetail["customerProfileId"]
        )

        controller = createCustomerPaymentProfileController(
            createCustomerPaymentProfile
        )
        return self.ExecuteWithApiResponse(controller)

    def ChargeCreditCard(self, payload):
        """
        Charges a credit card using Authorize.Net.

        Args:
            payload (dict): A dictionary containing transaction details.

        Returns:
            dict: The response from the API.
        """
        merchantAuth = self.MerchantAuthenticationType(payload)
        opaqueData = self.PaymentNonceType(payload)

        payment = apicontractsv1.paymentType()
        if payload["authPayMethod"] == "AcceptJs":
            payment.opaqueData = opaqueData
        else:
            raise PermissionError("Wrong Payment Method")

        order = apicontractsv1.orderType()
        order.invoiceNumber = payload["invoiceNumber"]
        order.description = payload["invoiceDiscription"]

        customerAddress = apicontractsv1.customerAddressType()
        customerAddress.firstName = payload["firstName"]
        customerAddress.lastName = payload["lastName"]

        customerData = apicontractsv1.customerDataType()
        customerData.type = payload["contactType"]
        customerData.id = str(payload["UserId"])
        if payload["contactEmail"]:
            customerData.email = payload["contactEmail"]

        refId = f"ref{int(time.time() * 1000)}"

        transactionrequest = apicontractsv1.transactionRequestType()
        transactionrequest.transactionType = "authCaptureTransaction"
        transactionrequest.amount = payload["amount"]
        transactionrequest.payment = payment
        transactionrequest.order = order
        transactionrequest.billTo = customerAddress
        transactionrequest.customer = customerData

        createtransactionrequest = apicontractsv1.createTransactionRequest()
        createtransactionrequest.merchantAuthentication = merchantAuth
        createtransactionrequest.refId = refId
        createtransactionrequest.transactionRequest = transactionrequest

        createtransactioncontroller = createTransactionController(
            createtransactionrequest
        )
        return self.ExecuteWithApiResponse(createtransactioncontroller)

    # Additional methods like `RefundTransaction`, `ReadTransactionInfo`, etc., can be refactored similarly.