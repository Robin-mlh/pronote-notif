## Pronote-notif

> **Notifier l'activité pronote.**

## Description

__Pronote-notif vous notifie par mail en cas de nouvelle note, nouvelle information ou en cas de cours annulé.__
L'API [pronotepy](github.com/bain3/pronotepy) est utilisée, les ENT sont donc supportés pour se connecter à Pronote.
Ce script est adapté à une utilisation serveur avec un système de log et de fichier de configuration.

## Installation et Usage sur GNU+Linux

Python 3 est requis, ainsi que l'API pronotepy:

    pip3 install https://github.com/bain3/pronotepy/archive/refs/heads/master.zip

###
Tout d'abord, __vous devez définir vos paramètres (identifiants, mail, etc) dans le fichier de configuration__ ```pronote-notif.conf```.
Vous devrez configurer un compte mail avec accès smtp pour envoyer les notifications. [Voilà comment faire avec Gmail.](https://support.google.com/mail/answer/7126229?hl=fr#zippy=%2C%C3%A9tape-modifier-les-param%C3%A8tres-smtp-et-les-autres-param%C3%A8tres-dans-votre-client-de-messagerie)
Vous pouvez aussi modifier plus de chose directement dans le fichier ```pronote-notif.py```. Par exemple, désactiver les notifications pour un certain type d'activité (ligne 200).


Lancez le script après lui avoir donné la permission nécessaire:

    sudo chmod +x tkp.py
    ./tkp.py

Pour exécuter le script toutes les 30 minutes par exemple, sur Ubuntu le plus simple est d'utiliser cron:
    
    crontab -e

Ajoutez cette ligne, en remplaçant ```pronote-notif.py``` par le bon chemin:
    
    */30 * * * * ./pronote-notif.py
    
Vérifiez ensuite que la tâche a bien été ajoutée:

    crontab -l


#### Pour lire les logs:
Par exemple pour voir si tout marche bien ou pour régler un problème, ouvrez le fichier ```pronote-notif.log```:

    tail -n 13 pronote-notif.log


## Contact, contributions et plus

***L'aide et les retours sont bienvenus !***

Mail: dev_contactmail@protonmail.com
