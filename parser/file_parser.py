
import logging
import re
import traceback as tb
from dataclasses import asdict
from datetime import datetime
from os.path import join
from typing import Any, List

import numpy as np
import pandas as pd

from parser.data import DataRow


# CONSTANTS
run_date_col = 'Unnamed: 1'
title_col1 = 'Unnamed: 6'
title_col2 = 'Unnamed: 7'
section_title = "Hunter's Creek"
section_invoice_paid = 'Invoice Paid'
section_end_run_date = 'Run Date'

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
        reduced_df['Name'] = df.loc[data_row_index:(section_end_row_index-1), 'Unnamed: 3'].to_list()
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

    # keep the strings consistent by having upper case
    reduced_df['Name'] = reduced_df['Name'].str.upper()

    # Drop rows where the date column is empty. other rolumns may have
    # data, but if date is empty then we should remove the whole row
    # reduce here because it won't work during the clean up phase.
    # this is because the 'Invoice Paid' line will have empty date column
    first_col = reduced_df.columns[0]
    drop_ind = reduced_df.index[reduced_df[first_col].isna()]
    reduced_df.drop(index=drop_ind, inplace=True)

    # Remove lines representing the person who grabbed the data
    ind_delete = reduced_df['Date'] == 'IAN'
    reduced_df.drop(reduced_df.loc[ind_delete,:].index, inplace=True)

    # Data where row has 'Dry Cleaning' and everything after should be destroyed
    is_end = reduced_df['Date'] == 'Dry Cleaning'
    if is_end.sum() > 0:
        stop_ind = reduced_df.loc[is_end, :].index[0]
        drop_ind = reduced_df.loc[reduced_df.index >= stop_ind, :].index
        reduced_df.drop(drop_ind, inplace=True)

    return reduced_df


def reduce_file(in_file: str) -> List[DataRow]:
    
    data_frames: List[DataRow] = []

    raw_df = pd.read_excel(in_file)

    # Clean up the file otherwise the weird line skips are annoying
    raw_df.dropna(how='all', inplace=True, ignore_index=True)

    # Some of the data is shifted right
    section_row_indices1 = np.where(raw_df[title_col1] == section_invoice_paid)[0]
    section_row_indices2 = np.where(raw_df[title_col2] == section_invoice_paid)[0]
    section_end_row_indices = np.where(raw_df[run_date_col] == section_end_run_date)[0]
    section_row_indices = np.concatenate( (section_row_indices1, section_row_indices2))
    section_row_indices.sort()

    # process each section (one per day)
    for section_row_index, section_end_row_index in zip(section_row_indices, section_end_row_indices):
        try:
            section_df = reduce_section(section_row_index, section_end_row_index, raw_df)
            data_frames.append(section_df)
        except Exception as e:
            logging.warning(tb.format_exc())

    return data_frames


def parse_reduced_df(df: pd.DataFrame) -> pd.DataFrame:

    data: List[DataRow] = []

    # Loop through all names and process their transactions
    name_ind = df.index[df['Name'].notna()].to_list()
    for i_name, i_next_name in zip(name_ind, name_ind[1:] + [df.index.to_list()[-1]+1]):

        # Loop through each transaction under name and process
        for i_transaction in range(i_name+1,i_next_name):
            try:
                data_row = parse_transaction(i_name, i_transaction, df)
                data.append(data_row)

            except Exception as e:
                logging.warning(tb.format_exc())

    # Recombine into final data frame
    data = pd.DataFrame([asdict(d) for d in data])

    return data


"""
Example Transaction:
9/3/2024	8:47 AM					Debit		A103844	L	4	$23.96 
407	937-9448	PORCELLA STEFANO									
"""
def parse_transaction(
    name_index: int,
    transaction_index: int,
    df: pd.DataFrame,
) -> DataRow:

    # Parse the phone number
    area_code = df.loc[name_index, 'Date']
    other_phone_digits = df.loc[name_index, 'Time']
    phone_number = f'({area_code}) {other_phone_digits}'

    # return the data record
    data_row = DataRow(
        Date=df.loc[transaction_index, 'Date'],
        Time=df.loc[transaction_index, 'Time'],
        FoP=df.loc[transaction_index, 'FoP'],
        Invoice=df.loc[transaction_index, 'Invoice'],
        TransactionType=df.loc[transaction_index, 'Type'],
        Qty=int(df.loc[transaction_index, 'Qty']),
        Amount=df.loc[transaction_index, 'Amount'],
        CustomerName=df.loc[name_index, 'Name'],
        PhoneNumber=phone_number,
    )
    
    return data_row

