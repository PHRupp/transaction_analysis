
from dataclasses import dataclass

@dataclass
class DataRowIn:
    Date: str
    Time: str
    Invoice: str
    TransactionType: str
    Qty: int
    Amount: str
    CustomerName: str
    PhoneNumber: str

@dataclass
class DataRowReady:
    Date: str
    Time: str
    FoP: str
    Invoice: str
    TransactionType: str
    Qty: int
    Amount: str
    CustomerName: str
    PhoneNumber: str

@dataclass
class DataRowPaid:
    Date: str
    Time: str
    FoP: str
    Invoice: str
    TransactionType: str
    Qty: int
    Amount: str
    CustomerName: str
    PhoneNumber: str

@dataclass
class DataRowPickup:
    Date: str
    Time: str
    FoP: str
    Invoice: str
    TransactionType: str
    Qty: int
    Amount: str
    CustomerName: str
    PhoneNumber: str
