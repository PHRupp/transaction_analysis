
from dataclasses import dataclass

@dataclass
class DataRowIn:
    DateIn: str
    TimeIn: str
    Invoice: str
    TransactionType: str
    QtyIn: int
    AmountIn: str
    CustomerName: str
    PhoneNumber: str

@dataclass
class DataRowReady:
    DateReady: str
    TimeReady: str
    FoP: str
    Invoice: str
    TransactionType: str
    QtyReady: int
    AmountReady: str
    CustomerName: str
    PhoneNumber: str

@dataclass
class DataRowPaid:
    DatePaid: str
    TimePaid: str
    FoP: str
    Invoice: str
    TransactionType: str
    QtyPaid: int
    AmountPaid: str
    CustomerName: str
    PhoneNumber: str

@dataclass
class DataRowPickup:
    DatePickup: str
    TimePickup: str
    FoP: str
    Invoice: str
    TransactionType: str
    QtyPickup: int
    AmountPickup: str
    CustomerName: str
    PhoneNumber: str
