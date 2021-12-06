import tkinter as tk
from tkinter import ttk
import os
from gestion.data_gestion import *


def sortir():
    global root
    global glob_stop
    glob_stop=True
    root.destroy()
##
def get_catnbr_from_catname(catname : str):
    """
    Get the category number from its full name (nbr -- name)

    :param catname: Full Name of the category
    """
    category_number=""
    i=0
    while (catname[i]!='-' and catname[i+1]!='-'):
        category_number+=catname[i]
        i+=1
    category_number.strip()
    return category_number
##

def nettoyage_affichage_central():
    """
    Libère l'affichage central
    """
    global root_frame
    #There should only be a frame :
    for w in root_frame.winfo_children():
        w.destroy()

def creation_affichage_central(root):
    global root_frame
    root_frame=tk.Frame(root)
    widget_frame=tk.Frame(root_frame)

    def set_label_wrap(event):
        wraplength = event.width-1 # 12, to account for padding and borderwidth
        event.widget.configure(wraplength=wraplength)




    label = tk.Label(widget_frame,text="Veuillez selectionner une action à effectuer dans le menu en haut de la fenêtre",font=("Arial", 20))
    label.bind("<Configure>", set_label_wrap)

    label.pack(fill="both",expand=True)
    widget_frame.pack(fill="both",expand=True)
    root_frame.pack(fill="both",expand=True)

def creation_menu_barre(root):
    menubar=tk.Menu(root)

    creation_menu_database(menubar)

    root.config(menu=menubar)

def creation_menu_database(menubar):
    database_menu = tk.Menu(menubar,tearoff=0)

    database_menu.add_command(label="Affichage keywords", command=load_show_keyword)
    database_menu.add_command(label="Ajout keyword", command=load_add_keyword)
    database_menu.add_command(label="Supression keyword", command=load_del_keyword)
    database_menu.add_command(label="Modification keyword", command=load_mod_keyword)

    menubar.add_cascade(label="Base de donnée", menu=database_menu)

def load_show_keyword():
    global root_frame
    nettoyage_affichage_central()
    widget_frame=tk.Frame(root_frame)
    recherche_frame=tk.Frame(widget_frame)
    resultats_frame=tk.Frame(widget_frame)

    label=tk.Label(recherche_frame,text="Catégorie dont vous souhaitez afficher les keywords :",font=("Arial",13))

    conn = create_connection("../data.db")
    categories__=get_categories(conn)
    categories={}
    if categories__ is not None:
        for categorie in categories__:
            categories[categorie[1]]=categorie[2]

    choix= tk.StringVar()
    combobox=ttk.Combobox(recherche_frame,textvariable=choix,state="readonly",width=30)
    combobox['values']=[number+" -- "+value for number,value in categories.items()]

    result_var=tk.StringVar()
    button = ttk.Button(recherche_frame,text="Afficher les keywords",command=lambda : afficher_keywords(choix.get(),result_var))

    result_label=tk.Label(resultats_frame,textvariable=result_var)

    label.pack(pady=5)
    combobox.pack(pady=3)
    button.pack()

    result_label.pack(pady=5)


    recherche_frame.pack()
    resultats_frame.pack()
    widget_frame.pack()

def afficher_keywords(category : str,result_var : tk.StringVar):
    """
    Affiche les keywords associés à la catégorie recherchée

    :param category: La catégorie associée à la recherche
    """
    db_file="../data.db"
    conn = create_connection(db_file)

    category_number=get_catnbr_from_catname(category)
    
    result = get_keywords_from_category(conn,category_number)

    if result==None:
        result_var.set("Catégorie inexistante")
    else:
        text="Les keywords sont : \n\n"
        for resultat in result:
            text+=resultat[0]+" / "
        text = text[:-2]
        result_var.set(text)

def load_add_keyword():
    global root_frame
    nettoyage_affichage_central()
    widget_frame = tk.Frame(root_frame)
    entry_frame = tk.Frame(widget_frame)
    result_frame = tk.Frame(widget_frame)

    label1=tk.Label(entry_frame,text="Catégorie dans laquelle vous souhaitez ajouter le keyword :",font=("Arial",13))

    conn = create_connection("../data.db")
    categories__=get_categories(conn)
    categories={}
    if categories__ is not None:
        for categorie in categories__:
            categories[categorie[1]]=categorie[2]

    choix= tk.StringVar()
    combobox=ttk.Combobox(entry_frame,textvariable=choix,width=30,state="readonly")
    combobox['values']=[number+" -- "+value for number,value in categories.items()]

    label2=tk.Label(entry_frame,text="Keyword à ajouter :",font=("Arial",13))
    keyword=tk.StringVar()
    entry = ttk.Entry(entry_frame,exportselection=0, textvariable = keyword,width=30)

    result_var = tk.StringVar()
    button = ttk.Button(entry_frame,text="Ajouter le keywords",command=lambda : ajouter_keyword(choix.get(),keyword.get().strip(),result_var))

    label3= tk.Label(result_frame,textvariable=result_var)


    label1.pack(pady=5)
    combobox.pack(pady=3)
    label2.pack(pady=(20,5))
    entry.pack(pady=3)
    button.pack(pady=5)

    label3.pack(pady=10)

    entry_frame.pack()
    result_frame.pack()
    widget_frame.pack()

def ajouter_keyword(category, keyword, result_var):
    if category=='':
        result_var.set("Veuillez choisir une catégorie")
    elif keyword=='':
        result_var.set("Veuillez entrer un keyword à ajouter")
    else:
        conn = create_connection("../data.db")
        category_nbr=get_catnbr_from_catname(category)
        done=add_keyword(conn,category_nbr,keyword)
        if done:
            result_var.set("Le keyword : "+keyword+" a été ajouté !")
        else:
            result_var.set("Ce keyword existe déjà dans cette catégorie !")

def load_del_keyword():
    global root_frame
    nettoyage_affichage_central()
    widget_frame = tk.Frame(root_frame)
    entry_frame = tk.Frame(widget_frame)
    keyword_frame = tk.Frame(entry_frame)

    label1=tk.Label(entry_frame,text="Catégorie dans laquelle vous souhaitez supprimer un keyword :",font=("Arial",13))

    conn = create_connection("../data.db")
    categories__=get_categories(conn)
    categories={}
    if categories__ is not None:
        for categorie in categories__:
            categories[categorie[1]]=categorie[2]

    choix= tk.StringVar()
    combobox=ttk.Combobox(entry_frame,textvariable=choix,state="readonly",width=30)
    combobox['values']=[number+" -- "+value for number,value in categories.items()]

    choosen_keyword=tk.StringVar()

    def keyword_choice(*args):
        for w in keyword_frame.winfo_children():
            w.destroy()
        db_file="../data.db"
        conn = create_connection(db_file)
        result = get_keywords_from_category(conn,get_catnbr_from_catname(choix.get()))
        keywords=[]
        if result is not None:
            for keyword in result:
                keywords.append(keyword[0])
        combobox=ttk.Combobox(keyword_frame,textvariable=choosen_keyword,width=30,values=keywords,state="readonly")
        tk.Label(keyword_frame,text="Keyword à supprimer :",font=("Arial",13)).pack(pady=(20,10))
        combobox.pack()

        ttk.Button(keyword_frame,text="Supprimer le keyword",command=lambda : supprimer_keyword(choix.get(),choosen_keyword.get())).pack(pady=10)

    combobox.bind("<<ComboboxSelected>>", keyword_choice)


    label1.pack(pady=10)
    combobox.pack(pady=3)

    keyword_frame.pack()
    entry_frame.pack()
    widget_frame.pack()

def supprimer_keyword(category,keyword):
    if keyword!="":
        conn=create_connection("../data.db")
        del_keyword(conn,get_catnbr_from_catname(category),keyword)
        load_del_keyword()

def load_mod_keyword():
    #to do
    nettoyage_affichage_central()

def main():
    global root
    global glob_stop
    glob_stop=False
    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", sortir)
    root.title("IBS Data-Access™")
    root.geometry("500x400+400+150")
    root.description="Gestion de la base de donnée"

    if "nt" == os.name: #Si on est sur windows
        root.iconbitmap("../ico/ibs-database.ico")

    creation_affichage_central(root)
    creation_menu_barre(root)

    root.mainloop()

if __name__ == '__main__':
    main()
