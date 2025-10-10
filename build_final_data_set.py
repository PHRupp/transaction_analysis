
import logging
import os
import traceback as tb

from os.path import join

import pandas as pd

in_file_name = 'HC_%s_final.csv'
out_file_name = 'HC_final.csv'

data_dir = 'G:/My Drive/LBA/MLX Admin/HC/Analysis/6mo Data Sets'
log_file = './logs/build_final_results.log'

in_data_file = join(data_dir, in_file_name % 'in')
paid_data_file = join(data_dir, in_file_name % 'paid')
pickup_data_file = join(data_dir, in_file_name % 'pickup')
out_file = join(data_dir, out_file_name)

# Remove the log file
if os.path.exists(log_file):
    os.remove(log_file)

logging.basicConfig(filename=log_file, level=logging.INFO)

try:
    data_in = pd.read_csv(in_data_file)
    data_paid = pd.read_csv(paid_data_file)
    data_pickup = pd.read_csv(pickup_data_file)
    data_final = pd.merge(data_in, data_paid, on='Invoice', how='outer', suffixes=('In', 'Paid'))
    data_final = pd.merge(data_final, data_pickup, on='Invoice', how='outer', suffixes=('', 'Pickup'))
    data_final['DateTimeIn'] = pd.to_datetime(data_final['DateIn'] + " " + data_final['TimeIn'])
    data_final.sort_values(by=['DateTimeIn'], inplace=True)
    print(data_final)
    print(data_final.dtypes)
    data_final.to_csv(out_file, index=False)
except Exception as e:
    logging.error(tb.format_exc())
