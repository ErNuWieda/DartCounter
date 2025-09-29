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
from tkinter import ttk, messagebox


def show_message(
    msg_type: str,
    title: str,
    message: str,
    parent=None,
    auto_close_for_ai_after_ms: int = 0,
):
    """
    Zeigt eine zentrale MessageBox des angegebenen Typs an.
    Kann sich für KI-Spieler nach einem Timeout automatisch schließen.

    Args:
        msg_type (str): Der Typ der Nachricht ('info', 'warning', 'error').
        title (str): Der Titel des Dialogfensters.
        message (str): Die anzuzeigende Nachricht.
        parent (tk.Widget, optional): Das übergeordnete Fenster.
        auto_close_for_ai_after_ms (int): Wenn > 0, wird ein nicht-nativer Dialog
                                          erstellt, der sich nach X Millisekunden
                                          selbst schließt.
    """
    if auto_close_for_ai_after_ms > 0 and parent:
        # Erstelle einen benutzerdefinierten, modalen Dialog
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.transient(parent)
        dialog.resizable(False, False)

        # Nachricht
        msg_frame = ttk.Frame(dialog, padding=20)
        msg_frame.pack(expand=True, fill=tk.BOTH)
        ttk.Label(msg_frame, text=message, wraplength=350, justify="center").pack()

        # OK-Button, der den Dialog und den Timer schließt
        button_frame = ttk.Frame(dialog, padding=(0, 0, 0, 10))
        button_frame.pack()

        after_id = [
            None
        ]  # Verwende eine Liste, um sie in der verschachtelten Funktion veränderbar zu machen

        def on_ok():
            if after_id[0]:
                dialog.after_cancel(after_id[0])
            dialog.destroy()

        ok_button = ttk.Button(button_frame, text="OK", command=on_ok, style="Accent.TButton")
        ok_button.pack()
        ok_button.bind("<Return>", lambda e: on_ok())
        ok_button.focus_set()

        # Timer zum automatischen Schließen starten
        after_id[0] = dialog.after(auto_close_for_ai_after_ms, on_ok)

        # Fenster zentrieren und modal machen
        dialog.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        dialog_w = dialog.winfo_reqwidth()
        dialog_h = dialog.winfo_reqheight()
        x = parent_x + (parent_w // 2) - (dialog_w // 2)
        y = parent_y + (parent_h // 2) - (dialog_h // 2)
        dialog.geometry(f"+{x}+{y}")

        dialog.grab_set()
        dialog.wait_window()  # Macht den Dialog blockierend, wie eine echte MessageBox
    else:
        # Standard-MessageBox verwenden
        msg_func = {
            "info": messagebox.showinfo,
            "warning": messagebox.showwarning,
            "error": messagebox.showerror,
        }.get(msg_type)
        if msg_func:
            msg_func(title, message, parent=parent)


def ask_question(buttons: str, title: str, message: str, default=None, parent=None) -> bool | None:
    """
    Zeigt eine zentrale Frage-MessageBox an und gibt die Antwort zurück.
    Kapselt die tkinter-Aufrufe an einem Ort.

    Args:
        buttons (str): Der Typ der Buttons ('yesno', 'okcancel', etc.).
        title (str): Der Titel des Dialogfensters.
        message (str): Die anzuzeigende Frage.
        parent (tk.Widget, optional): Das übergeordnete Fenster.
    """
    # Hole die Funktion dynamisch zur Laufzeit über getattr.
    # Dies stellt sicher, dass Mocks in Tests korrekt angewendet werden.
    func_name = f"ask{buttons}"
    ask_func = getattr(messagebox, func_name, None)

    if ask_func:
        return ask_func(title, message, default=default, parent=parent)
    return None
