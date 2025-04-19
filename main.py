
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

run_date_col = 'Unnamed: 1'
title_col1 = 'Unnamed: 6'
title_col2 = 'Unnamed: 7'
section_title = "Hunter's Creek"
section_invoice_paid = 'Invoice Paid'
section_end_run_date = 'Run Date'

PHONE_NUMBER_PATTERN = re.compile('\(\d{3}\) \d{3}-\d{4}')


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


def clean_up_data(df: pd.DataFrame) -> pd.DataFrame:

    index_list_to_drop = []
    
    # Remove empty first column
    df.drop(columns=df.columns[0:1], inplace=True)

    # Clean up the file otherwise the weird line skips are annoying
    df.dropna(axis='index', how='all', inplace=True, ignore_index=True)
    
    # Collection of strings that represent rows to be removed
    drop_rows_strings = [
        "Hunter's Creek",
        '3964 Town Center Blvd, Orlando,FL 32837-6103',
        'Invoice Paid',
        'Invoice',
        'Run Date',
        'Dry Cleaning',
        'Account Receivable',
        'Miscellaneous',
        'IAN',
        'Cash Drawer',
    ]
    
    # Build an index filter for all rows to remove
    ind = (drop_rows_strings[0] == df)
    for s in drop_rows_strings[1:]:
        ind = ind | (s == df)
    
    # Check each row, if it has one of these strings, drop the row
    for i in ind.index:
        if ind.loc[i].sum() > 0:
            index_list_to_drop.append(i)

    # Drop the rows that contain useless data
    df.drop(index=index_list_to_drop, inplace=True)
    
    # The last row is aggregate financials, so drop it
    # Dropping here instead of adding to index list because it's not the last 
    # before the filtering above. After the filtering, it is last
    df.drop(index=df.index[-1], inplace=True)
    
    # Some rows have duplicate transaction amount as line above but no date/areacode data
    df.dropna(axis='index', subset=df.columns[:1], inplace=True, ignore_index=True)
    
    # Some rows are shifted right
    col2_shifted = df[df.columns[1]].isnull()
    for i in range(1, df.shape[1]-1):
        i_col = df.columns[i]
        j_col = df.columns[i+1]
        #df.loc[col2_shifted, i_col] = df.loc[col2_shifted, j_col]

    # Make the right most column nans to avoid duplication since shifted left
    #df.loc[col2_shifted, df.columns[-1]] = np.nan
    
    # Once all the bad rows are dropped, then we can clean up some of the oddly
    # shifted columns. Doing this again because columns have now been shifted left.
    df.dropna(axis='columns', how='all', inplace=True, ignore_index=True)
    print(df)

    return df


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
def parse_data(
    df: pd.DataFrame,
) -> pd.DataFrame:
    data = []

    # column names after 'Invoice Paid' row
    data_row_index = df.index[0]
    
    for data_row_index in range(df.shape[0]):
    
        # If last line reached, jump out
        if data_row_index+1 == df.shape[0]:
            continue

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
    
    df = pd.read_excel(in_file)

    # Some of the data is shifted right
    section_row_indices1 = np.where(df[title_col1] == section_invoice_paid)[0]
    section_row_indices2 = np.where(df[title_col2] == section_invoice_paid)[0]
    section_end_row_indices = np.where(df[run_date_col] == section_end_run_date)[0]
    section_row_indices = np.concatenate( (section_row_indices1, section_row_indices2))
    section_row_indices.sort()
    
    df = clean_up_data(df)
    
    df.to_csv(join(data_dir, 'temp.csv'))

    data_rows = parse_data(section_row_index, section_end_row_index, df)

    # put all the data together
    data_frames.append(
        pd.DataFrame([
            d.__dict__ for d in data_rows
        ])
    ).to_csv(out_file)

except Exception as e:
    logging.warning(tb.format_exc())


























