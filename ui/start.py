from ui.article_search import ArticleSearch
import data_gestion.create_database as db_create
import os.path

class Start():
    def __init__(self, max_age: int=0, max_articles: int=1000) -> None:

        if not os.path.isfile("./data.db"):
            db_create.main()    
    
        self.search = ArticleSearch(max_age,max_articles)
    
    def traitement(self, bw: str, args: str) -> bool:
        """Given a base word (for example "benzyl") and arguments (for example "alcohol / acetic)
         it will search for it on PubMed (for example "benzyl alcohol" and "benzyl acetic"))

        :param bw: A base word for the search
        :param args: Zero or multiples arguments separated by a /
        :return: Return True when finished
        """
        return self.search.traitement_mots(bw,args)
    