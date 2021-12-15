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
import nltk
import stanza


class ArticleSearch():
    def __init__(self, max_age: int = 0, max_articles: int = 1000):
        # common elements
        self.max_age = max_age
        self.max_articles = max_articles
        create_logs()
        self.check_update

    def check_update():
        stanza.download('en')
        nltk.download('punkt')


# ============================================================================
# INPUT PROCESSING
# ============================================================================

    def traitement_recherche(self, entry, etape_: int, force: bool):

        queries = convert_entry_to_queries(entry)

        if not force:
            # Check if the request already exist
            conn = db.create_connection("./data.db")
            db_queries = db.get_request(conn, json.dumps(queries))
            if db_queries != []:
                etape = db_queries[0][5]
                if etape == 0:
                    conn = db.create_connection("./data.db")
                    db.update_request(conn, json.dumps(queries),
                                      self.max_articles, self.max_age)
                # already downloaded pdfs
                elif etape == 1:
                    return (1, db_queries[0][2], db_queries[0][0]
                            )  #return etape and timestamp and request_id

                # CPSR already done
                elif etape == 2:
                    # already finished so we want to cancel
                    return (2, db_queries[0][2], db_queries[0][0]
                            )  #return etape and timestamp and request_id

            else:
                conn = db.create_connection("./data.db")
                db.add_request(conn, json.dumps(queries), self.max_articles,
                               self.max_age)

        if etape_ == 0:
            # output path
            path = f'./pdf/PubMed/{queries}'
            links, queries = get_pub_links(entry, self.max_articles,
                                           self.max_age)
            if links == []:
                return

            if force:
                conn = db.create_connection("./data.db")
                db.update_request(conn, json.dumps(queries), self.max_articles,
                                  self.max_age)
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
            etape_ = 1

        if etape_ == 1:
            # output path
            path = f'./pdf/PubMed/{queries}'

            if force:
                conn = db.create_connection("./data.db")
                db.update_request(conn, json.dumps(queries), self.max_articles,
                                  self.max_age)

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
            conn = db.create_connection("./data.db")
            db.add_category_to_request(conn, request_id)
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
                        db.add_result(conn, request_id, category_id,
                                      sentence['sentence'], title, link,
                                      sentence['value'], sentence['in_what'],
                                      json.dumps(sentence['methods']),
                                      json.dumps(sentence['subjects']))[0][0]

            # finished
            conn = db.create_connection("./data.db")
            db.update_request_stage(conn, json.dumps(queries), 2)

        # afficher le rapport
        conn = db.create_connection("./data.db")
        return 10, "10", db.get_request(conn, json.dumps(queries))[0][0]

    def traitement_mots(self, bw, args, etape_, force):
        """
        """
        if bw == '':
            print('Aucun mot dans la recherche')
            return

        entry = {
            'base_word': bw.replace(' ', ''),
            'keywords': args.replace(' ', '').split('/'),
        }

        return self.traitement_recherche(entry, etape_, force)

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