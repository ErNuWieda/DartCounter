# Dartcounter Deluxe
# Copyright (C) 2025 Martin Hehl (airnooweeda)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import tkinter as tk
from tkinter import messagebox

def show_message(msg_type: str, title: str, message: str, parent=None):
    """
    Zeigt eine zentrale MessageBox des angegebenen Typs an.
    Kapselt die tkinter-Aufrufe an einem Ort.

    Args:
        msg_type (str): Der Typ der Nachricht ('info', 'warning', 'error').
        title (str): Der Titel des Dialogfensters.
        message (str): Die anzuzeigende Nachricht.
        parent (tk.Widget, optional): Das übergeordnete Fenster.
    """
    msg_func = {'info': messagebox.showinfo, 'warning': messagebox.showwarning, 'error': messagebox.showerror}.get(msg_type)
    if msg_func:
        msg_func(title, message, parent=parent)

def ask_question(buttons: str, title: str, message: str, parent=None) -> bool | None:
    """
    Zeigt eine zentrale Frage-MessageBox an und gibt die Antwort zurück.
    Kapselt die tkinter-Aufrufe an einem Ort.

    Args:
        buttons (str): Der Typ der Buttons ('yesno', 'okcancel', etc.).
        title (str): Der Titel des Dialogfensters.
        message (str): Die anzuzeigende Frage.
        parent (tk.Widget, optional): Das übergeordnete Fenster.
    """
    ask_func = {
        'yesno': tk.messagebox.askyesno,
        'yesnocancel': tk.messagebox.askyesnocancel,
        'retrycancel': tk.messagebox.askretrycancel,
        'okcancel': tk.messagebox.askokcancel
        }.get(buttons)
        
    if ask_func:
        return ask_func(title, message, parent=parent)
    return None # Fallback