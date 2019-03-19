import logging
import os

# local
OUTPUT_DIR = '/home/swann/projets/autonomie/tmp/ftp'
LOG_DIR = '/var/log/autonomie'
LOG_LEVEL = logging.INFO

# prod 
# LOG_LEVEL = logging.INFO
# OUTPUT_DIR = '/root/autonomie/tmp/ftp'
# LOG_DIR = '/var/log/autonomie'

# no change
SUCESS_DIR = os.path.join(OUTPUT_DIR, 'pdf_done')
FAIL_DIR = os.path.join(OUTPUT_DIR, 'pdf_fail')