# This module defines Pydantic models for user payment method management in the payment API service.
# These models handle user payment methods, status tracking, and payment method configurations.

from __future__ import annotations
from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, Field, validator


class StatusType(str, Enum):
    """
    Enumeration of payment method status types.
    
    Defines the possible states of a user's payment method during processing.
    """
    approved = "approved"    # Payment method has been approved for use
    declined = "declined"    # Payment method has been declined
    pending = "pending"      # Payment method is awaiting approval
    desabled = "desabled"    # Payment method has been disabled


class Type(str, Enum):
    """
    Enumeration of supported payment method types.
    
    This enum defines all the payment providers and methods supported by the system.
    """
    authnet = "authnet"      # Authorize.Net payment processor
    paysafe = "paysafe"      # Paysafe payment processor
    jupiter = "jupiter"      # Jupiter payment processor
    stripe = "stripe"        # Stripe payment processor
    paypal = "paypal"        # PayPal payment processor
    googlepay = "googlepay"  # Google Pay digital wallet
    applepay = "applepay"    # Apple Pay digital wallet


class Preference(str, Enum):
    """
    Enumeration of preference types.
    
    Defines the scope of payment preferences.
    """
    user = "user"  # User-level preferences


class OrderDirection(str, Enum):
    """
    Enumeration of sorting order directions.
    
    Used for ordering query results in ascending or descending order.
    """
    asc = "asc"    # Ascending order
    desc = "desc"  # Descending order


class Currency(str, Enum):
    """
    Comprehensive enumeration of supported currencies.
    
    This enum includes all major world currencies supported by the payment system,
    following ISO 4217 currency codes for international compatibility.
    """
    AED = "AED"  # UAE Dirham
    AFN = "AFN"  # Afghan Afghani
    ALL = "ALL"  # Albanian Lek
    AMD = "AMD"  # Armenian Dram
    ANG = "ANG"  # Netherlands Antillean Guilder
    AOA = "AOA"  # Angolan Kwanza
    ARS = "ARS"  # Argentine Peso
    AUD = "AUD"  # Australian Dollar
    AWG = "AWG"  # Aruban Florin
    AZN = "AZN"  # Azerbaijani Manat
    BAM = "BAM"  # Bosnia-Herzegovina Convertible Mark
    BBD = "BBD"  # Barbadian Dollar
    BDT = "BDT"  # Bangladeshi Taka
    BGN = "BGN"  # Bulgarian Lev
    BHD = "BHD"  # Bahraini Dinar
    BIF = "BIF"  # Burundian Franc
    BMD = "BMD"  # Bermudian Dollar
    BND = "BND"  # Brunei Dollar
    BOB = "BOB"  # Bolivian Boliviano
    BRL = "BRL"  # Brazilian Real
    BSD = "BSD"  # Bahamian Dollar
    BTN = "BTN"  # Bhutanese Ngultrum
    BWP = "BWP"  # Botswanan Pula
    BYR = "BYR"  # Belarusian Ruble
    BZD = "BZD"  # Belize Dollar
    CAD = "CAD"  # Canadian Dollar
    CDF = "CDF"  # Congolese Franc
    CHF = "CHF"  # Swiss Franc
    CLP = "CLP"  # Chilean Peso
    CNY = "CNY"  # Chinese Yuan
    COP = "COP"  # Colombian Peso
    CRC = "CRC"  # Costa Rican Colón
    CUC = "CUC"  # Cuban Convertible Peso
    CUP = "CUP"  # Cuban Peso
    CVE = "CVE"  # Cape Verdean Escudo
    CZK = "CZK"  # Czech Koruna
    DJF = "DJF"  # Djiboutian Franc
    DKK = "DKK"  # Danish Krone
    DOP = "DOP"  # Dominican Peso
    DZD = "DZD"  # Algerian Dinar
    EGP = "EGP"  # Egyptian Pound
    ERN = "ERN"  # Eritrean Nakfa
    ETB = "ETB"  # Ethiopian Birr
    EUR = "EUR"  # Euro
    FJD = "FJD"  # Fijian Dollar
    FKP = "FKP"  # Falkland Islands Pound
    GBP = "GBP"  # British Pound Sterling
    GEL = "GEL"  # Georgian Lari
    GGP = "GGP"  # Guernsey Pound
    GHS = "GHS"  # Ghanaian Cedi
    GIP = "GIP"  # Gibraltar Pound
    GMD = "GMD"  # Gambian Dalasi
    GNF = "GNF"  # Guinean Franc
    GTQ = "GTQ"  # Guatemalan Quetzal
    GWP = "GWP"  # Guinea-Bissau Peso
    GYD = "GYD"  # Guyanese Dollar
    HKD = "HKD"  # Hong Kong Dollar
    HNL = "HNL"  # Honduran Lempira
    HRK = "HRK"  # Croatian Kuna
    HTG = "HTG"  # Haitian Gourde
    HUF = "HUF"  # Hungarian Forint
    IDR = "IDR"  # Indonesian Rupiah
    ILS = "ILS"  # Israeli New Sheqel
    IMP = "IMP"  # Manx Pound
    INR = "INR"  # Indian Rupee
    IQD = "IQD"  # Iraqi Dinar
    IRR = "IRR"  # Iranian Rial
    ISK = "ISK"  # Icelandic Króna
    JEP = "JEP"  # Jersey Pound
    JMD = "JMD"  # Jamaican Dollar
    JOD = "JOD"  # Jordanian Dinar
    JPY = "JPY"  # Japanese Yen
    KES = "KES"  # Kenyan Shilling
    KGS = "KGS"  # Kyrgystani Som
    KHR = "KHR"  # Cambodian Riel
    KMF = "KMF"  # Comorian Franc
    KPW = "KPW"  # North Korean Won
    KRW = "KRW"  # South Korean Won
    KWD = "KWD"  # Kuwaiti Dinar
    KYD = "KYD"  # Cayman Islands Dollar
    KZT = "KZT"  # Kazakhstani Tenge
    LAK = "LAK"  # Laotian Kip
    LBP = "LBP"  # Lebanese Pound
    LKR = "LKR"  # Sri Lankan Rupee
    LRD = "LRD"  # Liberian Dollar
    LSL = "LSL"  # Lesotho Loti
    LTL = "LTL"  # Lithuanian Litas
    LVL = "LVL"  # Latvian Lats
    LYD = "LYD"  # Libyan Dinar
    MAD = "MAD"  # Moroccan Dirham
    MDL = "MDL"  # Moldovan Leu
    MGA = "MGA"  # Malagasy Ariary
    MKD = "MKD"  # Macedonian Denar
    MMK = "MMK"  # Myanma Kyat
    MNT = "MNT"  # Mongolian Tugrik
    MOP = "MOP"  # Macanese Pataca
    MRO = "MRO"  # Mauritanian Ouguiya
    MUR = "MUR"  # Mauritian Rupee
    MVR = "MVR"  # Maldivian Rufiyaa
    MWK = "MWK"  # Malawian Kwacha
    MXN = "MXN"  # Mexican Peso
    MYR = "MYR"  # Malaysian Ringgit
    MZN = "MZN"  # Mozambican Metical
    NAD = "NAD"  # Namibian Dollar
    NGN = "NGN"  # Nigerian Naira
    NIO = "NIO"  # Nicaraguan Córdoba
    NOK = "NOK"  # Norwegian Krone
    NPR = "NPR"  # Nepalese Rupee
    NZD = "NZD"  # New Zealand Dollar
    OMR = "OMR"  # Omani Rial
    PAB = "PAB"  # Panamanian Balboa
    PEN = "PEN"  # Peruvian Nuevo Sol
    PGK = "PGK"  # Papua New Guinean Kina
    PHP = "PHP"  # Philippine Peso
    PKR = "PKR"  # Pakistani Rupee
    PLN = "PLN"  # Polish Zloty
    PYG = "PYG"  # Paraguayan Guarani
    QAR = "QAR"  # Qatari Rial
    RON = "RON"  # Romanian Leu
    RSD = "RSD"  # Serbian Dinar
    RUB = "RUB"  # Russian Ruble
    RWF = "RWF"  # Rwandan Franc
    SAR = "SAR"  # Saudi Riyal
    SBD = "SBD"  # Solomon Islands Dollar
    SCR = "SCR"  # Seychellois Rupee
    SDG = "SDG"  # Sudanese Pound
    SEK = "SEK"  # Swedish Krona
    SGD = "SGD"  # Singapore Dollar
    SHP = "SHP"  # Saint Helena Pound
    SLL = "SLL"  # Sierra Leonean Leone
    SOS = "SOS"  # Somali Shilling
    SPL = "SPL"  # Seborga Luigino
    SRD = "SRD"  # Surinamese Dollar
    SSP = "SSP"  # South Sudanese Pound
    STD = "STD"  # São Tomé and Príncipe Dobra
    SVC = "SVC"  # Salvadoran Colón
    SYP = "SYP"  # Syrian Pound
    SZL = "SZL"  # Swazi Lilangeni
    THB = "THB"  # Thai Baht
    TJS = "TJS"  # Tajikistani Somoni
    TMT = "TMT"  # Turkmenistani Manat
    TND = "TND"  # Tunisian Dinar
    TOP = "TOP"  # Tongan Pa'anga
    TRY = "TRY"  # Turkish Lira
    TTD = "TTD"  # Trinidad and Tobago Dollar
    TVD = "TVD"  # Tuvaluan Dollar
    TWD = "TWD"  # New Taiwan Dollar
    TZS = "TZS"  # Tanzanian Shilling
    UAH = "UAH"  # Ukrainian Hryvnia
    UGX = "UGX"  # Ugandan Shilling
    USD = "USD"  # US Dollar
    UYU = "UYU"  # Uruguayan Peso
    UZS = "UZS"  # Uzbekistani Som
    VEF = "VEF"  # Venezuelan Bolívar
    VND = "VND"  # Vietnamese Dong
    VUV = "VUV"  # Vanuatu Vatu
    WST = "WST"  # Samoan Tala
    XAF = "XAF"  # Central African CFA Franc
    XCD = "XCD"  # East Caribbean Dollar
    XDR = "XDR"  # Special Drawing Rights
    XOF = "XOF"  # West African CFA Franc
    XPF = "XPF"  # CFP Franc
    YER = "YER"  # Yemeni Rial
    ZAR = "ZAR"  # South African Rand
    ZMW = "ZMW"  # Zambian Kwacha
    ZMK = "ZMK"  # Zambian Kwacha (old)
    ZWD = "ZWD"  # Zimbabwean Dollar


class CreateUserPaymentMethod(BaseModel):
    """
    Model for creating new user payment methods.
    
    This model handles the creation of payment methods for users,
    including the payment processor type and application details.
    """
    payment_method_type: Type = Field(default=Type.authnet, description="Type of payment method to create")
    application_number: str = Field(..., description="Application number for the payment method")

    @validator("*", pre=True)
    def blank_strings(cls, v):
        """
        Validator to clean up string values.
        
        Strips whitespace and converts empty strings or placeholder values to None.
        """
        if isinstance(v, str):
            v = v.strip()
            if v == "" or v == "string":
                return None
        return v


class UpdateUserPaymentMethod(BaseModel):
    """
    Model for updating existing user payment methods.
    
    This model allows users to update their payment method information
    including account details, currency, and merchant information.
    """
    account_number: str = Field(..., description="Account number for the payment method")
    account_name: Optional[str] = Field(None, description="Name associated with the account")
    account_currency: Currency = Field(default=Currency.USD, description="Currency for the account")
    merchant_id: str = Field(..., description="Merchant ID for the payment method")
    payment_method_type: Type = Field(default=Type.authnet, description="Type of payment method")

    @validator("*", pre=True)
    def blank_strings(cls, v):
        """
        Validator to clean up string values.
        
        Strips whitespace and converts empty strings or placeholder values to None.
        """
        if isinstance(v, str):
            v = v.strip()
            if v == "" or v == "string":
                return None
        return v


class StoreAuthAccess(BaseModel):
    """
    Model for storing authentication access credentials.
    
    This model handles the storage of authentication credentials for different
    payment processors, including login IDs, transaction keys, and client keys.
    """
    auth_login_id: str = Field(..., description="Authentication login ID")
    auth_transaction_key: str = Field(..., description="Authentication transaction key")
    auth_client_key: str = Field(..., description="Authentication client key")
    user_id: int = Field(..., description="ID of the user storing the credentials")
    payment_method_type: str = Field(..., description="Type of payment method for the credentials")

    @validator("*", pre=True)
    def blank_strings(cls, v):
        """
        Validator to clean up string and integer values.
        
        Strips whitespace from strings and converts empty values to None.
        """
        if isinstance(v, str):
            v = v.strip()
            if v == "" or v == "string":
                return None
        if isinstance(v, int):
            if v is None or v == 0:
                return None
        return v


class DefaultDetailsRequest(BaseModel):
    """
    Model for requesting default payment method details.
    
    This model is used to retrieve default payment method information
    for a specific user and payment processor.
    """
    payment_method: Literal[Type.paypal, Type.authnet, Type.jupiter, Type.stripe, Type.paypal, Type.applepay, Type.googlepay] = Field(default=Type.authnet, description="Payment method type to get defaults for")
    user_id: Optional[int] = Field(None, description="ID of the user requesting default details")