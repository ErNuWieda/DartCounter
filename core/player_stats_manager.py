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

import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from .database_manager import DatabaseManager
from .heatmap_generator import HeatmapGenerator
from PIL import ImageTk

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
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialisiert den PlayerStatsManager.

        Args:
            db_manager (DatabaseManager): Eine bereits initialisierte Instanz des DatabaseManagers.
        """
        self.db_manager = db_manager

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

    def _prompt_and_reset_stats(self, stats_win, player_select_combo):
        """Öffnet einen Dialog zur Bestätigung des Zurücksetzens von Statistiken."""
        selected_player = player_select_combo.get()

        # Erstellt einen modalen Dialog
        reset_dialog = tk.Toplevel(stats_win)
        reset_dialog.title("Statistiken zurücksetzen")
        reset_dialog.transient(stats_win)
        reset_dialog.grab_set()
        reset_dialog.geometry("400x150")

        # Nachricht anpassen, je nachdem ob ein Spieler ausgewählt ist
        if selected_player:
            msg = f"Möchtest du nur die Statistiken für '{selected_player}' oder die Statistiken aller Spieler zurücksetzen?"
        else:
            msg = "Möchtest du die Statistiken aller Spieler zurücksetzen?"
        ttk.Label(reset_dialog, text=msg, wraplength=380, justify="center").pack(pady=20)

        button_frame = ttk.Frame(reset_dialog)
        button_frame.pack(pady=10)

        def do_reset(player_to_reset):
            mode_name = f"'{player_to_reset}'" if player_to_reset else "alle Spieler"
            confirm_msg = f"Bist du sicher, dass du die Spiel-Statistiken für {mode_name} unwiderruflich löschen möchtest?"

            if not messagebox.askyesno("Bestätigung", confirm_msg, parent=reset_dialog):
                return

            self.db_manager.reset_game_records(player_to_reset)
            messagebox.showinfo("Erfolg", "Statistiken wurden zurückgesetzt.", parent=reset_dialog)
            reset_dialog.destroy()
            stats_win.destroy() # Schließt das Hauptfenster, um ein Neuladen zu erzwingen

        if selected_player:
            ttk.Button(button_frame, text=f"Nur '{selected_player}'", command=lambda: do_reset(selected_player)).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Alle zurücksetzen", command=lambda: do_reset(None)).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Abbrechen", command=reset_dialog.destroy).pack(side="left", padx=5)

    def update_accuracy_model(self, player_name: str, parent_window=None):
        """
        Berechnet das Wurf-Genauigkeitsmodell für einen Spieler und speichert es.
        """
        if not NUMPY_AVAILABLE:
            messagebox.showerror("Abhängigkeit fehlt", "Die 'numpy'-Bibliothek wird für die Analyse benötigt.\nBitte installieren: pip install numpy", parent=parent_window)
            return

        # 1. Alle Wurfkoordinaten des Spielers sammeln
        records = self.db_manager.get_records_for_player(player_name)
        all_coords_normalized = [coord for rec in records for coord in rec.get('all_throws_coords', []) if coord]

        if len(all_coords_normalized) < 20: # Mindestanzahl an Würfen für eine sinnvolle Analyse
            messagebox.showinfo("Nicht genügend Daten", f"Für '{player_name}' sind nicht genügend Wurfdaten für eine Analyse vorhanden.", parent=parent_window)
            return

        # 2. Würfe nach Zielsegment gruppieren
        throws_by_target = {}
        for norm_x, norm_y in all_coords_normalized:
            # Konvertiere normalisierte Koordinaten in absolute Koordinaten des Referenz-Boards
            x = norm_x * DartboardGeometry.ORIGINAL_SIZE
            y = norm_y * DartboardGeometry.ORIGINAL_SIZE
            
            # Leite das getroffene Segment ab
            segment = DartboardGeometry.get_segment_from_coords(x, y)
            target_key = f"T{segment}" # Wir nehmen an, dass auf das Triple gezielt wurde

            if target_key not in throws_by_target:
                throws_by_target[target_key] = []
            throws_by_target[target_key].append((x, y))

        # 3. Statistisches Modell für jede Zielgruppe berechnen
        accuracy_model = {}
        for target_key, coords_list in throws_by_target.items():
            if len(coords_list) < 10: continue # Mindestanzahl Würfe pro Ziel

            ideal_coords = DartboardGeometry.get_target_coords(target_key)
            if not ideal_coords: continue

            # Berechne die Abweichungen von jedem Wurf zum idealen Ziel
            deviations = np.array(coords_list) - np.array(ideal_coords)
            
            # Berechne Mittelwert (Bias) und Standardabweichung (Gruppierung)
            mean_deviation = np.mean(deviations, axis=0)
            std_deviation = np.std(deviations, axis=0)
            
            accuracy_model[target_key] = {
                'mean_offset_x': float(mean_deviation[0]),
                'mean_offset_y': float(mean_deviation[1]),
                'std_dev_x': float(std_deviation[0]),
                'std_dev_y': float(std_deviation[1]),
                'data_points': len(coords_list)
            }

        # 4. Modell in der Datenbank speichern
        if self.db_manager.update_profile_accuracy_model(player_name, accuracy_model):
            messagebox.showinfo("Erfolg", f"Genauigkeitsmodell für '{player_name}' wurde erfolgreich berechnet und gespeichert.", parent=parent_window)
        else:
            messagebox.showerror("Fehler", "Das Genauigkeitsmodell konnte nicht gespeichert werden.", parent=parent_window)

    def show_stats_window(self, parent):
        """Erstellt und zeigt das Fenster für die Spielerstatistiken an."""
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showerror("Fehler", "Die 'matplotlib'-Bibliothek wird für die Diagrammanzeige benötigt.\nBitte installieren: pip install matplotlib", parent=parent)
            return

        win = tk.Toplevel(parent)
        win.title("Spielerstatistiken")
        win.geometry("800x650")

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

        # --- Button Frame (ganz unten) ---
        # Wird vor den expandierenden Widgets gepackt, damit er immer sichtbar ist.
        bottom_frame = ttk.Frame(win, padding=10)
        bottom_frame.pack(side='bottom', fill='x')
        reset_button = ttk.Button(bottom_frame, text="Statistiken zurücksetzen...", command=lambda: self._prompt_and_reset_stats(win, player_select))
        reset_button.pack(side='right')

        # Heatmap-Button
        heatmap_button = ttk.Button(bottom_frame, text="Heatmap anzeigen", state="disabled", command=lambda: self._show_heatmap(win, player_select.get()))
        heatmap_button.pack(side='right', padx=10)

        # --- Diagramm (Mitte) ---
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.get_tk_widget().pack(side='top', fill='x', pady=10)

        # --- Tabelle (unten) ---
        table_frame = ttk.Frame(win, padding=10)
        table_frame.pack(side='top', expand=True, fill='both')
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
            heatmap_button.config(state="normal")

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

    def _show_heatmap(self, parent, player_name):
        """Sammelt alle Koordinaten für einen Spieler und zeigt die Heatmap an."""
        if not player_name:
            messagebox.showwarning("Kein Spieler", "Bitte zuerst einen Spieler auswählen.", parent=parent)
            return

        all_coords = []
        game_records = self.db_manager.get_records_for_player(player_name)
        for record in game_records:
            # 'all_throws_coords' wird als JSONB gespeichert und von psycopg2 als Liste zurückgegeben
            coords_list = record.get('all_throws_coords')
            if coords_list and isinstance(coords_list, list):
                all_coords.extend(coords_list)

        if not all_coords:
            messagebox.showinfo("Keine Daten", f"Für {player_name} wurden keine Wurf-Koordinaten für eine Heatmap gefunden.", parent=parent)
            return

        # Skalierungslogik analog zur DartBoard-Klasse, um eine konsistente Größe zu gewährleisten.
        screen_height = parent.winfo_screenheight()
        # Das Dartboard-Bild ist quadratisch, daher reicht die Höhe zur Skalierung.
        target_height = int(screen_height * 0.90)
        target_size = (target_height, target_height)

        heatmap_img = HeatmapGenerator.create_heatmap(all_coords, target_size)
        if not heatmap_img:
            messagebox.showerror("Fehler", "Die Heatmap konnte nicht erstellt werden.", parent=parent)
            return

        # Neues Fenster für die Heatmap erstellen
        heatmap_win = tk.Toplevel(parent)
        heatmap_win.title(f"Heatmap für {player_name}")
        heatmap_win.resizable(False, False)

        photo = ImageTk.PhotoImage(heatmap_img)
        img_label = ttk.Label(heatmap_win, image=photo)
        img_label.image = photo # Wichtig: Referenz behalten, um Garbage Collection zu verhindern
        img_label.pack()

        heatmap_win.grab_set()