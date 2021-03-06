import sqlite3
import json

# Database functions


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print(e)

    return conn


def add_category(conn, category_nbr: str, category_name: str, desc: str = ""):
    """
    Add a category to the database
    :param conn: Connection object
    :param category_nbr: Number of the category to add
    :param category_name: Name of the category to add
    :param desc: Description of the category to add
    :return:
    """
    sql = ''' INSERT INTO categories(number, name, description)
                VALUES(?,?,?) '''

    cur = conn.cursor()
    cur.execute(sql, (category_nbr, category_name, desc))
    conn.commit()
    conn.close()


def get_categories(conn):
    """
    Return all categories
    :param conn: Connection object
    :return:
    """
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM categories")
    except:
        return None
    else:
        rows = cur.fetchall()
        return rows


def get_category_id(conn, **kwargs):
    """
    Get category ID from category number or category name

    :param conn: Connection object
    :param kwargs: Must contain either category_nbr or category_name
    :return: None if bad arguments
    """
    cur = conn.cursor()
    id = None
    if "category_nbr" in kwargs.keys():
        sql = '''SELECT id FROM categories WHERE number=?'''
        cur.execute(sql, (kwargs['category_nbr'],))
        id = cur.fetchall()
    elif "category_name" in kwargs.keys():
        sql = '''SELECT id FROM categories WHERE name=?'''
        cur.execute(sql, (kwargs['category_name'],))
        id = cur.fetchall()
    conn.close()
    return id


def add_keyword(conn, category_nbr: str, keyword: str):
    """
    Add a keyword linked to a category in the database
    :param conn: Connection object
    :param keyword: Category number linked to the keyword
    :synonm: Keyword to add
    :return: True if the keyword is not already in the database for this category
    """
    cur = conn.cursor()
    # V??rification que le keyword n'est pas d??j?? dans la table
    cur.execute(
        "SELECT k.name FROM keywords as k JOIN categories as c on k.category_id=c.id WHERE c.number=?", (category_nbr,))
    rows = cur.fetchall()

    if keyword not in [k_name[0] for k_name in rows]:
        cur.execute("SELECT id FROM categories WHERE number=?",
                    (category_nbr,))
        rows = cur.fetchall()

        sql = ''' INSERT INTO keywords(category_id,name)
                    VALUES(?,?) '''

        cur.execute(sql, (rows[0][0], keyword))
        conn.commit()
        conn.close()
        return True
    return False


def del_keyword(conn, category_nbr: str, keyword: str):
    """
    Supprime un keyword dans la base de donn??e
    :param conn: Connection object
    :param category_nbr: Category number linked to the keyword
    :param keyword: Keyword to delete
    :return: False if keyword not in database
    """
    cur = conn.cursor()
    # V??rification que le keyword est dans la table
    cur.execute("SELECT c.id FROM keywords as k JOIN categories as c on k.category_id=c.id WHERE c.number=? and k.name=?", (category_nbr, keyword))
    rows = cur.fetchall()
    if rows != []:
        c_id = rows[0][0]
        cur.execute(
            "DELETE FROM keywords WHERE category_id=? and name=?", (c_id, keyword))
        conn.commit()
        conn.close()


def add_request(conn, query: str, article_limit: int, age_limit: int):
    """
    Add a request to the database

    :param conn: Connection object
    :param query: Name of the molecule searched
    :param article_limit: Choosen limit article
    :param age_limit: Choosen article age limit for the search
    """

    cur = conn.cursor()
    sql = ''' INSERT INTO requests(query,article_limit,age_limit)
                VALUES(?,?,?) '''

    cur.execute(sql, (query, article_limit, age_limit))
    conn.commit()
    conn.close()


def get_requests(conn):
    """
    Get all requests already made

    :param conn: Connection object
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM requests")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_request(conn, queries: str):
    """
    Get a request if it exist in the database

    :param conn: Connection object
    :param queries: Request to search
    """

    cur = conn.cursor()
    cur.execute("SELECT * FROM requests WHERE query=?", (queries,))
    rows = cur.fetchall()
    conn.close()
    return rows


def update_request(conn, queries: str, article_limit: int, age_limit: int):
    """
    Used to update a request (time is auto updated)

    :param conn: Connection object
    :param queries: The request to update
    :param article_limit: The new article limit
    :param age_limit: The new age limit
    """
    cur = conn.cursor()
    sql = '''UPDATE requests SET created_at = datetime(CURRENT_TIMESTAMP, 'localtime'), article_limit=? , age_limit=? WHERE query = ?'''
    cur.execute(sql, (article_limit, age_limit, queries))
    conn.commit()
    conn.close()


def update_request_stage(conn, queries: str, etape: int):
    """
    Used to update the current state of the request

    :param conn: Connection object
    :param queries: Query to search
    :param etape: Stage of the research
    """
    cur = conn.cursor()
    sql = '''UPDATE requests SET etape=? WHERE query=?'''
    cur.execute(sql, (etape, queries))
    conn.commit()
    conn.close()


def get_keywords_from_category(conn, category_nbr: str):
    """
    Get keywords associated to a category in the database
    :param conn: Connection object
    :param category_nbr: Category number linked the keywords
    :return: Return keywords list
    """
    cur = conn.cursor()
    cur.execute("SELECT id FROM categories WHERE number=?", (category_nbr,))
    rows = cur.fetchall()
    sql = "SELECT name FROM keywords WHERE category_id=?"

    try:
        cur.execute(sql, (rows[0][0],))
    except Exception as e:
        conn.close()
        return None
    else:
        success = True
        results = cur.fetchall()
        conn.close()
        return results


def add_result(conn, request_id: int, category_id: int,sentence: str, article_name: str, article_link: str, value: int, in_what: str, method: str, subject: str):
    cur = conn.cursor()
    cat_to_req = cur.execute("SELECT id FROM category_to_request WHERE id_category=? and id_request=?",(category_id,request_id)).fetchall()[0][0]
    sql = ''' INSERT INTO results(cat_to_req_id,sentence,article_name,article_link,value,in_what,method,subject)
              VALUES(?,?,?,?,?,?,?,?) '''
    cur.execute(sql, (cat_to_req,sentence, article_name, article_link,
                value, in_what, method, subject))
    conn.commit()
    sql = ''' SELECT id FROM results WHERE sentence=? and article_name=? and article_link=? and value=? and in_what=? and method=? and subject=?'''
    cur.execute(sql, ((sentence, article_name, article_link,
                value, in_what, method, subject)))
    id = cur.fetchall()
    conn.close()
    return id


def get_results(conn, bw: str, args: str):

    entry = {
        'base_word': bw.replace(' ', ''),
        'keywords': args.replace(' ', '').split('/'),
    }

    # build list of queries for each keyword given
    if len(entry['keywords']) != 0:
        query = [f'{entry["base_word"]} {keyword}' for keyword in entry['keywords']
                 ]
    else:
        # no keywords: result is a list with only the base word
        query = [entry['base_word']]

    cur = conn.cursor()

    categories_info = [cat for cat in cur.execute(
        "SELECT * FROM categories").fetchall()]

    to_return = {(key[1], key[2]): [] for key in categories_info}

    sql = '''SELECT r.* FROM results as r 
             JOIN category_to_request as c_t ON r.id=c_t.id_result 
             JOIN requests as req ON req.id=c_t.id_request
             WHERE req.query=? and c_t.id_category=?'''

    for categorie in categories_info:
        cur.execute(sql, (json.dumps(query), categorie[0]))
        for result in cur.fetchall():
            to_return[(categorie[1], categorie[2])].append(result)

    return to_return


# def get_methods(conn):
#     cur = conn.cursor()
#     cur.execute("SELECT method_name FROM methods")
#     rows = cur.fetchall()
#     conn.close()
#     return rows


def add_subject(conn, subject: str):
    """Add a subject to the database

    :param conn: Connection object
    :param subject: Subject name
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT subject_name FROM subjects WHERE subject_name=?", (subject,))
    rows = cur.fetchall()
    if subject not in [result[0] for result in rows]:
        cur.execute("INSERT INTO subjects(subject_name) values (?)", (subject,))
        conn.commit()
        conn.close()


def get_subjects(conn):
    cur = conn.cursor()
    cur.execute("SELECT subject_name FROM subjects")
    rows = cur.fetchall()
    conn.close()
    return rows


def add_category_to_request(conn, request_id: int):
    cur = conn.cursor()
    categories = [categorie for categorie in cur.execute("SELECT * FROM categories").fetchall()]
    sql = '''INSERT INTO category_to_request(id_request,id_category)
             values (?,?)'''
    for categorie in categories:
        cur.execute(sql, (request_id, categorie[0]))
    conn.commit()
    conn.close()


def add_decision_word(conn, category_id: int, decision_word: str, value: int):
    """
    Add a decision word link to a category in the database

    :param conn: Connection object
    :param category_id: Id of the linked category
    :param decision_word: Decision word to add to the database
    :param value: Value of the decision word (between 0 and 10, 10 being the most positive)
    """
    cur = conn.cursor()
    sql = '''INSERT INTO decision_words(id_category,decision_word,value)
             values (?,?,?)'''
    cur.execute(sql, (category_id, decision_word, value))
    conn.commit()
    conn.close()


def get_decision_words(conn):
    """
    Return the decision words in a dictionnary {category : [decision words]}

    :param conn: Connection object
    """
    cur = conn.cursor()
    sql = '''SELECT c.name,decision_word,value
             FROM decision_words as d JOIN categories as c where d.id_category=c.id'''
    cur.execute(sql)
    rows = cur.fetchall()

    categories_name = [categorie[2] for categorie in get_categories(conn)]
    result = {key: [] for key in categories_name}
    for word in rows:
        result[word[0]].append((word[1], word[2]))

    return result


def add_method(conn, category_nbr: str, method: str):
    """
    Add a method linked to a category in the database

    :param conn: Connection object
    :param method: Category number linked to the method
    :synonm: method to add
    :return: True if the method is not already in the database for this category
    """
    cur = conn.cursor()
    # V??rification que la m??thode n'est pas d??j?? dans la table
    cur.execute(
        "SELECT m.name FROM methods as m JOIN categories as c on m.category_id=c.id WHERE c.number=?", (category_nbr,))
    rows = cur.fetchall()

    if method not in [m_name[0] for m_name in rows]:
        cur.execute("SELECT id FROM categories WHERE number=?",
                    (category_nbr,))
        rows = cur.fetchall()

        sql = ''' INSERT INTO methods(category_id,name)
                    VALUES(?,?) '''

        cur.execute(sql, (rows[0][0], method))
        conn.commit()
        conn.close()
        return True
    return False


def get_methods(conn):
    """
    Return the methods in a dictionnary {category : [methods]}

    :param conn: Connection object
    """
    cur = conn.cursor()
    sql = '''SELECT c.name,m.name
             FROM methods as m JOIN categories as c where m.category_id=c.id'''
    cur.execute(sql)
    rows = cur.fetchall()

    categories_name = [categorie[2] for categorie in get_categories(conn)]
    result = {key: [] for key in categories_name}
    for word in rows:
        result[word[0]].append(word[1])

    return result
