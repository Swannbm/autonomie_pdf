# coding: utf-8
from PyPDF2 import PdfFileReader
import re
import os
import unidecode
import unicodedata

os.system("clear")

#FIND_ANCODE = r'NAF(?P<ANCODE>[a-zA-Z0-9]+)[ ]+Salaire'
FIND_ANCODE = r'(NAF)?(?P<ANCODE>[a-zA-Z0-9]+)[ ]+(R.mun.ration fixe|Cong. sans solde|Salaire mensuel)'
#FIND_NAME = r'Virement     (Mme|Mlle|M)( )?(?P<NAME>[\w \-]*?)[ ]{20,40}'
FIND_NAME = r'Cat.gorie(Cadre|Employ. non cadre)[ ]+(Mme|Mlle|M)[ ]*(?P<NAME>[\w \-]*?)[ ]{2,}'
FLAGS = re.MULTILINE | re.IGNORECASE | re.UNICODE

#temp_file = 'salaire_2018_10.PDF'
temp_file = 'salaire_2019_01.PDF'
with open(temp_file, 'rb') as f:
    temp_pdf = PdfFileReader(f)
    for i, page in enumerate(temp_pdf.pages):
        text = temp_pdf.getPage(i).extractText()
        
        try:
            # recherche de l'ANCODE et du NAME
            ancode = re.search(FIND_ANCODE, text, flags=FLAGS).group('ANCODE')
            name = re.search(FIND_NAME, text, flags=FLAGS).group('NAME')
            name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore')
            print('{}: {} / {}'.format(i, name, ancode))
        except Exception as e:
            print(e)
            # Les regex n'ont pas permis de trouver toutes les informations
            # on log une erreur et on passe le retour de la fonction à False
            print('-'*20)
            print(text)
            print('-'*20)
            print(FIND_ANCODE)
            print(FIND_NAME)
        del ancode, name