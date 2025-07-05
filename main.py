
import logging
import os
import re
import traceback as tb

from os.path import join
from typing import List

import numpy as np
import pandas as pd

from parser.file_parser import reduce_file
from parser.data import DataRow

"""
WARNING: Processing XLSX files instead of the XLS provides more data. Not sure why, but it 
parses the XLS and has missing area codes or phone numbers, but it's fully populated in XLSX.
"""

in_file_names = [
    '2023Q12.xlsx',
    '2023Q34.xlsx',
    '2024Q12.xlsx',
    '2024Q34.xlsx',
]


data_dir = 'G:/My Drive/LBA/MLX Admin/HC/Analysis/6mo Data Sets'
log_file = './results.log'
out_file_name = 'HC.csv'

try:
    os.remove(log_file)
except FileNotFoundError:
    print(tb.format_exc())

out_file = join(data_dir, out_file_name)

logging.basicConfig(filename=log_file, level=logging.INFO)

data_frames: List[DataRow] = []

for f in in_file_names:
    try:
        in_file = join(data_dir, f)
        data_frames += reduce_file(in_file)
    except Exception as e:
        print('FILE ERROR!')
        logging.warning(tb.format_exc())

# put all the data together
pd.concat(data_frames, ignore_index=True).to_csv(out_file)
