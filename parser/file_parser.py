
import logging
import re
import traceback as tb
from datetime import datetime
from typing import Any, List

import numpy as np
import pandas as pd

from parser.data import DataRow

PARTIAL_PHONE_NUMBER_PATTERN = '^\d{3}-\d{4}$'
PHONE_NUMBER_PATTERN = re.compile('\(\d{3}\) \d{3}-\d{4}')
TIME_FORMAT_12HR = "%I:%M %p" #"02:30 PM"


def is_partial_phone_number_format(phone_s: str) -> bool:
    is_phone_number: bool = False
    try:
        match = re.search(PARTIAL_PHONE_NUMBER_PATTERN, phone_s)
        if match is not None:
            is_phone_number = True
    except Exception as e:
        #logging.warning(tb.format_exc())
        pass
    return is_phone_number


def is_time_format(time_s: str) -> bool:
    is_time: bool = False
    try:
        d = datetime.strptime(time_s, TIME_FORMAT_12HR)
        is_time = True
    except Exception as e:
        #logging.warning(tb.format_exc())
        pass
    return is_time


def remove_rows(df: pd.DataFrame, drop_strings: List[str], columns: List[Any]) -> pd.DataFrame:

    index_list_to_drop = []

    # Build an index filter for all rows to remove
    ind = (drop_strings[0] == df[columns])
    for s in drop_strings[1:]:
        ind = ind | (s == df)
    
    # Check each row, if it has one of these strings, drop the row
    for i in ind.index:
        if ind.loc[i].sum() > 0:
            index_list_to_drop.append(i)

    # Drop the rows that contain useless data
    df.drop(index=index_list_to_drop, inplace=True)

    return df


def clean_up(df: pd.DataFrame) -> pd.DataFrame:

    index_list_to_drop = []

    # Remove empty first column
    df.drop(columns=df.columns[0:1], inplace=True)

    # Clean up the file otherwise the weird line skips are annoying
    df.dropna(axis='index', how='all', inplace=True)

    # Collection of strings that represent rows to be removed (if string is in any column)
    drop_rows_strings = [
        "Hunter's Creek",
        '3964 Town Center Blvd, Orlando,FL 32837-6103',
        'Run Date',
    ]
    remove_rows(df, drop_rows_strings, df.columns)

    # Collection of strings that represent rows to be removed (if string is in the date column)
    drop_date_col_strings = [
        'IAN',
    ]
    remove_rows(df, drop_date_col_strings, [df.columns[0]])

    return df


"""								
						Invoice Paid						
	Date	Time					FoP		Invoice	Type	Qty	Amount
	9/4/2024	4:51 PM					Debit		A104091	D	12	$71.71 
	689	272-5740	TSIFTSI SEVNTA									
	9/4/2024	5:03 PM					CASH		A104656	D	1	$32.03 
	407	376-7264	GUSMAN ERIC									
	9/4/2024	5:34 PM					Debit		A104528	L	6	$30.29 
	714	244-5456	hache nancy																	
"""
def reduce_section(
    section_row_index: int,
    section_end_row_index: int,
    df: pd.DataFrame,
) -> pd.DataFrame:
    data = []
    
    # column names after 'Invoice Paid' row, and first data row after that
    col_names_row_index = section_row_index + 1
    data_row_index = col_names_row_index + 1

    # parse which columns have the data and grab their names
    raw_cols = df.loc[col_names_row_index,:]
    col_index = df.columns[raw_cols.notna()]
    cols = df.loc[col_names_row_index, col_index]

    # Create a subset of data for just the columns with data
    reduced_df = df.loc[data_row_index:(section_end_row_index-1), col_index]
    reduced_df.reset_index(drop=True, inplace=True)
    reduced_df.columns = cols.to_list()

    # If the 'Time' column has phone numbers, then the names are over by 1 column to the right
    # This should be run before we further filter out rows in reduced_df
    reduced_df['Name'] = ''
    col_shifted_ind = reduced_df['Time'].str.contains(PARTIAL_PHONE_NUMBER_PATTERN)
    if col_shifted_ind.sum() > 0:
        reduced_df['Name'] = df.loc[data_row_index:(section_end_row_index-1), 3].to_list()
    else:

        # Otherwise, the time column has the names, parse the names out if doesn't match time format
        # Shift the phone number out of date column and into time column to be consistent
        for i in reduced_df.index:
            date_val = reduced_df.loc[i, 'Date']
            time_val = reduced_df.loc[i, 'Time']
            is_time: bool = is_time_format(time_val)
            is_phone: bool = is_partial_phone_number_format(date_val)
            reduced_df.loc[i, 'Name'] = None if is_time else time_val
            reduced_df.loc[i, 'Date'] = '000' if is_phone else date_val #not valid area-code, prevents filtering when date column is empty
            reduced_df.loc[i, 'Time'] = time_val if is_time else (date_val if is_phone else None)
        
    # Drop rows where the date column is empty. other rolumns may have
    # data, but if date is empty then we should remove the whole row
    # reduce here because it won't work during the clean up phase.
    # this is because the 'Invoice Paid' line will have empty date column
    first_col = reduced_df.columns[0]
    drop_ind = reduced_df.index[reduced_df[first_col].isna()]
    reduced_df.drop(index=drop_ind, inplace=True)
    
    return reduced_df


def parse_reduced_df(df: pd.DataFrame):

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
	Date	Time					FoP		    Invoice	Type	Qty	Amount
9/3/2024	8:47 AM					Debit		A103844	   L	  4	$23.96 
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

