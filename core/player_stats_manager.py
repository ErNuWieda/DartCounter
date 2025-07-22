import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from .database_manager import DatabaseManager

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.dates import DateFormatter
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

class PlayerStatsManager:
    """
    Verwaltet das Laden, Speichern und Anzeigen von persistenten Spielerstatistiken.

    Diese Klasse sammelt die Ergebnisse jedes abgeschlossenen Spiels und speichert
    sie in einer JSON-Datei, um den Formverlauf der Spieler über die Zeit zu verfolgen.
    """
    def __init__(self):
        self.db_manager = DatabaseManager()

    def add_game_record(self, player_name, game_stats):
        """
        Fügt den Statistik-Datensatz eines beendeten Spiels für einen Spieler hinzu,
        indem er ihn in die Datenbank schreibt.

        Args:
            player_name (str): Der Name des Spielers.
            game_stats (dict): Ein Dictionary mit den Statistiken des Spiels.
        """
        if not self.db_manager.is_connected:
            return
        
        # Füge Zeitstempel hinzu
        game_stats['date'] = datetime.now()
        self.db_manager.add_game_record(player_name, game_stats)

    def get_all_player_names(self):
        """Gibt eine Liste aller Spieler zurück, für die Statistiken in der DB existieren."""
        if not self.db_manager.is_connected:
            return []
        return self.db_manager.get_all_player_names_from_records()

    def show_stats_window(self, parent):
        """Erstellt und zeigt das Fenster für die Spielerstatistiken an."""
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showerror("Fehler", "Die 'matplotlib'-Bibliothek wird für die Diagrammanzeige benötigt.\nBitte installieren: pip install matplotlib", parent=parent)
            return

        win = tk.Toplevel(parent)
        win.title("Spielerstatistiken")
        win.geometry("800x600")

        # --- Steuerung (oben) ---
        control_frame = ttk.Frame(win, padding=10)
        control_frame.pack(fill='x')

        ttk.Label(control_frame, text="Spieler auswählen:").pack(side='left', padx=(0, 10))
        player_names = self.get_all_player_names()
        player_select = ttk.Combobox(control_frame, values=player_names, state="readonly")
        player_select.pack(side='left')

        # Filter für Spielmodus
        ttk.Label(control_frame, text="Spielmodus filtern:").pack(side='left', padx=(20, 10))
        game_mode_select = ttk.Combobox(control_frame, state="disabled")
        game_mode_select.pack(side='left')

        # --- Diagramm (Mitte) ---
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.get_tk_widget().pack(fill='x', pady=10)

        # --- Tabelle (unten) ---
        table_frame = ttk.Frame(win, padding=10)
        table_frame.pack(expand=True, fill='both')
        
        cols = ("Datum", "Spiel", "Avg/MPR", "Gewonnen")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor='center')
        tree.pack(expand=True, fill='both')

        # --- Logik ---
        player_games_cache = [] # Cache für die Spiele des ausgewählten Spielers

        def _refresh_views(games_to_display):
            """Aktualisiert Tabelle und Diagramm mit den übergebenen Spieldaten."""
            # Tabelle leeren und neu füllen
            tree.delete(*tree.get_children())
            for game in games_to_display:
                metric = game.get('average') or game.get('mpr') or 0
                win_status = "Ja" if game.get('is_win', False) else "Nein"
                tree.insert("", "end", values=(
                    game['game_date'].strftime('%Y-%m-%d %H:%M'),
                    game['game_mode'],
                    f"{metric:.2f}",
                    win_status
                ))

            # Diagramm aktualisieren
            ax.clear()
            selected_mode = game_mode_select.get()
            player_name = player_select.get()

            # Metrik und Titel basierend auf dem Filter bestimmen
            metric_key, metric_label = None, ""
            if selected_mode == "Alle Spiele" or selected_mode in ('301', '501', '701'):
                metric_key, metric_label = 'average', "3-Dart-Average"
            elif selected_mode in ('Cricket', 'Cut Throat', 'Tactics'):
                metric_key, metric_label = 'mpr', "Marks Per Round (MPR)"

            # Spiele für das Diagramm filtern und sortieren
            plot_games = sorted(
                [g for g in games_to_display if g.get(metric_key) is not None],
                key=lambda x: x['game_date']
            )

            if plot_games and metric_key:
                dates = [g['game_date'] for g in plot_games]
                values = [g[metric_key] for g in plot_games]
                
                ax.plot(dates, values, marker='o', linestyle='-')
                ax.set_title(f"{selected_mode} - {metric_label}-Verlauf für {player_name}")
                ax.set_ylabel(metric_label)
                ax.grid(True)
                ax.xaxis.set_major_formatter(DateFormatter('%d.%m.%y'))
                fig.autofmt_xdate()
            else:
                ax.set_title(f"Keine Daten für Diagramm gefunden ({selected_mode})")

            canvas.draw()

        def on_player_select(event=None):
            """Wird aufgerufen, wenn ein Spieler ausgewählt wird."""
            nonlocal player_games_cache
            player_name = player_select.get()
            if not player_name:
                return

            # Daten aus der DB holen und cachen
            player_games_cache = self.db_manager.get_records_for_player(player_name)
            
            # Spielmodus-Filter aktualisieren
            modes = sorted(list(set(g['game_mode'] for g in player_games_cache)))
            game_mode_select['values'] = ["Alle Spiele"] + modes
            game_mode_select.set("Alle Spiele")
            game_mode_select.config(state="readonly")

            _refresh_views(player_games_cache)

        def on_game_mode_select(event=None):
            """Wird aufgerufen, wenn ein Spielmodus im Filter ausgewählt wird."""
            selected_mode = game_mode_select.get()
            if selected_mode == "Alle Spiele":
                _refresh_views(player_games_cache)
            else:
                filtered_games = [g for g in player_games_cache if g['game_mode'] == selected_mode]
                _refresh_views(filtered_games)

        player_select.bind("<<ComboboxSelected>>", on_player_select)
        game_mode_select.bind("<<ComboboxSelected>>", on_game_mode_select)