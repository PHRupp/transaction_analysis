
import logging
import traceback as tb
from dataclasses import asdict
from typing import List

import pandas as pd

from parser.data import DataRow


"""
Example Transaction:
9508	407	319-3606						OSORIO MARIO
9509	9/7/2023	3:45 PM	Debit	A98245	D	20	$120.01 	

Name precedes the transaction amount
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
