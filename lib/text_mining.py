import tkinter as tk
from data_gestion.gestion.data_gestion import *
from tkinter import filedialog as fd
from .logs import write_in_logs
import nltk
import stanza


def check_update():
    stanza.download('en')
    nltk.download('punkt')


##


def creation_dict_keywords():
    """Used to get keywords for each category in the database

    Returns:
        dict keywords: Dictionnary associating categories with its keywords
    """
    keywords = {}
    conn = create_connection(
        "./data.db")  # récupération des données dans la base de donnée
    categories = [(categorie[1], categorie[2])
                  for categorie in get_categories(conn)]
    for category in categories:
        conn = create_connection("./data.db")
        keywords[category[1]] = [
            keyword[0].lower()
            for keyword in get_keywords_from_category(conn, category[0])
        ]
    return keywords


def get_word_variants(word: str):
    """
    Used to get all variants of a word (for exemple non corrosive --> ["non corrosive","non-corrosive"])

    :param word: Word to get variants
    :type word: str
    """
    word_l = word.lower()
    word_variants = [word_l]
    if "-" in word_l:
        s = word_l.split("-")
        new_word = ''
        for w in s:
            new_word += f'{w} '
        word_variants.append(new_word.strip())
    elif " " in word_l:
        s = word_l.split(" ")
        new_word = ''
        for w in s:
            new_word += f'{w}-'
        word_variants.append(new_word.strip('-'))

    return word_variants


def traitement_mining(filename):
    check_update()

    with open(filename, encoding="utf-8") as f:
        text = f.read()
        sents = nltk.sent_tokenize(text)
    usable_sents = []
    # sentence that are not part of summaries for exemple
    for sentence in sents:
        sentence = sentence.rstrip().lower()
        if len(sentence) < 1000:
            repetition = False
            nbr_repetition_max = 4
            i = 0
            while i < len(sentence) - nbr_repetition_max:
                if sentence[i] == sentence[i + 1] == sentence[
                        i + 2] == sentence[i + 3]:
                    repetition = True
                    break
                i += 1

            if not repetition:
                usable_sents.append(sentence.replace('\n', ' '))
    return extraction_phrases(usable_sents, creation_dict_keywords())


def extraction_phrases(usable_sents, keywords):
    conn = create_connection(
        "./data.db")  # récupération des données dans la base de donnée
    categories = keywords.keys()
    extracted_sents = {key: [] for key in categories}
    # On regarde pour chaque phrase si elle contient un keyword appartenant a une categorie
    for sentence in usable_sents:
        for categorie in categories:
            for keyword in keywords[categorie]:
                for variant in get_word_variants(keyword):  # team rambo
                    if variant in sentence:
                        extracted_sents[categorie].append(
                            {'sentence': sentence})
    return extraction_methods_and_subjects(extracted_sents)
    # return our_nlp(extracted_sents, keywords)


def extraction_methods_and_subjects(extracted_sents):
    conn = create_connection("./data.db")
    methods = [method[0] for method in get_methods(conn)]
    conn = create_connection("./data.db")
    subjects = [subject[0] for subject in get_subjects(conn)]
    conn = create_connection("./data.db")
    decision_words = get_decision_words(conn)
    in_what_words = [
        word for what_word in ["in vivo", "in vitro"]
        for word in get_word_variants(what_word)
    ]
    for categorie in extracted_sents.keys():
        conn = create_connection("./data.db")
        categorie_id = get_category_id(conn, category_nbr=categorie)
        for sentence in extracted_sents[categorie]:
            sentence['methods'] = []
            for method in methods:
                for variant in get_word_variants(method):
                    if variant in sentence['sentence']:
                        sentence['method'].append(variant)
            sentence['subjects'] = []
            for subject in subjects:
                for variant in get_word_variants(subject):
                    if variant in sentence['sentence']:
                        sentence[subjects].append(variant)
            sentence['in_what'] = ''
            for word in in_what_words:
                if word in sentence['sentence']:
                    sentence['in_what'] = word
            sentence['value'] = 0
            # Dès qu'on trouve un mot de décision on s'arrête
            # TODO: améliorer avec le nlp pour détecter des négations
            for decision_word in decision_words[categorie]:
                if decision_word[0] in sentence['sentence']:
                    sentence['value'] = decision_word[1]
                    break

    return extracted_sents


def our_nlp(extracted_sents, keywords):

    nlp = stanza.Pipeline('en', verbose=False)

    data = {key: [] for key in keywords.keys()}
    i = 1
    total = sum(
        [len(extracted_sents[categorie]) for categorie in extracted_sents])
    for categorie in extracted_sents.keys():
        for sentence in extracted_sents[categorie]:
            doc = nlp(sentence)
            #write_in_logs("informations",(str(i)+"/"+str(total)+" sentences done"),glob_stop)
            i += 1
            for sent in doc.sentences:
                relation = [
                ]  # [0: id, 1: text, 2: type, 3: relation, 4: type of relation]
                for token in sent.words:
                    relation.append([
                        token.id, token.text, token.upos, token.head,
                        token.deprel
                    ])
                usefull_sentence = extraction_information(
                    relation, categorie, keywords)
                if usefull_sentence != []:
                    data[categorie].append(sentence)
    return data


def extraction_information(relation, categorie, keywords):

    usefull_info = False
    selection_word = []
    id_neighbor_1 = []
    for elt in relation:  # ne jamais mettre elt !!!
        if elt[4] == 'root':
            root = elt
            break  # qu'un seul root dans la phrase
    for elt in relation:
        if elt[3] == root[0] and (elt[4] == 'obj' or elt[4] == 'nsubj'
                                  or elt[4] == 'aux' or elt[4] == 'parataxis'):
            id_neighbor_1.append(elt[0])
            selection_word.append(elt)

    for elt in relation:
        if elt != root and elt[3] in id_neighbor_1:
            selection_word.append(elt)

    for keyword in keywords[categorie]:
        if keyword in [word[1] for word in selection_word]:
            usefull_info = True

    sentence = []
    if usefull_info:
        sentence = [
            word[1] for word in sorted(selection_word, key=lambda M: M[0])
        ]
    return sentence
