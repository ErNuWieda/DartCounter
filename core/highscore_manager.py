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
from tkinter import ttk, filedialog, font
from .database_manager import DatabaseManager
import csv
from .settings_manager import get_app_data_dir
from . import ui_utils


class HighscoreManager:
    """
    Verwaltet die Highscore-Logik und die Interaktion mit dem Benutzer.

    Diese Klasse dient als Schnittstelle zwischen der Benutzeroberfläche und der
    Datenbanklogik für Highscores. Sie ist verantwortlich für:
    - Das Anzeigen der Highscores in einem eigenen Fenster.
    - Das Hinzufügen neuer Highscore-Einträge nach einem Spielende.
    - Das Exportieren der Highscores in eine CSV-Datei.
    - Das sichere Zurücksetzen von Highscores nach Benutzerbestätigung.

    Sie delegiert alle direkten Datenbankoperationen an eine Instanz des
    `DatabaseManager`.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialisiert den HighscoreManager.

        Args:
            db_manager (DatabaseManager): Eine bereits initialisierte Instanz des DatabaseManagers.
        """
        self.db_manager = db_manager

    def add_score(self, game_mode, player_name, score_metric):
        """
        Fügt einen neuen Highscore-Eintrag hinzu.

        Prüft, ob eine Datenbankverbindung besteht und ob der Spielmodus für Highscores
        relevant ist. Delegiert das Hinzufügen des Eintrags an den `DatabaseManager`.

        Args:
            game_mode (str): Der Spielmodus (z.B. "301").
            player_name (str): Der Name des Spielers.
            score_metric (float or int): Die Punktzahl (z.B. Darts für X01, MPR für Cricket).
        """
        if not self.db_manager.is_connected:
            return

        # Nur für definierte Spiele verfolgen
        valid_modes = ["301", "501", "701", "Cricket", "Cut Throat", "Tactics"]
        if str(game_mode) not in valid_modes:
            return

        self.db_manager.add_score(str(game_mode), player_name, score_metric)

    def export_highscores_to_csv(self, parent):
        """
        Exportiert alle Highscores aus der Datenbank in eine CSV-Datei.

        Öffnet einen "Speichern unter"-Dialog, damit der Benutzer einen Speicherort
        auswählen kann. Ruft alle Highscores für die definierten Spielmodi ab,
        formatiert sie und schreibt sie in die ausgewählte CSV-Datei.

        Args:
            parent (tk.Widget): Das übergeordnete Fenster für Dialoge.
        """
        if not self.db_manager.is_connected:
            ui_utils.show_message(
                "warning",
                "Datenbankfehler",
                "Keine Verbindung zur Datenbank möglich.",
                parent=parent,
            )
            return

        # Verzeichnis für CSV-Exporte definieren und bei Bedarf erstellen
        hiscores_dir = get_app_data_dir() / "hiscores"
        hiscores_dir.mkdir(parents=True, exist_ok=True)

        filepath = filedialog.asksaveasfilename(
            initialdir=hiscores_dir,
            title="Highscores als CSV exportieren...",
            defaultextension=".csv",
            filetypes=(("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")),
        )

        if not filepath:
            return  # User cancelled

        all_scores = []
        highscore_modes = ["301", "501", "701", "Cricket", "Cut Throat", "Tactics"]
        for game_mode in highscore_modes:
            scores = self.db_manager.get_scores(game_mode)
            for score in scores:
                all_scores.append(
                    {
                        "game_mode": game_mode,
                        "player_name": score["player_name"],
                        "score": score["score_metric"],
                        "date": score["date"].strftime("%Y-%m-%d"),
                    }
                )

        if not all_scores:
            ui_utils.show_message(
                "info",
                "Export",
                "Keine Highscores zum Exportieren vorhanden.",
                parent=parent,
            )
            return

        try:
            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["game_mode", "player_name", "score", "date"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_scores)
            ui_utils.show_message(
                "info",
                "Erfolg",
                f"Highscores erfolgreich exportiert nach:\n{filepath}",
                parent=parent,
            )
        except IOError as e:
            ui_utils.show_message(
                "error",
                "Exportfehler",
                f"Fehler beim Schreiben der CSV-Datei: {e}",
                parent=parent,
            )

    def _prompt_and_reset(self, highscore_win, notebook):
        """
        Öffnet einen Dialog zur Bestätigung des Zurücksetzens von Highscores.

        Diese private Hilfsmethode wird durch den "Zurücksetzen"-Button aufgerufen.
        Sie erstellt ein modales Dialogfenster, das dem Benutzer die Wahl gibt,
        entweder nur die Highscores des aktuell angezeigten Tabs oder alle
        Highscores zu löschen. Die eigentliche Löschoperation wird erst nach einer
        weiteren Bestätigung durchgeführt.

        Args:
            highscore_win (tk.Toplevel): Das übergeordnete Highscore-Fenster.
            notebook (ttk.Notebook): Das Notebook-Widget, um den aktuellen Tab zu ermitteln.
        """

        current_tab_index = notebook.index(notebook.select())
        current_game_mode = notebook.tab(current_tab_index, "text")

        reset_dialog = tk.Toplevel(highscore_win)
        reset_dialog.title("Highscores zurücksetzen")
        reset_dialog.transient(highscore_win)
        reset_dialog.grab_set()
        reset_dialog.geometry("350x150")

        msg = f"Möchtest du die Highscores für '{current_game_mode}' oder alle Highscores zurücksetzen?"
        ttk.Label(reset_dialog, text=msg, wraplength=330, justify="center").pack(pady=20)

        button_frame = ttk.Frame(reset_dialog)
        button_frame.pack(pady=10)

        def do_reset(mode):
            mode_name = current_game_mode if mode else "alle Spielmodi"
            confirm_msg = f"Bist du sicher, dass du die Highscores für '{mode_name}' unwiderruflich löschen möchtest?"  # noqa: E501

            if not ui_utils.ask_question("yesno", "Bestätigung", confirm_msg, parent=reset_dialog):
                return

            self.db_manager.reset_scores(mode)
            ui_utils.show_message(  # type: ignore
                "info",
                "Erfolg",
                "Highscores wurden zurückgesetzt.",
                parent=reset_dialog,
            )
            reset_dialog.destroy()
            highscore_win.destroy()  # Schließt das Highscore-Fenster, um ein Neuladen zu erzwingen

        ttk.Button(
            button_frame,
            text=f"Nur '{current_game_mode}'",
            command=lambda: do_reset(current_game_mode),  # type: ignore
        ).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Alle zurücksetzen", command=lambda: do_reset(None)).pack(
            side="left", padx=5
        )
        ttk.Button(button_frame, text="Abbrechen", command=reset_dialog.destroy).pack(
            side="left", padx=5
        )

    def show_highscores_window(self, root):
        """
        Erstellt und zeigt das Highscore-Fenster an.

        Prüft zunächst, ob eine Datenbankverbindung besteht. Erstellt dann ein
        Toplevel-Fenster mit einem `ttk.Notebook` für die verschiedenen X01-Spielmodi.
        Für jeden Modus werden die Highscores aus der Datenbank abgerufen und in
        einem `ttk.Treeview` dargestellt. Fügt außerdem Buttons zum Exportieren
        und Zurücksetzen der Highscores hinzu.

        Args:
            root (tk.Tk): Das Hauptfenster der Anwendung, das als Parent dient.
        """
        if not self.db_manager.is_connected:
            ui_utils.show_message(
                "warning",
                "Datenbankfehler",
                "Keine Verbindung zur Highscore-Datenbank möglich.\nBitte prüfe die `config.ini` und den Datenbank-Server.",
                parent=root,
            )
            return

        win = tk.Toplevel(root)
        win.title("Highscores")
        win.geometry("500x480")
        win.resizable(False, True)

        notebook = ttk.Notebook(win)
        notebook.pack(expand=True, fill="both", padx=10, pady=10)

        highscore_modes = ["301", "501", "701", "Cricket", "Cut Throat", "Tactics"]
        for game_mode in highscore_modes:
            frame = ttk.Frame(notebook, padding="10")
            notebook.add(frame, text=f"{game_mode}")

            # Spaltenüberschrift dynamisch anpassen
            score_header = "MPR" if game_mode in ("Cricket", "Cut Throat", "Tactics") else "Darts"

            tree = ttk.Treeview(frame, columns=("Rank", "Player", "Score", "Date"), show="headings")
            tree.heading("Rank", text="Platz")
            tree.column("Rank", width=50, anchor="center")
            tree.heading("Player", text="Spieler")
            tree.column("Player", width=150)
            tree.heading("Score", text=score_header)
            tree.column("Score", width=80, anchor="center")
            tree.heading("Date", text="Datum")
            tree.column("Date", width=100, anchor="center")

            # NEU: Tag für persönliche Bestleistungen konfigurieren
            # Wir leiten die Schriftart vom Treeview ab, um themenkonsistent zu sein
            try:
                default_font = font.nametofont(tree.cget("font"))
                bold_font = default_font.copy()
                bold_font.configure(weight="bold")
                tree.tag_configure("personal_best", font=bold_font)
            except tk.TclError:
                # Fallback, falls die Schriftart nicht gefunden wird
                tree.tag_configure("personal_best", font="-weight bold")

            # NEU: Persönliche Bestleistungen für alle Spieler in diesem Modus abrufen
            personal_bests = self.db_manager.get_personal_bests_for_mode(game_mode)

            scores = self.db_manager.get_scores(game_mode)
            for i, score in enumerate(scores):
                # Score-Wert korrekt formatieren
                score_value = score["score_metric"]
                formatted_score = (
                    f"{score_value:.2f}"
                    if game_mode in ("Cricket", "Cut Throat", "Tactics")
                    else int(score_value)
                )

                player_name = score["player_name"]
                tags = (
                    ("personal_best",)
                    if player_name in personal_bests and score_value == personal_bests[player_name]
                    else ()
                )
                tree.insert(
                    "",
                    "end",
                    values=(
                        f"{i+1}.",
                        player_name,
                        formatted_score,
                        score["date"].strftime("%Y-%m-%d"),
                    ),
                    tags=tags,
                )

            tree.pack(expand=True, fill="both")

        # Frame für Buttons am unteren Rand
        bottom_frame = ttk.Frame(win)
        bottom_frame.pack(pady=(5, 10), fill="x", side="bottom")

        export_button = ttk.Button(
            bottom_frame,
            text="Als CSV exportieren",
            command=lambda: self.export_highscores_to_csv(win),
        )
        export_button.pack(side="left", padx=20)

        reset_button = ttk.Button(
            bottom_frame,
            text="Highscores zurücksetzen",
            command=lambda: self._prompt_and_reset(win, notebook),
        )
        reset_button.pack(side="right", padx=20)

        return win
