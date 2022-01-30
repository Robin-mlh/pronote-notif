#!/usr/bin/python3

""" Notifier par mail l'activité pronote. """

import os
import datetime
import pickle
import logging
import configparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pronotepy
from pronotepy.ent import *

LOG_FICHIER = "pronote-notif.log"
LOG_FORMAT = '%(asctime)s  %(levelname)s %(message)s'
CONF_FICHIER = "pronote-notif.conf"
DB_FICHIER = "db-pronote-notif.pickle"
DOSSIER = os.getcwd()
os.chdir(DOSSIER)


def notif_notes():
    """ Envoi un mail contenant les nouvelles notes, s'il y en a. """

    # Récupère la totalité des notes de ce trimestre depuis Pronote.
    notes_maj = client.current_period.grades
    if not dict_database["notes"]:
        logging.info("notif_notes - Liste des notes connues vide: "
                     "enregistrement des notes dans la liste.")
        # Si la liste des informations connues est vide, la recréer.
        for note in notes_maj:
            dict_database["notes"].append(str(note.date) + note.grade)
        enregistre_donnees_fichier(dict_database)
    else:
        logging.info("notif_notes - Cherche les notes non connues.")
        nouvelles_notes = []
        # Parcours la liste des notes mises à jour.
        for note in notes_maj:
            if (str(note.date) + note.grade) not in dict_database["notes"]:
                # Si la note n'est pas présente dans la liste des notes deja connues.
                nouvelles_notes.append(note)  # La note est nouvelle.
                dict_database["notes"].append(str(note.date) + note.grade)

        if nouvelles_notes:  # Si la liste des nouvelles notes n'est pas vide.
            enregistre_donnees_fichier(dict_database)
            notes_contenu_mail = ""
            for note in nouvelles_notes:
                notes_contenu_mail = (f" * {note.grade}/{note.out_of} - {note.subject.name}"
                                      f"\nle {str(note.date)}"
                                      f"\ncoeff: {note.coefficient} "
                                      f"\nmoyenne classe: {note.average}"
                                      f"\nnote max: {note.max}"
                                      f"\n note min: {note.min}\n\n")
            envoi_mail("Nouvelle note - Notification Pronote",
                       "Notification Pronote - Bot pronote-notif\n\n"
                       f"### Nouvelle note:\n{notes_contenu_mail}")


def notif_annulation_cours():
    """ Envoi un mail contenant les cours annulés. """

    cours_contenu_mail = ""
    logging.info("notif_annulation_cours - Compilation des cours annulés des "
                 f"{config['Pronote']['ANALYSE_NB_JOURS']} prochains jours.")
    for jour in range(int(config["Pronote"]["ANALYSE_NB_JOURS"])):
        # Récupère l'emploi du temps quotidien d'aujourd'hui jusqu'à
        # aujourd'hui + config["Pronote"]["ANALYSE_NB_JOURS"].
        date = datetime.date.today() + datetime.timedelta(days=jour)
        for cour in client.lessons(date):
            # Parcours les cours de la journée.
            if cour.canceled:  # Si le cours est annulé.
                if str(cour.start) not in dict_database["cours_annules"]:
                    # Si le cours n'est pas deja présent dans la liste des cours annulés.
                    cours_contenu_mail += (f" {cour.start.strftime('%d//%m/%Y')} "
                                           f"{cour.start.strftime('%H')}h-{cour.end.strftime('%H')}"
                                           f"h: {cour.subject.name}\n")
                    dict_database["cours_annules"].append(str(cour.start))
    if cours_contenu_mail != "":  # S'il y a des nouveaux cours annulés.
        enregistre_donnees_fichier(dict_database)
        envoi_mail("Annulation de cours - Notification Pronote",
                   "Notification Pronote - Bot pronote-notif\n\n"
                   f"### Cours annulé:\n{cours_contenu_mail}")


def notif_informations():
    """ Envoi un mail concernant les nouvelles informations. """

    # Récupère la totalité des informations depuis Pronote.
    informations_maj = client.information_and_surveys()
    if not dict_database["informations"]:
        logging.info("notif_informations - Liste des informations connues vide: "
                     "enregistrement des informations dans la liste.")
        # Si la base de donnée des informations connues est vide, la recréer.
        for info in informations_maj:
            dict_database["informations"].append(info.title)
        enregistre_donnees_fichier(dict_database)
    else:
        logging.info("notif_informations - Cherche les informations non connues.")
        nouvelles_infos = []
        # Parcours la liste des informations mis à jour.
        for info in informations_maj:
            if not info.read:  # Si l'information n'est pas marquée comme lue.
                if info.title not in dict_database["informations"]:
                    # Si l'information n'est pas présente dans la liste des informations deja connues.
                    nouvelles_infos.append(info)  # L'information est nouvelle.
                    dict_database["informations"].append(info.title)
                    nouvelles_infos.append(info)
                    if config["Pronote"]["MARQUER_COMME_LUE"]:
                        info.mark_as_read(True)
        if nouvelles_infos:  # Si la liste des nouvelles informations n'est pas vide.
            enregistre_donnees_fichier(dict_database)
            infos_contenu_mail = ""
            for info in nouvelles_infos:
                if info.survey:  # Si l'information est un sondage.
                    infos_contenu_mail += (f"{str(info.start_date)[:-9]} - {info.author}"
                                           f"- SONDAGE - {info.title} :\n\n{info.content}\n\n")
                else:
                    infos_contenu_mail += (f"{str(info.start_date)[:-9]} - {info.author}"
                                           f"- {info.title} :\n\n{info.content}\n\n")
            envoi_mail("Nouvelle information - Notification Pronote",
                       "Notification Pronote - Bot pronote-notif\n\n"
                       f"### Nouvelle information:\n{infos_contenu_mail}")


def envoi_mail(objet, contenu):
    """ Envoi un mail. """

    global mail_envoye

    try:
        msg = MIMEMultipart()
        msg['From'] = config["Email"]["MAIL_ENVOYEUR"]
        msg['To'] = config["Email"]["MAIL_DESTINATAIRE"]
        msg['Subject'] = objet
        msg.attach(MIMEText(contenu))
        mailserver = smtplib.SMTP(config["Email"]["MAIL_ADRESSE"], config["Email"]["MAIL_PORT"])
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.ehlo()
        mailserver.login(config["Email"]["MAIL_LOGIN"], config["Email"]["MAIL_MOT_DE_PASSE"])
        mailserver.sendmail(config["Email"]["MAIL_ENVOYEUR"],
                            config["Email"]["MAIL_DESTINATAIRE"], msg.as_string())
        mailserver.quit()
        logging.info(f"Mail envoyé: {objet}")
        mail_envoye = True
    except Exception as err:
        logging.critical(f"Une erreur est survenue lors de l'envoi d'un mail: {err}")
        raise SystemExit(f"Erreur: une erreur est survenue lors de l'envoi d'un mail: {err}")


def enregistre_donnees_fichier(donnees):
    """ Sauvegarde les données dans un fichier binaire
        sous forme de dictionnaire avec pickle.
    """

    with open(DB_FICHIER, "wb") as f:
        pickle.dump(donnees, f)
    logging.info(f"Dictionnaire enregistré dans le fichier {DB_FICHIER}")


if __name__ == '__main__':
    mail_envoye = False
    # Configuration de la journalisation.
    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO,
                        handlers=[logging.FileHandler(LOG_FICHIER), logging.StreamHandler()])
    # Chargement du fichier de configuration.
    logging.info("Lancement du script.")
    try:
        config = configparser.ConfigParser()
        config.read(CONF_FICHIER)
    except Exception as e:
        logging.critical(f"Impossible de charger le fichier de configuration {CONF_FICHIER}")
        raise SystemExit(f"Erreur: impossible de charger le fichier de configuration {CONF_FICHIER}")
    # Chargement du dictionnaire des données sauvegardées.
    if not os.path.isfile(DB_FICHIER):
        # Création du fichier de sauvegarde des données s'il n'existe pas.
        dict_database = {"notes": [], "informations": [], "cours_annules": []}
        logging.info("Création du nouveau dictionnaire.")
        enregistre_donnees_fichier(dict_database)
    else:
        # Chargement des données depuis le fichier.
        with open(DB_FICHIER, "rb") as file:
            dict_database = pickle.load(file)
        # Décommentez la ligne suivante pour afficher le dictionnaire chargé dans les logs.
        #logging.info(f"Dictionnaire chargé: {dict_database}")
    # Connexion à Pronote. Création de l'objet Client.
    try:
        client = pronotepy.Client(config["Pronote"]["PRONOTE_ADRESSE"],
                                  username=config["Pronote"]["PRONOTE_UTILISATEUR"],
                                  password=config["Pronote"]["PRONOTE_MOT_DE_PASSE"],
                                  ent=globals()[config["Pronote"]["DEFAUT_ENT"]])
    except Exception as e:
        logging.critical("Impossible de se connecter au compte Pronote. "
                         "Vérifiez le fichier de configuration.")
        raise SystemExit("Impossible de se connecter au compte Pronote. "
                         "Vérifiez le fichier de configuration.")

    # Commentez les fonctions ci-dessous pour les désactiver.
    notif_informations()
    notif_annulation_cours()
    notif_notes()

    if not mail_envoye:
        logging.info("Aucun mail envoyé.")
