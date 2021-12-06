from sqlalchemy.sql.sqltypes import Integer
from lib.extraction import (convert_entry_to_queries, get_pub_links,
                            save_pdf_from_links)
from lib.logs import create_logs, write_in_logs
import pandas as pd
from lib.text_mining import traitement_mining
import data_gestion.gestion.data_gestion as db
from tkinter import ttk
import os
import json
import threading
import tkinter as tk


class ArticleSearch():
    def __init__(self, max_age: int = 0, max_articles: int = 1000):
        # common elements
        self.article_age_var = max_age
        self.pubmed_limit = max_articles
        create_logs()


# ============================================================================
# INPUT PROCESSING
# ============================================================================

    def traitement_recherche(self, entry):
        """
        """
        def call_when_interrupt(reason: str, request_id: Integer = None ,  **kwargs):
            """
            Called when finish to reset the GUI window

            :param reason: Reason to why it is finished, can be 'success' or
                           'already done'
            """

            # too bad their is no switch
            if reason == 'success' or reason == 'no link':
                #TODO: do something when the result is available
                return request_id


            if reason == '0':
                #TODO: Ask this:
                #   'Information',
                #   'Recherche déjà effectuée mais abandonnée en cours de '
                #   'processus\n reprise à zéro !'
                pass

            elif reason == '1':
                #TODO: Ask this:
                #   Attention',
                #   'La recherche à déjà été effectuée le '
                #   f'{kwargs["timestamp"]} et les articles sont déjà '
                #   'téléchargés\n Voulez vous recommencer le '
                #   'téléchargement ?\n (Si non alors les articles '
                #   'téléchargés seront analysés)'
                pass

            elif reason == '2':
                #TODO: Ask this:
                #   'Attention',
                #   'La recherche à déjà été effectuée le '
                #   f'{kwargs["timestamp"]} et les articles ont déjà '
                #   'été traités\n Voulez vous recommencer le '
                #   'téléchargement ?\n (Si non alors le dernier '
                #   'rapport sera affiché)'
                pass

        links, path, queries = get_pub_links(entry, self.pubmed_limit,
                                             self.article_age_var,
                                             call_when_interrupt)
        if links == []:
            call_when_interrupt('no links')
            return

        if links not in ['1', '2'] and queries not in ['1', '2']:
            # references of the articles
            ref = save_pdf_from_links(links, path)
            df = pd.DataFrame(ref,
                              columns=['article', 'title', 'date', 'link'])
            # output directory does not exist: create it
            if not os.path.exists(path):
                os.makedirs(path)
            df.to_csv(f'{path}/{entry["base_word"]}_ref.csv')
            conn = db.create_connection('./data.db')
            # Pdfs downloaded, we save it for later
            db.update_request_stage(conn, json.dumps(queries), 1)

        if links != '2' and queries != '2':
            conn = db.create_connection("./data.db")
            categories = [
                categorie[2] for categorie in db.get_categories(conn)
            ]
            result = {key: {} for key in categories}
            df = pd.read_csv(f'{path}/{entry["base_word"]}_ref.csv')
            for file in os.listdir(path):
                if '.txt' in file:
                    data = traitement_mining(path + '/' + file)
                    if result == {}:
                        result = data
                    else:
                        write_in_logs('informations',
                                      'Fichier ' + file + ' traité')
                        for categorie in data.keys():
                            if data[categorie] != []:
                                result[categorie][file.split(".")
                                                  [0]] = data[categorie]

            # write all the results in the database
            queries = convert_entry_to_queries(entry)
            conn = db.create_connection("./data.db")
            request_id = db.get_request(conn, json.dumps(queries))[0][0]
            
            for categorie in result.keys():
                conn = db.create_connection("./data.db")
                category_id = db.get_category_id(conn,
                                                 category_name=categorie)[0][0]
                for article in result[categorie]:
                    ligne = df.loc[df['article'] == article]
                    title = ""
                    date = ""
                    link = ""
                    if not pd.isnull(ligne.iloc[0]['title']):
                        title = ligne.iloc[0]['title']
                    if not pd.isnull(ligne.iloc[0]['date']):
                        date = ligne.iloc[0]['date']
                    if not pd.isnull(ligne.iloc[0]['link']):
                        link = ligne.iloc[0]['link']

                    for sentence in result[categorie][article]:
                        conn = db.create_connection("./data.db")
                        result_id = db.add_result(
                            conn, sentence['sentence'], title, link,
                            sentence['value'], sentence['in_what'],
                            json.dumps(sentence['methods']),
                            json.dumps(sentence['subjects']))[0][0]
                        conn = db.create_connection("./data.db")
                        db.add_category_to_request(conn, request_id,
                                                   category_id, result_id)

            #finished
            conn = db.create_connection("./data.db")
            db.update_request_stage(conn, json.dumps(queries), 2)

        #afficher le rapport
        return call_when_interrupt('success' , request_id=request_id)

    def traitement_mots(self, bw, args):
        """
        """
        if bw == '':
            print('Aucun mot dans la recherche')
            return

        entry = {
            'base_word': bw.replace(' ', ''),
            'keywords': args.replace(' ', '').split('/'),
        }

        return self.traitement_recherche(entry)

    def get_base_from_queries(self, str_queries: str):
        """
        Get the base word of a query

        :param str_queries: Queries that come from the database
        """
        # Get the queries from string to a table format
        queries = json.loads(str_queries)
        query = queries[0]
        # we split space but also + for backwards compatibility
        return query.split(' ')[0].split('+')[0]
