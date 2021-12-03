from lib.extraction import (convert_entry_to_queries,
                            get_pub_links,
                            save_pdf_from_links)
from lib.logs import create_logs, create_logs_window, write_in_logs
import pandas as pd
from lib.text_mining import traitement_mining
import data_gestion.gestion.data_gestion as db
from tkinter import ttk
import os
import json
import threading
import tkinter as tk


class ArticleSearch():

    def __init__(self , article_age_var : int = 0 , pubmed_limt : int = 1000):

        self.glob_stop = False

        # common elements
        self.article_age_var = article_age_var #durée de la recherche [1-5-10-0]
        self.progress_indicators = {} #s'allume
        self.pubmed_limit = pubmed_limt #limite d'articlee

# ============================================================================
# INPUT PROCESSING
# ============================================================================

    def traitement_mots(self, bw, args):
        """
        """
        if bw == '':
            print('Aucun mot dans la recherche')
            return

        # checkbuttons['autre'][1]['state'] = 'disabled'

        entry = {
            'base_word': bw.replace(' ', ''),
            'keywords': args.replace(' ', '').split('/'),
        }

        # x = threading.Thread(target=self.traitement_recherche,
        #                      args=[entry],
        #                      daemon=True)

        # x.start()
        return self.traitement_recherche(entry)

    def traitement_recherche(self, entry):
        """
        """
        if self.glob_stop:
            return

        def call_when_interrupt(reason: str, **kwargs):
            """
            Called when finish to reset the GUI window

            :param reason: Reason to why it is finished, can be 'success' or
                           'already done'
            """

            # too bad their is no switch
            if reason == 'success' or reason == 'no link':
                tk.messagebox.showinfo(
                    'Information',
                    ('Succès !' if reason == 'success' else
                        'Aucun articles trouvés!')
                )
                self.val_button['state'] = 'enabled'
                self.checkbuttons['pubmed'][1]['state'] = 'enabled'
                # checkbuttons['autre'][1]['state'] = 'enabled'

                self.progress_indicators['ind_mot_cles'].deselect()
                self.progress_indicators['ind_recherche_pubmed'].deselect()
                self.progress_indicators['ind_recup_liens'][0].deselect()
                self.progress_indicators['ind_pdf_download'][0].deselect()
                self.progress_indicators['progress_bar']['value'] = 0
                self.progress_indicators['ind_recup_liens'][1].set(
                    'Articles uniques trouvés : ')
                self.progress_indicators['ind_pdf_download'][1].set(
                    'Nombre d\'articles téléchargés :')

            if reason == '0':
                tk.messagebox.showinfo(
                    'Information',
                    'Recherche déjà effectuée mais abandonnée en cours de '
                    'processus\n reprise à zéro !'
                )

            elif reason == '1':
                msgbox = tk.messagebox.askyesno(
                    title='Attention',
                    message='La recherche à déjà été effectuée le '
                            f'{kwargs["timestamp"]} et les articles sont déjà '
                            'téléchargés\n Voulez vous recommencer le '
                            'téléchargement ?\n (Si non alors les articles '
                            'téléchargés seront analysés)'
                )
                return msgbox

            elif reason == '2':
                msgbox = tk.messagebox.askyesno(
                    title='Attention',
                    message='La recherche à déjà été effectuée le '
                            f'{kwargs["timestamp"]} et les articles ont déjà '
                            'été traités\n Voulez vous recommencer le '
                            'téléchargement ?\n (Si non alors le dernier '
                            'rapport sera affiché)'
                )
                return msgbox

        links, path, queries = get_pub_links(entry,
                                             self.progress_indicators,
                                             self.pubmed_limit,
                                             self.article_age_var,
                                             call_when_interrupt,
                                             self.glob_stop)
        if links == []:
            # call_when_interrupt('no links')
            return 0

        if links not in ['1', '2'] and queries not in ['1', '2']:
            # references of the articles
            ref = save_pdf_from_links(
                links, self.progress_indicators, path, self.glob_stop)
            df = pd.DataFrame(ref, columns=['article','title', 'date', 'link'])
            # output directory does not exist: create it
            if not os.path.exists(path):
                os.makedirs(path)
            df.to_csv(f'{path}/{entry["base_word"]}_ref.csv')
            conn = db.create_connection('./data.db')
            # Pdfs downloaded, we save it for later
            db.update_request_stage(conn, json.dumps(queries), 1)

        if links != '2' and queries != '2':
            conn=db.create_connection("./data.db")
            categories=[categorie[2] for categorie in db.get_categories(conn)]
            result = {key: {} for key in categories}
            df = pd.read_csv(f'{path}/{entry["base_word"]}_ref.csv')
            for file in os.listdir(path):
                if self.glob_stop:
                    return
                if '.txt' in file:
                    data = traitement_mining(path+'/'+file, self.glob_stop)
                    if result == {}:
                        result = data
                    else:
                        write_in_logs('informations', 'Fichier ' +
                                      file+' traité', self.glob_stop)
                        for categorie in data.keys():
                            if data[categorie]!=[]:
                                result[categorie][file.split(".")[0]]=data[categorie]
            
            # write all the results in the database
            queries = convert_entry_to_queries(entry)
            conn = db.create_connection("./data.db")
            request_id = db.get_request(conn,json.dumps(queries))[0][0]
            for categorie in result.keys():
                conn = db.create_connection("./data.db")
                category_id = db.get_category_id(conn,category_name=categorie)[0][0]
                for article in result[categorie]:
                    ligne=df.loc[df['article'] == article]
                    title=""
                    date=""
                    link=""
                    if not pd.isnull(ligne.iloc[0]['title']):
                        title=ligne.iloc[0]['title']
                    if not pd.isnull(ligne.iloc[0]['date']):
                        date=ligne.iloc[0]['date']
                    if not pd.isnull(ligne.iloc[0]['link']):
                        link=ligne.iloc[0]['link']
                    for sentence in result[categorie][article]:
                        conn = db.create_connection("./data.db")
                        result_id=db.add_result(conn,sentence['sentence'],title,link,sentence['value'],sentence['in_what'],json.dumps(sentence['methods']),json.dumps(sentence['subjects']))[0][0]
                        conn = db.create_connection("./data.db")
                        db.add_category_to_request(conn,request_id,category_id,result_id)
                

            #finished
            conn = db.create_connection("./data.db")
            db.update_request_stage(conn, json.dumps(queries), 2)
           
        #afficher le rapport
        #call_when_interrupt('success')
        return 1

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
