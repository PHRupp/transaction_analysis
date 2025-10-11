
import logging
import os
import re
import traceback as tb
from os.path import join
from typing import List

import pandas as pd
import numpy as np

from parser.utils import AREA_CODE_PATTERN, PHONE_NUMBER_PATTERN_ONLY

pd.options.mode.chained_assignment = None  # default is 'warn'

in_file_name = 'HC_final.csv'
out_file_name = 'HC_customer_phone.csv'

data_dir = 'G:/My Drive/LBA/MLX Admin/HC/Analysis/6mo Data Sets'
log_file = './logs/customer_phone_results.log'

in_file = join(data_dir, in_file_name)
out_file = join(data_dir, out_file_name)

# Remove the log file
if os.path.exists(log_file):
    os.remove(log_file)

logging.basicConfig(filename=log_file, level=logging.INFO)


def is_phone_missing_area_code(ph: str) -> bool:
    return '(000)' in ph


def is_valid_phone(ph: str) -> bool:
    if not type(ph) == str:
        ph = ''
    return (re.match(PHONE_NUMBER_PATTERN_ONLY, ph) is not None) and (not is_phone_missing_area_code(ph))


def fix_phone_number(phone_numbers: List[str]) -> str:
    phone = None
    phone_numbers = [p for p in phone_numbers if p is not None]
    phone_numbers = [p for p in phone_numbers if type(p) == str]

    # return valid phone
    for ph in phone_numbers:
        if is_valid_phone(ph):
            return ph

    # fix the phone numbers
    area_code = '(000)'
    phone_without_area_code = '000-0000'
    for ph in phone_numbers:

        # Get the area code
        area_code_match = re.match(AREA_CODE_PATTERN, ph)
        if (area_code_match is not None) and not is_phone_missing_area_code(ph):
            area_code = area_code_match.group(1)

        # get the final 7 digits
        phone_match = re.match(PHONE_NUMBER_PATTERN_ONLY, ph)
        if (phone_match is not None) and is_phone_missing_area_code(ph):
            phone_without_area_code = phone_match.group(1)

    # Combine the new phone and check to make sure it's valid
    new_phone = area_code + " " + phone_without_area_code
    if not is_phone_missing_area_code(new_phone) and not "000-0000" in new_phone:
        return new_phone

    return phone


def get_unique_customer_phone(df: pd.DataFrame) -> pd.DataFrame:
    data_out = []
    keep_cols = [
        'CustomerNameIn', 'PhoneNumberIn',
        'CustomerNamePaid', 'PhoneNumberPaid',
        'CustomerName', 'PhoneNumber',
    ]
    df = df[keep_cols]

    # Fill in the Customer name from whatever is populated
    df.loc[:,'Customer'] = df['CustomerNameIn']
    customer_na = df['Customer'].isna().to_list()
    df.loc[customer_na, 'Customer'] = df.loc[customer_na, 'CustomerNamePaid']
    customer_na = df['Customer'].isna().to_list()
    df.loc[customer_na, 'Customer'] = df.loc[customer_na, 'CustomerName']

    # 
    for name in df['Customer'].unique():
        name_ind = (df['Customer'] == name)
        phones_in = df.loc[name_ind, 'PhoneNumberIn'].to_list()
        phones_paid = df.loc[name_ind, 'PhoneNumberPaid'].to_list()
        phones = df.loc[name_ind, 'PhoneNumber'].to_list()
        all_phones = phones_in + phones_paid + phones
        phone = fix_phone_number(all_phones)
        if phone is not None:
            data_out.append([name, phone])

    return pd.DataFrame(data_out, columns=['Name', 'Phone'])


try:
    data_in = pd.read_csv(in_file)
    data_out = get_unique_customer_phone(data_in)
    data_out.sort_values(by='Name', inplace=True)
    print(data_out)
    data_out.to_csv(out_file, index=False)
except Exception as e:
    logging.error(tb.format_exc())
