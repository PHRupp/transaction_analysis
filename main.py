
import logging
import os
import re
import traceback as tb

from dataclasses import dataclass
from datetime import datetime
from os.path import join
from typing import List

import numpy as np
import pandas as pd


log_file = './results.log'
in_file_name = 'HUNTERSCREEK2023.xls'
out_file_name = 'HC_2023.csv'


logging.basicConfig(filename=log_file, level=logging.INFO)


data_dir = 'G:/My Drive/LBA/Dry Cleaning MLX/HC/Analysis'
in_file = 'C:/Users/pathr/Downloads/SEPT2024-2025#1.xls'
#in_file = join(data_dir, in_file_name)
out_file = join(data_dir, out_file_name)
df = pd.read_excel(in_file)

# Clean up the file otherwise the weird line skips are annoying
df.dropna(how='all', inplace=True, ignore_index=True)

run_date_col = 'Unnamed: 1'
title_col1 = 'Unnamed: 6'
title_col2 = 'Unnamed: 7'
section_title = "Hunter's Creek"
section_invoice_paid = 'Invoice Paid'
section_end_run_date = 'Run Date'

PHONE_NUMBER_PATTERN = re.compile('\(\d{3}\) \d{3}-\d{4}')

# Some of the data is shifted right
section_row_indices1 = np.where(df[title_col1] == section_invoice_paid)[0]
section_row_indices2 = np.where(df[title_col2] == section_invoice_paid)[0]
section_end_row_indices = np.where(df[run_date_col] == section_end_run_date)[0]
section_row_indices = np.concatenate( (section_row_indices1, section_row_indices2))
section_row_indices.sort()


data_frames = []


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


"""
						Hunter's Creek						
			3964 Town Center Blvd, Orlando,FL 32837-6103									
						Invoice Paid						
	Date	Time					FoP		Invoice	Type	Qty	Amount
	9/4/2024	4:51 PM					Debit		A104091	D	12	$71.71 
	689	272-5740	TSIFTSI SEVNTA									
	9/4/2024	5:03 PM					CASH		A104656	D	1	$32.03 
	407	376-7264	GUSMAN ERIC									
	9/4/2024	5:34 PM					Debit		A104528	L	6	$30.29 
	714	244-5456	hache nancy																	
"""
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

        # Sometimes there are two invoices under one transaction
        # see if it's a date next then skip
        """
        9/4/2024	11:12 AM					Debit		A95917	D	2	$0.00 
        9/4/2024	11:12 AM					Debit		A104416	D	1	$0.00 
        954	849-5156	GOLDSMITH JOHN									
        """
        try:
            # skip line, this may happen if a transaction is not parsable
            if is_parsable_transaction(data_row_index, col_name_indices, df):
                data_row = parse_transaction(data_row_index, col_name_indices, df)
                data.append(data_row)

        except Exception as e:
            logging.warning(tb.format_exc())

        # Move forward a row
        data_row_index += 1

        # Jump out if we reached the end of section
        if (data_row_index+1) >= section_end_row_index:
            reached_end = True

    return data


"""
Example Transaction:
9/3/2024	8:47 AM					Debit		A103844	L	4	$23.96 
407	937-9448	PORCELLA STEFANO									
"""
def is_parsable_transaction(
    data_row_index: int,
    col_name_indices: List[int],
    df: pd.DataFrame,
) -> bool:

    success = False

    try:
        # Verify line 1 starts with a valid date
        area_code_index = col_name_indices[0]
        area_code = df.iat[data_row_index, area_code_index]
        date = datetime.strptime(area_code, "%m/%d/%Y")

        # Verify the phone number is parsable
        area_code_index = col_name_indices[0]
        area_code = df.iat[data_row_index+1, area_code_index]
        other_phone_digits = df.iat[data_row_index+1, area_code_index+1]
        phone_number = f'({area_code}) {other_phone_digits}'

        match = PHONE_NUMBER_PATTERN.search(phone_number)

        if match is not None:
            success = True

    except Exception as e:
        logging.warning(tb.format_exc())

    return success


"""
Example Transaction:
9/3/2024	8:47 AM					Debit		A103844	L	4	$23.96 
407	937-9448	PORCELLA STEFANO									
"""
def parse_transaction(
    data_row_index: int,
    col_name_indices: List[int],
    df: pd.DataFrame,
) -> DataRow:

    # Parse the phone number
    area_code_index = col_name_indices[0]
    area_code = df.iat[data_row_index+1, area_code_index]
    other_phone_digits = df.iat[data_row_index+1, area_code_index+1]
    phone_number = f'({area_code}) {other_phone_digits}'

    # Parse date/time
    date_index = col_name_indices[0]
    time_index = col_name_indices[1]
    date = df.iat[data_row_index, date_index]
    time = df.iat[data_row_index, time_index]

    # Parse name
    name_index = time_index + 1
    name = df.iat[data_row_index+1, name_index]

    # Parse the FoP
    fop_index = col_name_indices[2]
    fop = df.iat[data_row_index, fop_index]

    # Parse the Invoice number
    invoice_index = col_name_indices[3]
    invoice = df.iat[data_row_index, invoice_index]

    # Parse the type
    transaction_type_index = col_name_indices[4]
    transaction_type = df.iat[data_row_index, transaction_type_index]

    # Parse the quantity
    qty_index = col_name_indices[5]
    qty = int(df.iat[data_row_index, qty_index])

    # Parse the amount
    amount_index = col_name_indices[6]
    amount = df.iat[data_row_index, amount_index]

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


try:
    # process each section (one per day)
    for section_row_index, section_end_row_index in zip(section_row_indices, section_end_row_indices):

        section_data = parse_section(section_row_index, section_end_row_index, df)

        data_frames.append(
            pd.DataFrame([
                d.__dict__ for d in section_data
            ])
        )

    # put all the data together
    pd.concat(data_frames).to_csv(out_file)

except Exception as e:
    logging.warning(tb.format_exc())


























