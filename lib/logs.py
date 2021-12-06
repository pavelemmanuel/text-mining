from tkinter import ttk
import time
import tkinter as tk
import os


def create_logs() -> None:
    """
    Create logs instance
    """
    global logs
    text_log = ""
    error_log = ""
    logs = {
        'informations': text_log,
        'erreurs': error_log,
    }

def write_in_logs(log_tab: str, text: str) -> None:
    """
    Log one event

    :param log_tab: event category, can be either "informations" or "erreurs"
    :param text: event to be logged
    """

    # valid event category: log it
    if log_tab in logs:
        logs[log_tab]+=''.join([time.strftime('%H:%M:%S', time.localtime()),f' : {text}\n'])

    # otherwise: log error
    else:
        logs['erreurs'] += 'Tentative d\'écriture de log sur l\'onglet : ' + \
                           f'{log_tab}, celui ci n\'existe pas !'
