
from dataclasses import dataclass

@dataclass
class DataRowIn:
    DateIn: str
    TimeIn: str
    Invoice: str
    TransactionTypeIn: str
    QtyIn: int
    AmountIn: str
    CustomerNameIn: str
    PhoneNumberIn: str

@dataclass
class DataRowReady:
    DateReady: str
    TimeReady: str
    FoPReady: str
    Invoice: str
    TransactionTypeReady: str
    QtyReady: int
    AmountReady: str
    CustomerNameReady: str
    PhoneNumberReady: str

@dataclass
class DataRowPaid:
    DatePaid: str
    TimePaid: str
    FoPPaid: str
    Invoice: str
    TransactionTypePaid: str
    QtyPaid: int
    AmountPaid: str
    CustomerNamePaid: str
    PhoneNumberPaid: str

@dataclass
class DataRowPickup:
    DatePickup: str
    TimePickup: str
    FoPPickup: str
    Invoice: str
    TransactionTypePickup: str
    QtyPickup: int
    AmountPickup: str
    CustomerNamePickup: str
    PhoneNumberPickup: str
