import logging
import os 
import re

LOG_LEVEL = logging.INFO
OUTPUT_DIR = '/home/swann/projets/autonomie/tmp/ftp'
LOG_DIR = '/var/log/autonomie'
SUCESS_DIR = os.path.join(OUTPUT_DIR, 'pdf_done')
FAIL_DIR = os.path.join(OUTPUT_DIR, 'pdf_fail')

CHECK_FILENAME = r'(?P<DOCTYPE>salaire|tresorerie)_(?P<YEAR>[0-9]+)_(?P<MONTH>[^_]+)\.pdf'
#FIND_ANCODE = r'NAF(?P<ANCODE>[a-zA-Z0-9]+)[ ]+Salaire'
#FIND_NAME = r'Virement     (Mme|Mlle|M)( )?(?P<NAME>[\w \-]*?)[ ]{20,40}'
# changed 201811 for handle new salary roll
#FIND_ANCODE = r'(?P<ANCODE>[a-zA-Z0-9]+)[ ]+(R.mun.ration fixe|Cong. sans solde)'
FIND_ANCODE = r'(NAF)?(?P<ANCODE>[a-zA-Z0-9]+)[ ]+(R.mun.ration fixe|Cong. sans solde|Salaire mensuel)'
FIND_NAME = r'Cat.gorie(Cadre|Employ. non cadre)[ ]+(Mme|Mlle|M)[ ]*(?P<NAME>[\w \-]*?)[ ]+'
# end change
FLAGS = re.MULTILINE | re.IGNORECASE | re.UNICODE