
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List

f = 'C:/Users/pathr/Downloads/SEPT2024-2025#1.xls'
df = pd.read_excel(f)

title_col = 'Unnamed: 6'
section_title = "Hunter's Creek"
section_invoice_paid = 'Invoice Paid'

section_row_indices = np.where(df[title_col] == section_invoice_paid)[0]


@dataclass
class DataRow:
    Date: str
    Time: str
    FoP: str
    Invoice: str
    Type: str
    Qty: int
    Amount: str
    CustomerName: str
    PhoneNumber: str



def parse_section(section_row_index: int, df: pd.DataFrame) -> pd.DataFrame:
    """
    """
    # column names after 'Invoice Paid' row
    col_names_row_index = section_row_index + 1
    data_row_index = col_names_row_index + 2

    # parse which columns have the data and grab their names
    raw_cols = df.iloc[col_names_row_index,:]
    col_name_indices = np.where(~raw_cols.isna())[0]
    
    data_row = parse_transaction(data_row_index, col_name_indices, df)
    print(data_row)
    exit(0)


def parse_transaction(
    data_row_index: int,
    col_name_indices: List[int],
    df: pd.DataFrame,
) -> DataRow:

    # Parse the phone number
    area_code_index = col_name_indices[0]
    area_code = df.iat[data_row_index, area_code_index]
    other_phone_digits = df.iat[data_row_index, area_code_index+1]
    phone_number = f'({area_code}) {other_phone_digits}'

    # Parse date/time
    date_index = col_name_indices[0]
    time_index = col_name_indices[1]
    date = df.iat[data_row_index+1, date_index]
    time = df.iat[data_row_index+1, time_index]

    # Parse name
    name_index = time_index + 1
    name = df.iat[data_row_index, name_index]

    # Parse the FoP
    fop_index = col_name_indices[2]
    fop = df.iat[data_row_index+1, fop_index]

    # Parse the Invoice number
    invoice_index = col_name_indices[3]
    invoice = df.iat[data_row_index+1, invoice_index]

    # Parse the type
    type_index = col_name_indices[4]
    type = df.iat[data_row_index+1, type_index]

    # Parse the quantity
    qty_index = col_name_indices[5]
    qty = int(df.iat[data_row_index+1, qty_index])

    # Parse the amount
    amount_index = col_name_indices[6]
    amount = df.iat[data_row_index+1, amount_index]

    # return the data record
    data_row = DataRow(
        Date=date,
        Time=time,
        FoP=fop,
        Invoice=invoice,
        Type=type,
        Qty=qty,
        Amount=amount,
        CustomerName=name,
        PhoneNumber=phone_number,
    )
    
    return data_row



# process each section (one per day)
for section_row_index in section_row_indices:
    
    new_df = parse_section(section_row_index, df)

print(df)


























