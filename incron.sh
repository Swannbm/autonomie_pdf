#!/bin/bash
# set -o xtrace

####################
#         CONFIG
####################

# local
root_app=/home/swann/projets/split_pdf/split_pdf.py
venv_dir=/home/swann/.virtualenvs/autonomie
output_dir=/home/swann/projets/autonomie/tmp/ftp/

# prod serveur
# root_app=/root/auto_split/split_pdf.py
# venv_dir=/root/.local/share/virtualenvs/autonomie
# output_dir=/root/autonomie/tmp/ftp/

# no change
log_file=/var/log/autonomie/incron.sh.log
done_dir=$output_dir/pdf_done
fail_dir=$output_dir/pdf_fail


####################
#         SCRIPT
####################
# on redirige tous les outputs vers le log
exec &>> $log_file
# log sur l'event reçu et le fichier concerné
echo "$(date +'%m.%d.%Y %H:%M:%S') - event $3-$2 on $1"
# construction de la commande pour découper le PDF
todo_cmd="$root_app $1"
# log de la commande et de l'utilisateur qui va la lancer
echo "$(date +'%m.%d.%Y %H:%M:%S') - ($(whoami)) CMD ($todo_cmd)"
# activation du virtualenv contenant tous les packages requis
source $venv_dir/bin/activate
# commande de découpage
$todo_cmd &>> $log_file
# on vérifie si la commande à réussi et on déplace le PDF dans un dossier de réussit ou de fail
if [ $? -eq 0 ]; then
    echo "$(date +'%m.%d.%Y %H:%M:%S') - CMD success"
    dir=$done_dir
else
    echo "$(date +'%m.%d.%Y %H:%M:%S') - CMD fail"
    dir=$fail_dir
fi
mv $1 $dir
# log du déplacement
echo "$(date +'%m.%d.%Y %H:%M:%S') - PDF $1 moved to $dir"
# on quitte le venv
deactivate
echo "forçage des droits sur les éventuels nouveaux dossiers et fichiers"
echo "dossier chown : $output_dir"
chown www-data:www-data -R $output_dir