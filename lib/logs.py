from tkinter import ttk
import time
import tkinter as tk
import os


def create_logs() -> None:
    """
    Create logs instance
    """
    global logs
    text_log = tk.StringVar()
    error_log = tk.StringVar()
    logs = {
        'informations': text_log,
        'erreurs': error_log,
    }


def create_logs_window(root: tk.Tk) -> None:
    """
    Create logs window
    :param root: main window of an application
    """
    # initialize the window
    new_window = tk.Toplevel(root)
    new_window.geometry('400x300+80+200')
    # OS is windows:
    if 'nt' == os.name:
        new_window.iconbitmap('./ico/info.ico')
    tabs = ttk.Notebook(new_window)

    # create the informations tab
    tab_info = ttk.Frame(tabs)
    text_info = tk.Label(tab_info,
                         textvariable=logs['informations'],
                         anchor='w',
                         justify='left')
    text_info.pack(fill='both')

    # create the errors tab
    tab_error = ttk.Frame(tabs)
    text_error = tk.Label(tab_error,
                          textvariable=logs['erreurs'],
                          anchor='w',
                          justify='left')
    text_error.pack(fill='both')

    # configure text visualization
    def set_label_wrap(event: tk.Event) -> None:
        """
        Wrap event label for better visualization
        """
        # 12, to account for padding and borderwidth
        wraplength = event.width-12
        event.widget.configure(wraplength=wraplength)
    text_info.bind('<Configure>', set_label_wrap)
    text_error.bind('<Configure>', set_label_wrap)

    # add the tabs for each category
    tabs.add(tab_info, text='Informations')  # does the packing for tab_info
    tabs.add(tab_error, text='Erreurs')     # and tab_error
    tabs.pack(fill='both', expand='true')


def write_in_logs(log_tab: str, text: str, glob_stop: bool = True) -> None:
    """
    Log one event
    :param log_tab: event category, can be either "informations" or "erreurs"
    :param text: event to be logged
    :param glob_stop: whether or not the program was already closed
    """
    # program already closed: abort
    if glob_stop:
        return

    # valid event category: log it
    if log_tab in logs:
        logs[log_tab].set(''.join([
            logs[log_tab].get(),
            time.strftime('%H:%M:%S', time.localtime()),
            f' : {text}\n',
        ]))

    # otherwise: log error
    else:
        logs['erreurs'] += 'Tentative d\'écriture de log sur l\'onglet : ' + \
                           f'{log_tab}, celui ci n\'existe pas !'
