import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from .database_manager import DatabaseManager
import csv
import os


class HighscoreManager:
    """
    Verwaltet die Highscore-Logik und -Anzeige durch Interaktion mit dem DatabaseManager.
    """
    def __init__(self):
        self.db_manager = DatabaseManager()

    def add_score(self, game_mode, player_name, darts_used):
        """Fügt einen neuen Score hinzu, wenn es ein Highscore ist."""
        if not self.db_manager.is_connected:
            return
        
        # Nur für definierte X01-Spiele verfolgen
        if str(game_mode) not in ["301", "501", "701"]:
            return
        
        self.db_manager.add_score(str(game_mode), player_name, darts_used)

    def export_highscores_to_csv(self):
        """Exportiert alle Highscores in eine CSV-Datei."""
        if not self.db_manager.is_connected:
            messagebox.showwarning("Datenbankfehler", "Keine Verbindung zur Datenbank möglich.")
            return

        filepath = filedialog.asksaveasfilename(
            initialdir=os.path.expanduser('~'),
            title="Highscores als CSV exportieren...",
            defaultextension=".csv",
            filetypes=(("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*"))
        )

        if not filepath:
            return  # User cancelled

        all_scores = []
        for game_mode in ["301", "501", "701"]:
            scores = self.db_manager.get_scores(game_mode)
            for score in scores:
                all_scores.append({
                    'game_mode': game_mode,
                    'player_name': score['player_name'],
                    'darts_used': score['darts_used'],
                    'date': score['date'].strftime("%Y-%m-%d")
                })

        if not all_scores:
            messagebox.showinfo("Export", "Keine Highscores zum Exportieren vorhanden.")
            return

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['game_mode', 'player_name', 'darts_used', 'date']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_scores)
            messagebox.showinfo("Erfolg", f"Highscores erfolgreich exportiert nach:\n{filepath}")
        except IOError as e:
            messagebox.showerror("Exportfehler", f"Fehler beim Schreiben der CSV-Datei: {e}")

    def _prompt_and_reset(self, highscore_win, notebook):
        """Öffnet einen Dialog zur Bestätigung des Zurücksetzens von Highscores."""
        
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
            confirm_msg = f"Bist du sicher, dass du die Highscores für '{mode_name}' unwiderruflich löschen möchtest?"
            
            if not messagebox.askyesno("Bestätigung", confirm_msg, parent=reset_dialog):
                return
            
            self.db_manager.reset_scores(mode)
            messagebox.showinfo("Erfolg", "Highscores wurden zurückgesetzt.", parent=reset_dialog)
            reset_dialog.destroy()
            highscore_win.destroy() # Schließt das Highscore-Fenster, um ein Neuladen zu erzwingen

        ttk.Button(button_frame, text=f"Nur '{current_game_mode}'", command=lambda: do_reset(current_game_mode)).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Alle zurücksetzen", command=lambda: do_reset(None)).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Abbrechen", command=reset_dialog.destroy).pack(side="left", padx=5)

    def show_highscores_window(self, root):
        """Zeigt die Highscores in einem Toplevel-Fenster an."""
        if not self.db_manager.is_connected:
            messagebox.showwarning("Datenbankfehler", "Keine Verbindung zur Highscore-Datenbank möglich.\nBitte prüfe die `config.ini` und den Datenbank-Server.")
            return

        win = tk.Toplevel(root)
        win.title("Highscores")
        win.geometry("500x480")
        win.resizable(False, True)

        notebook = ttk.Notebook(win)
        notebook.pack(expand=True, fill="both", padx=10, pady=10)

        for game_mode in ["301", "501", "701"]:
            frame = ttk.Frame(notebook, padding="10")
            notebook.add(frame, text=f"{game_mode}")

            tree = ttk.Treeview(frame, columns=("Rank", "Player", "Darts", "Date"), show="headings")
            tree.heading("Rank", text="Platz"); tree.column("Rank", width=50, anchor="center")
            tree.heading("Player", text="Spieler"); tree.column("Player", width=150)
            tree.heading("Darts", text="Darts"); tree.column("Darts", width=80, anchor="center")
            tree.heading("Date", text="Datum"); tree.column("Date", width=100, anchor="center")

            scores = self.db_manager.get_scores(game_mode)
            for i, score in enumerate(scores):
                tree.insert("", "end", values=(f"{i+1}.", score['player_name'], score['darts_used'], score['date'].strftime("%Y-%m-%d")))

            tree.pack(expand=True, fill="both")

        # Frame für Buttons am unteren Rand
        bottom_frame = ttk.Frame(win)
        bottom_frame.pack(pady=(5, 10), fill='x', side='bottom')

        export_button = ttk.Button(bottom_frame, text="Als CSV exportieren", command=self.export_highscores_to_csv)
        export_button.pack(side='left', padx=20)
        
        reset_button = ttk.Button(bottom_frame, text="Highscores zurücksetzen", command=lambda: self._prompt_and_reset(win, notebook))
        reset_button.pack(side='right', padx=20)