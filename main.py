
import logging
import os
import traceback as tb

from os.path import exists, join

import numpy as np
import pandas as pd

from parser.file_parser import clean_up, reduce_section
from parser.data import DataRow


#data_dir = 'G:/My Drive/LBA/Dry Cleaning MLX/HC/Analysis'
data_dir = 'G:/My Drive/LBA/XL SHEET FOR HUNTERS CREEK'
log_file = './results.log'
in_file_name = 'INVOICEREPORT2025-RECENT.xls'
out_file_name = 'HC_2023.csv'


if exists(log_file):
    os.remove(log_file)
logging.basicConfig(filename=log_file, level=logging.INFO)


#in_file = 'C:/Users/pathr/Downloads/SEPT2024-2025#1.xls'
in_file = join(data_dir, in_file_name)
out_file = join(data_dir, out_file_name)
df = pd.read_excel(in_file, header=None)

# Clean up the file otherwise the weird line skips are annoying
df = clean_up(df)
#df.to_csv('reduced.csv', index=False)

# Get the section indices
data_frames = []
section_ind = df.index[(df == 'Invoice Paid').sum(axis=1) > 0]
n = len(section_ind)


try:
    # process each section (one per day roughly)
    for section_start, section_end in zip(section_ind[0:(n-1)], section_ind[1:n]):

        section_data = reduce_section(section_start, section_end, df)
        data_frames.append(section_data)

    # put all the data together
    df = pd.concat(data_frames, ignore_index=True)


    df.to_csv(out_file)

except Exception as e:
    logging.warning(tb.format_exc())
