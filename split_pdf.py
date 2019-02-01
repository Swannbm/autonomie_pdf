#!/home/swann/.virtualenvs/autonomie/bin/python
# coding=utf-8

# liste des imports requis
import argparse
import os
import sys
import logging
import logging.handlers
import re
import unidecode
import unicodedata
from PyPDF2 import PdfFileWriter, PdfFileReader

####################
#         CONFIG
####################

from config import *

####################
#         SCRIPT
####################

# initialiser le logger
logger = logging.getLogger(__name__)
# déclaration des variables globales
arguments = None

def main():
    """
        Fonction principale appelée par if __name__ = 'main'.
        Récupère les arguments utilisés.
        Fait une boucle sur la liste des fichiers passés en arguments et les traite
        un par un.
    """
    logger.info('Start running split_pdf.py')
    
    # gestion des arguments à passer aux scripts
    parser = argparse.ArgumentParser(description='Sage files parsing')
    parser.add_argument(
        'files',
        type=argparse.FileType('rb'),
        help='pdf filename named DOCTYPE_YEAR_MONTH.pdf',
        nargs='+'
    )
    parser.add_argument(
        '-r',
        '--restrict',
        help="Restrict to n first pages",
        type=int,
        default=0
    )
    arguments = parser.parse_args()
    logger.info('Arguments : {}'.format(arguments))

    total = len(arguments.files)        # nombre de fichiers à traiter
    success = 0
    for fileStream in arguments.files:
        if process_file(fileStream):
            result = 'success'
            success += 1
        else:
            result = 'errors'
        logger.debug('file {} processed with {}'.format(fileStream.name, result))
    
    logger.info('{} / {} ({}%) files processed'.format(success, total, int((1.0*success / total)*100)))
    
    # Si on a eu autant de succès qu'il y a de fichiers, on renvoit TRUE
    if success == total:
        return True
    else:
        return False


def process_file(fileStream):
    """
        Cette fonction va traiter un fichier PDF exporter par Sage de Port Parallele. 
        Il y a 2 fichiers traitables : celui qui contient toutes les fiches de paies et
        celui qui indique la trésorerie de tous les entrepreneurs. 
        Cette fonction va les lires et les découper pour que chaque entrepreneur ait un
        fichier avec sa feuille de paie seulement ou son solde de trésorerie seulement.
        Le fichier de trésorerie va être découpé en fonction de son sommaire. 
        Le fichier des salaires sera découpé page par page (il n'y a pas de sommaire)
        
        :return: Renvoi True si tout s'est bien passé sinon False
        :rtype: bool

        :param fileStream: un fichier déjà ouvert avec la fonction open('rb')
        :type fileStream: file object

        .. warning:: la regex pour vérifier le nom du fichier : 
                    r'(?P<DOCTYPE>salaire|tresorerie)_(?P<YEAR>[0-9]+)_(?P<MONTH>[^_]+)\.pdf'
                    exemples: salaire_2018_06.pdf, tresorerie_2017_12.pdf...
                    https://regex101.com/r/sOJAYq/1
        .. todo:: ajouter des exceptions pour traiter les erreurs et faciliter la maintenance
    """
    # Vérifier que le nom du fichier respecte la nomenclature
    filename = os.path.split(fileStream.name)[-1]
    logger.info('Processing {}'.format(filename))

    parsed = re.search(CHECK_FILENAME, filename, flags=FLAGS)
    if not parsed:
        logger.error('{} is not a correct file name. Expected format : [salaire|trésorerie]_[YYYY]_[MM].pdf'.format(filename))
        return False
    
    # Créer l'arbo d'arrivée
    # ex : /path/from/param/salaire/2018/06
    output_path = os.path.join(
        OUTPUT_DIR, 
        parsed.group('DOCTYPE'), 
        parsed.group('YEAR'),
        parsed.group('MONTH'),
    )
    logger.info('Output_path={}'.format(output_path))
    if not os.path.isdir(output_path):
        logger.debug('Create output_path')
        os.makedirs(output_path)

    # ouverture du flux de lecture du fichier PDF
    pdf = PdfFileReader(fileStream)
    logger.info('PDF opened, contains {} pages'.format(pdf.getNumPages()))

    # choix du traitement en fonction du type de fichier
    logger.info('Processing a {} PDF'.format(parsed.group('DOCTYPE')))
    if parsed.group('DOCTYPE')=='tresorerie':
        return cut_using_outlines(pdf, output_path)
    elif parsed.group('DOCTYPE')=='salaire':
        return cut_using_text(pdf, output_path)
    else:
        logger.error('{} est un début de nom de fichier inconnu'.format(parsed.group('DOCTYPE')))
        return False




def cut_using_text(pdf, output_path):
    """
        Cette fonction va découper le pdf des salaires. Chaque fiche de salaire n'occupe
        qu'une seule page. On va commencer par découper toutes les pages et les écrires
        au bon endroit avec un nom temporaire.
        Ensuite on va lire chaque fichier pdf temporaire et rechercher les données 
        nécessaires au nommage correcte (ie : ANCODE_ENTREPRENEUR.pdf)

        :param pdf: ancien pdf que l'on va analyser et découper
        :type pdf: PdfFileReader
        :param output_path: chemin absolu vers le dossier qui contiendra les nouveaux pdf
        :type output_path: str

        :return: Renvoit True si tout s'est bien passé sinon False
        :rtype: bool

        .. warning:: fonction réservée au fichier de salaire
    """
    # la foncition renvoi succes_flag à la toute fin
    # si une erreur est constatée, il faut changer le flag à False
    succes_flag = True

    # première étape, on écrit tous les fichiers résultats
    # on les nomme 'temp_p[X].pdf' avec [X] le numéro de la page
    temp_files = []
    nb_pages = pdf.getNumPages()
    for i, page in enumerate(pdf.pages):
        new_pdf_filepath = os.path.join(output_path, 'temp_p{:0>4}.pdf'.format(i))
        with open(new_pdf_filepath, 'wb') as f_out:
            pdf_writer = PdfFileWriter()
            pdf_writer.addPage(page)
            pdf_writer.write(f_out)
        temp_files.append(new_pdf_filepath)
    logger.info('{}/{} temporary pdf wrote'.format(len(temp_files), nb_pages))

    # Maintenant, on va ouvrir chaque pdf 'temp' et en extraire le texte
    # grâce à 2 regex FIND_ANCODE & FIND_NAME on va récupérer le code comptable 
    # et le nom de l'entrepreneur. On se sert de ces 2 informations pour renommer le pdf
    # [ANCODE]_[NAME].pdf
    cpt_renamed = 0
    for i, temp_file in enumerate(temp_files):
        new_name = None
        with open(temp_file, 'rb') as f:
            temp_pdf = PdfFileReader(f)
            # extraction du texte
            text = temp_pdf.getPage(0).extractText()
            try:
                # recherche de l'ANCODE et du NAME
                ancode = re.search(FIND_ANCODE, text, flags=FLAGS).group('ANCODE')
                ancode = unix_sanitize(ancode)
                name = re.search(FIND_NAME, text, flags=FLAGS).group('NAME')
                name = unix_sanitize(name)
                new_name ='{}_{}.pdf'.format(ancode, name)
            except:
                # Les regex n'ont pas permis de trouver toutes les informations
                # on log une erreur et on passe le retour de la fonction à False
                logger.debug(text)
                logger.debug(FIND_ANCODE)
                logger.debug(FIND_NAME)
                succes_flag = False
        # s'il n'y a pas eu d'erreur avec les regex, new_name contient une valeur
        if new_name:
            new_path = os.path.join(output_path, new_name)
            os.rename(temp_file, new_path)
            logger.debug('{} renamed {}'.format(temp_file, new_name))
            cpt_renamed += 1
    
    # vérification que tous les PDF ont bien été renommés
    if cpt_renamed == nb_pages:
        logger.info('All {} temporary pdf renamed'.format(cpt_renamed))
    else:
        logger.error('Only {} temporary pdf renamed on {}'.format(cpt_renamed, nb_pages))
        succes_flag = False
    return succes_flag


def cut_using_outlines(pdf, output_path):
    """
        Cette fonction va découper le pdf en fonction de son sommaire. Elle est utilisée 
        pour les fichier de trésorerie. Le sommaire d'un PDF de trésorerie est constitué de
        la façon suivante :

        |-- RS
        |   |-- MACE06
        |   |   |-- BEAUFILS Sander
        |   |-- 001ARN
        |   |   |-- ARNAIZ David
        | [...]
        |-- Solde de Treso
        |   |-- MACE06
        |   |   |-- BEAUFILS Sander
        |   |-- 001ARN
        |   |   |-- ARNAIZ David
        | [...]
       
        - RS et Solde de Treso sont les entrées de premiers niveaux. Seul RS nous intéresse
        - MACE06, 001ARN... sont les entrées de deuxième niveau et elles contiennent les 
        ANCODE, compte comptable qui fait le lien entre les PDF et l'utilisateur dans autonomie
        - BEAUFILS Sander, ARNAIZ David... sont les noms des entrepreneurs. Ces entrées
        sont utilisées dans le nom douveau fichier à des fins de débuggage seulement

        :param pdf: ancien pdf que l'on va analyser et découper
        :type pdf: PdfFileReader
        :param output_path: chemin absolu vers le dossier qui contiendra les nouveaux pdf
        :type output_path: str

        :return: Renvoit True si tout s'est bien passé sinon False
        :rtype: bool

        .. warning:: fonction réservée au fichier de trésorerie
    """
    # on récupère le sommaire du pdf
    sommaire_entier = pdf.getOutlines()
    
    # le sommaire contient 2 entrées de niveau 1 (RS et Solde de tréso)
    # on conserve uniquement les entrées sous RS
    # sommaire[0] : titre de la première section (aka. RS)
    # sommaire[1] : liste de toutes les entrées de la première section
    # sommaire[2] : titre de la seconde section (aka. solde de...)
    sommaire = sommaire_entier[1]

    # on récupère la dernière page de la première section
    last_page = pdf.getDestinationPageNumber(sommaire_entier[2])

    # maintenant on traite les entrée 2 par 2
    # la première contient le code comptable
    # la deuxième entrée contient une liste d'un seul élément avec le nom de l'entrepreneur
    
    start_page = pdf.getDestinationPageNumber(sommaire[0])
    ancode = name = end_page = None
    for i in xrange(0,len(sommaire),2):
        # la page de cette section est la page de fin de la section précédente
        end_page = pdf.getDestinationPageNumber(sommaire[i])
        if ancode is not None:
            # c'est au moins la deuxième fois que la boucle itère
            # on peut donc écrire la page précédente (ie : on écrit la page 0 quand on lit la page 1)
            
            # chemin du nouveau pdf à écrire
            new_pdf_filepath = os.path.join(output_path, '{}_{}.pdf'.format(ancode, name))
            # appelle à la fonction d'écriture du nouveau pdf
            write_pdf_extract(pdf, new_pdf_filepath, start_page, end_page)
            # la page de cette section est la page de départ de la prochaine écriture
            start_page = end_page
        # récupération des intitulé de l'entrée en cours et de l'entrée suivante
        # ex : MACE06
        ancode = unix_sanitize(sommaire[i].title)
        # l'entrée suivante est une liste de 1 élément
        # ex : BEAUFILS Sander
        name = unix_sanitize(sommaire[i+1][0].title)
    
    # comme on a un décalage dans l'écriture des pages, la dernièe n'est pas encore écrite
    new_pdf_filepath = os.path.join(output_path, '{}_{}.pdf'.format(ancode, name))
    # attention, la dernière page est celle de la seconde section (voir ci-dessus)
    write_pdf_extract(pdf, new_pdf_filepath, start_page, last_page)
    return True

def write_pdf_extract(pdf, new_pdf_filepath, start_page, end_page):
    """
        Cette fonction écrit un nouveau PDF à partir des pages d'un ancien pdf

        :param PdfFileReader pdf : ancien pdf d'où les pages vont être extraites
        :param str new_pdf_filepath : chemin absolu vers le nouveau pdf qui va être écrit
        :param int start_page : première page de l'extrait (inclue au nouveau pdf)
        :param int end_page : dernière page de l'extrait à récupéré (exclue du nouveau pdf)
        
        .. warning:: la dernière page (end_page) n'est pas inclues dans le nouveau PDF
    """
    logger.debug('write {} with pages {} to {}'.format(new_pdf_filepath, start_page, end_page))
    with open(new_pdf_filepath, 'wb') as f_out:
        pdf_writer = PdfFileWriter()
        # on ajoute toutes les pages manquantes
        for i in range(start_page, end_page):
            pdf_writer.addPage(pdf.getPage(i))
        pdf_writer.write(f_out)
    


_NOSPACES = re.compile(r'[-\s]+')
_UNIX_VALID = re.compile(r'[^\w\s-]')
def unix_sanitize(value):
    """
    Normalise le texte pour pouvoir être utilisé comme nom de fichier
    :param value: texte à normaliser
    :type value: str
    :return: texte normalisé
    :rtype: unicode
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(_UNIX_VALID.sub('', value).strip())
    return _NOSPACES.sub('-', value)

# démarrage du script
if __name__ == '__main__':
    #initialiser les loggers
    logger.setLevel(LOG_LEVEL)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file_path = os.path.join(LOG_DIR, 'split_pdf.log')
    fh = logging.handlers.RotatingFileHandler(log_file_path, backupCount=5)
    ch = logging.StreamHandler()
    fh.setLevel(LOG_LEVEL)
    ch.setLevel(LOG_LEVEL)
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.info('Logging in file {}'.format(log_file_path))

    # execution du script
    if main(): sys.exit(0) # success
    else: sys.exit(1) # failure