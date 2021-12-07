from bs4 import BeautifulSoup
from lib.logs import write_in_logs
from pdfminer.high_level import extract_text
import data_gestion.gestion.data_gestion as db
import math
import json
import os
import requests
import time

# Variable globale
HEADER = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/50.0.2661.102 Safari/537.36'}


def convert_entry_to_queries(entry: dict) -> list:
    """
    Convert a search entry to a list of http url queries

    :param entry: search entry base word and keywords

    :returns: list of http url queries
    """
    # build list of queries for each keyword given
    if len(entry['keywords']) != 0:
        return [
            f'{entry["base_word"]} {keyword}' for keyword in entry['keywords']
        ]

    # no keywords: result is a list with only the base word
    return [entry['base_word']]


def get_element_text(soup: BeautifulSoup, tag: str, class_: str):
    """
    Given a bs4 soup, get element text without unnecessary whitespace.

    :param soup: bs4 soup
    :param tag: hmtl tag of element
    :param class: css class of element

    :returns: element text or empty string
    """
    element_soup = soup.find(tag, class_=class_)
    if element_soup is not None:
        return element_soup.text.replace('\n', '').strip(' ')
    return ''


def get_pub_links(entry: dict,
                  max_articles: int,
                  max_age: int,
                  call_when_interrupt) -> tuple:
    """
    Get url of PubMed articles based on a keyword search

    :param entry: baseword and keywords to look for in a document
    :param max_articles: maximum number of articles to extract
    :param max_age: maximum age for articles
    :param call_when_interrupt: Function to call when we want to interact with
                                the user

    :returns: list of the article urls, output diretory path and queries
    """
    # build list of queries
    queries = convert_entry_to_queries(entry)

    # output path
    path = f'./pdf/PubMed/{queries}'

    # Check if the request already exist
    conn = db.create_connection("./data.db")
    db_queries = db.get_request(conn, json.dumps(queries))
    if db_queries != []:
        etape = db_queries[0][5]
        if etape == 0:
            call_when_interrupt("0")
            conn = db.create_connection("./data.db")
            db.update_request(conn, json.dumps(queries), max_articles, max_age)
        # already downloaded pdfs
        elif etape == 1:
            # we want to resume the previous request
            if call_when_interrupt("1", timestamp=db_queries[0][2]) is False:
                return ("1", path, "1")
            conn = db.create_connection("./data.db")
            db.update_request(conn, json.dumps(queries), max_articles, max_age)
            conn = db.create_connection("./data.db")
            db.update_request_stage(conn, json.dumps(queries), 0)
        # CPSR already done
        elif etape == 2:
            # already finished so we want to cancel
            if call_when_interrupt("2", timestamp=db_queries[0][2]) is False:
                return("2", path, "2")
            conn = db.create_connection("./data.db")
            db.update_request(conn, json.dumps(queries), max_articles, max_age)
            conn = db.create_connection("./data.db")
            db.update_request_stage(conn, json.dumps(queries), 0)

    else:
        conn = db.create_connection("./data.db")
        db.add_request(conn,
                       json.dumps(queries),
                       max_articles,
                       max_age)

    # we start from beggining so we delete old pdf
    # output directory does not exist: create it
    if not os.path.exists(path):
        os.makedirs(path)
    for file in os.listdir(path):
        os.remove(f'{path}/{file}')

    # feedback for the user of the search progress
    write_in_logs('informations',
                  'Recherches à effectuer sur PubMed : ' + str(queries))
    write_in_logs('informations', 'Mot clés enregistrés')

    links = []
    page_counter = 0
    for query in queries:
        # search, request and parse result
        url = 'https://pubmed.ncbi.nlm.nih.gov/'
        params = {
            'term': query,
            'filter': ['simsearch2.ffrft', 'simsearch3.fft'],
            'size': 200,
        }
        if max_age != 0:
            params['filter'].append(f'datesearch.y_{max_age}')
        page = requests.get(url, headers=HEADER, params=params)
        soup = BeautifulSoup(page.content, 'html.parser')

        # get results number
        nbr_of_results = 0
        results_soup = (soup.find('div', class_='results-amount')
                            .find('span', class_='value'))
        if results_soup is not None:
            nbr_of_results = int(results_soup.text.replace(',', ''))
        nbr_of_pages = math.ceil(
            min(nbr_of_results, max_articles) / 200
        )

        write_in_logs('informations',
                      'Recherche effectuée sur PubMed avec une limite de '
                      f'{max_articles} articles et un âge maximal de '
                      f'{max_age if max_age!=0 else "--" } ans')

        for i in range(1, nbr_of_pages+1):
            page_counter += 1

            # request and parse search page
            try:
                url = 'https://pubmed.ncbi.nlm.nih.gov/'
                page = requests.get(url, headers=HEADER, params={
                    **params,
                    'page': i,
                })
                soup = BeautifulSoup(page.content, 'html.parser')
            # any error occurred: warn user
            except Exception:
                write_in_logs('erreurs',
                              'Chargement d\'une page impossible')
            # get the urls of the pages and add them to the result
            pages_awaiting = soup.select('a.docsum-title')
            for page in pages_awaiting:
                links.append(
                    'https://pubmed.ncbi.nlm.nih.gov' + page['href']
                )

    links = list(dict.fromkeys(links))

    # got more links than allowed: ignore extra links
    if len(links) > max_articles:
        links = links[:max_articles]

    # Nombre de liens obtenus
    write_in_logs('informations',
                  'Nombre de liens uniques obtenus : ' + str(len(links)))

    # return result
    return links, path, queries


def save_pdf_from_links(links: list,
                        path: str) -> list:
    """
    Download and save the pdf files of articles from their urls

    :param links: list of urls for each article file
    :param path: directory of output

    :returns: list of informations about each article
    """
    result_reference = []
    index = 0
    download_counter = 0
    for link in links:

        # request and parse pdf url
        page = requests.get(link, headers=HEADER)
        soup = BeautifulSoup(page.content, 'html.parser')

        title = get_element_text(soup, 'h1', 'heading-title')

        # try to find the publication link in the page
        full_publication_link = None
        if soup.find('a', class_='link-item pmc') is not None:
            full_publication_link = soup.find(
                'a', class_='link-item pmc')['href']
        elif soup.find('a', class_='link-item pmc dialog-focus') is not None:
            full_publication_link = soup.find(
                'a', class_='link-item pmc dialog-focus')['href']

        # publication link found: try to get document page
        if full_publication_link is not None:
            r = request_pdf(full_publication_link)

            # could not get document page: warn user
            if not r[0]:
                write_in_logs('erreurs',
                              '-->Connection refusée à {}'.format(
                                  full_publication_link
                              ))

            # got document page: parse and download pdf(s)
            else:
                page = r[1]
                soup = BeautifulSoup(page.content, 'html.parser')
                date = get_element_text(soup, 'span', 'fm-vol-iss-date')
                pdf_prelinks = [
                    a.get('href')
                    for a in soup.select('li a')
                    if ('.pdf' in a.get('href'))
                ]
                pdf_links = []
                for prelink in pdf_prelinks:
                    if prelink[0] == '/':
                        pdf_links.append(
                            'https://www.ncbi.nlm.nih.gov'+prelink)
                    else:
                        pass
                        # testing
                        # pdf_links.append(prelink)
                for pdf in pdf_links:
                    worked = download_pdf(pdf, index, path)
                    if worked:
                        result_reference.append(
                            (f'article{index}', title, date, link))
                        index += 1

        download_counter += 1

    return result_reference


def request_pdf(link: str, tries: int = 3) -> tuple:
    """
    Make a request for an article pdf

    :param link: url of the article pdf

    :returns: result of request and page returned
    """
    tries -= 1

    # request page
    try:
        page = requests.get(link, headers=HEADER)

        # request successful: log success and return result
        write_in_logs('erreurs', '->Success !')
        return True, page

    # request failed: warn user and try again later
    except Exception:
        write_in_logs('erreurs',
                      '>Connection refusée à {}, retrying ...'.format(link))

        # not exceeded number of tries: wait before trying again
        if tries > 0:
            time.sleep(9 - 2*tries)
            return request_pdf(link, tries)

    # failure as fallback
    return False, ''


def download_pdf(link: str,
                 index: int,
                 path: str) -> bool:
    """
    Make the download of an article pdf

    :param link: url of the article pdf
    :param index: index of the article
    :param path: directory of output

    :returns: result of the download (successful or not)
    """
    try:
        response = requests.get(link, headers=HEADER)

    # unsuccessful request: warn user and abort
    except Exception:
        write_in_logs('erreurs',
                      'Impossible d\'accéder au pdf : ' + link)
        return False

    # successful request: save file
    if response.status_code == 200:

        # save pdf file
        file_path = f'{path}/article{index}.pdf'
        pdf = open(file_path, 'wb')
        pdf.write(response.content)
        pdf.close()

        # verify that the file is not corrupted
        try:
            text = extract_text(file_path)

        # corrupted file: remove it and warn user
        except Exception:
            os.remove(file_path)
            write_in_logs('erreurs',
                          f'Pdf {index} corrompu, il a été supprimé')
            return False

        # save text contents fo the file
        text_file = open(file_path.replace('.pdf', '.txt'),
                         'w',
                         encoding='utf-8')
        text_file.write(text)
        text_file.close()
        return True

    return False
