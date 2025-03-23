
import numpy as np
import pandas as pd
from dataclasses import dataclass
from datetime import datetime
from typing import List

"""
PROBLEMS:
1.) not always a line below (FIXED)
2.) multiple invoice lines per
"""

f = 'C:/Users/pathr/Downloads/SEPT2024-2025#1.xls'
df = pd.read_excel(f)

# Clean up the file otherwise the weird line skips are annoying
df.dropna(how='all', inplace=True, ignore_index=True)

run_date_col = 'Unnamed: 1'
title_col1 = 'Unnamed: 6'
title_col2 = 'Unnamed: 7'
section_title = "Hunter's Creek"
section_invoice_paid = 'Invoice Paid'
section_end_run_date = 'Run Date'

# Some of the data is shifted right
section_row_indices1 = np.where(df[title_col1] == section_invoice_paid)[0]
section_row_indices2 = np.where(df[title_col2] == section_invoice_paid)[0]
section_end_row_indices = np.where(df[run_date_col] == section_end_run_date)[0]
section_row_indices = np.concatenate( (section_row_indices1, section_row_indices2))
section_row_indices.sort()
print(section_row_indices)


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


def parse_section(
    section_row_index: int,
    section_end_row_index: int,
    df: pd.DataFrame,
) -> pd.DataFrame:
    data = []

    # column names after 'Invoice Paid' row
    col_names_row_index = section_row_index + 1
    data_row_index = col_names_row_index + 1

    # parse which columns have the data and grab their names
    raw_cols = df.iloc[col_names_row_index,:]
    col_name_indices = np.where(~raw_cols.isna())[0]
    
    reached_end = False

    # keep parsing each transaction
    while not reached_end:
        print('------------------')
        print(data_row_index)
        data_row = parse_transaction(data_row_index, col_name_indices, df)
        data.append(data_row)
        #print(data)

        # jump to next transaction
        data_row_index += 2

        # Sometimes there are two invoices under one transaction
        # see if it's a date next then skip
        try:
            area_code_index = col_name_indices[0]
            area_code = df.iat[data_row_index, area_code_index]
            date = datetime.strptime(area_code, "%m/%d/%Y")
            data_row_index += 1
        except Exception as e:
            pass

        # Jump out if we reached the end of section
        if (data_row_index+1) >= section_end_row_index:
            reached_end = True

    return data


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
    transaction_type_index = col_name_indices[4]
    transaction_type = df.iat[data_row_index+1, transaction_type_index]

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
        TransactionType=transaction_type,
        Qty=qty,
        Amount=amount,
        CustomerName=name,
        PhoneNumber=phone_number,
    )
    
    return data_row



# process each section (one per day)
for section_row_index, section_end_row_index in zip(section_row_indices, section_end_row_indices):
    
    data = parse_section(section_row_index, section_end_row_index, df)
    
    new_df = pd.DataFrame([
        d.__dict__ for d in data
    ])

    print(new_df)
    exit(0)


























