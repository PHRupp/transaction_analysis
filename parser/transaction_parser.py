
import logging
import traceback as tb
from dataclasses import asdict
from typing import Any, List

import pandas as pd

from parser.data import DataRowIn, DataRowReady, DataRowPaid, DataRowPickup


"""
Date	 Time	 Inv #	Type	Route	Fast Ticket	Qty	Discount	Amount	Name
407									                                        SMITH SHIRLEY
1/2/2018 8:18 AM A66210	D			                15	$0.00 	    $88.54 	

Name precedes the transaction amount
"""
def parse_transaction_in(
    name_index: int,
    transaction_index: int,
    df: pd.DataFrame,
) -> DataRowPickup:

    # Parse the phone number
    area_code = df.loc[name_index, 'Date']
    other_phone_digits = df.loc[name_index, 'Time']
    phone_number = f'({area_code}) {other_phone_digits}'

    # return the data record
    data_row = DataRowIn(
        Date=df.loc[transaction_index, 'Date'],
        Time=df.loc[transaction_index, 'Time'],
        Invoice=df.loc[transaction_index, 'Inv #'],
        TransactionType=df.loc[transaction_index, 'Type'],
        Qty=int(df.loc[transaction_index, 'Qty']),
        Amount=df.loc[transaction_index, 'Amount'],
        CustomerName=df.loc[name_index, 'Name'],
        PhoneNumber=phone_number,
    )
    return data_row


"""
Example Transaction:
Date	  Time	    FoP	    Invoice	Type	Qty	Amount	Name
407	      501-0280						                VIANNA PEDRO
1/2/2018  8:28 AM	VISA	A66141	L	    3	$9.15 	

Name precedes the transaction amount
"""
def parse_transaction_paid(
    name_index: int,
    transaction_index: int,
    df: pd.DataFrame,
) -> DataRowPaid:

    # Parse the phone number
    area_code = df.loc[name_index, 'Date']
    other_phone_digits = df.loc[name_index, 'Time']
    phone_number = f'({area_code}) {other_phone_digits}'

    # return the data record
    data_row = DataRowPaid(
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


"""
Example Transaction:
Date	  Time	    FoP	    Invoice	Type	Qty	Amount	Name
407	      501-0280						                VIANNA PEDRO
1/2/2018  8:28 AM	VISA	A66141	L	    3	$9.15 	

Name precedes the transaction amount
"""
def parse_transaction_pickup(
    name_index: int,
    transaction_index: int,
    df: pd.DataFrame,
) -> DataRowPickup:

    # Parse the phone number
    area_code = df.loc[name_index, 'Date']
    other_phone_digits = df.loc[name_index, 'Time']
    phone_number = f'({area_code}) {other_phone_digits}'

    # return the data record
    data_row = DataRowPickup(
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


def parse_reduced_df(df: pd.DataFrame, dataset: str) -> pd.DataFrame:

    # Data Row objects depending on type of dataset
    data: List[Any] = []

    parse_transaction_funcs = {
        'in': parse_transaction_in,
        #'ready': parse_reduced_df_ready,
        'paid': parse_transaction_paid,
        'pickup': parse_transaction_pickup,
    }
    parse_transaction_func = parse_transaction_funcs[dataset]

    # Loop through all names and process their transactions
    name_ind = df.index[df['Name'].notna()].to_list()
    for i_name, i_next_name in zip(name_ind, name_ind[1:] + [df.index.to_list()[-1]+1]):

        # Loop through each transaction under name and process
        for i_transaction in range(i_name+1,i_next_name):
            try:
                data_row = parse_transaction_func(i_name, i_transaction, df)
                data.append(data_row)

            except Exception as e:
                logging.warning(tb.format_exc())

    # Recombine into final data frame
    data = pd.DataFrame([asdict(d) for d in data])

    return data
