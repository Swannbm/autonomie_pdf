import logging
import os 
import re

LOG_LEVEL = logging.INFO
OUTPUT_DIR = '/home/swann/projets/autonomie/tmp/ftp'
LOG_DIR = '/var/log/autonomie'
SUCESS_DIR = os.path.join(OUTPUT_DIR, 'pdf_done')
FAIL_DIR = os.path.join(OUTPUT_DIR, 'pdf_fail')