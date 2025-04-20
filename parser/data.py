
from dataclasses import dataclass

@dataclass
class DataRow:
    Date: str
    Time: str
    FoP: str
    Invoice: str
    TransactionType: str
    Qty: int
    Amount: str
    CustomerName: str
    PhoneNumber: str
