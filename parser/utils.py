
import re
from datetime import datetime
from os.path import join


# CONSTANTS
run_date_col = 'Unnamed: 1'
title_col1 = 'Unnamed: 6'
title_col2 = 'Unnamed: 7'
section_title = "Hunter's Creek"
section_invoice_in = 'Invoice In Report'
section_invoice_paid = 'Invoice Paid'
section_invoice = {
    'in': section_invoice_in,
    'ready': section_invoice_paid,
    'pickup': section_invoice_paid,
    'paid': section_invoice_paid,
}
section_end_run_date = 'Run Date'

INVOICE_PATTERN = '^A\d+$'
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
