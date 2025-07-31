#!python3 
# -*- coding: utf-8 -*-

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
from core._version import __version__
from tkinter import ttk
from PIL import Image, ImageTk
import sys
import sv_ttk
from core.settings_manager import SettingsManager
import pathlib
from core.gamemgr import GameManager
from core.game import Game
from core.dartboard import DartBoard
from core.save_load_manager import SaveLoadManager
from core.sound_manager import SoundManager
from core.player_stats_manager import PlayerStatsManager
from core.highscore_manager import HighscoreManager
from core.database_manager import DatabaseManager
from core.player_profile_manager import PlayerProfileManager
from core.profile_manager_dialog import ProfileManagerDialog
from core.settings_dialog import AppSettingsDialog
from core.tournament_dialog import TournamentSettingsDialog
from core.app_menu import AppMenu
from core.tournament_view import TournamentView
from core.tournament_manager import TournamentManager
from core import ui_utils

def get_asset_path(relative_path):
    """
    Gibt den korrekten Pfad zu einer Asset-Datei zurück, egal ob das Skript
    als normale .py-Datei oder als gepackte Anwendung (PyInstaller) läuft.
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller erstellt einen temporären Ordner und speichert den Pfad in _MEIPASS
        base_path = pathlib.Path(sys._MEIPASS)
    else:
        # Wenn wir nicht im gepackten Modus sind, verwenden wir den normalen Pfad
        base_path = pathlib.Path(__file__).resolve().parent

    return base_path / pathlib.Path(relative_path)

class App:
    """
    Die Hauptanwendungsklasse, die als zentraler Orchestrator fungiert.

    Verantwortlichkeiten:
    - Initialisierung des Hauptfensters und der Menüs.
    - Verwaltung des Lebenszyklus der Anwendung.
    - Instanziierung und Koordination der verschiedenen Manager (Settings, Sound, etc.).
    - Starten, Laden und Beenden von Spielsitzungen (`Game`-Instanzen).
    """
    def __init__(self, root):
        self.root = root
        self.version = f"v{__version__}"
        
        # Manager-Instanzen als Instanzvariablen
        self.settings_manager = SettingsManager()
        self.sound_manager = SoundManager(self.settings_manager, self.root)

        # --- Dependency Injection für DatabaseManager ---
        # Einmal erstellen und an die abhängigen Manager weitergeben, um doppelte
        # Verbindungen und Log-Ausgaben zu vermeiden.
        self.db_manager = DatabaseManager()
        self.highscore_manager = HighscoreManager(self.db_manager)
        self.player_stats_manager = PlayerStatsManager(self.db_manager)
        self.profile_manager = PlayerProfileManager(self.db_manager)

        self.game_instance = None
        self.tournament_manager = None
        self.tournament_view = None

        # UI-Setup
        self._setup_window()
        self._setup_menu()
        self._setup_main_canvas()

    def _setup_window(self):
        # Theme anwenden (NACH dem Erstellen des root-Fensters, aber VOR dem Rest)
        theme = self.settings_manager.get('theme', 'light')
        # Sicherstellen, dass nur gültige Themes verwendet werden, um Abstürze zu vermeiden
        if theme not in ('light', 'dark'):
            print(f"Warnung: Ungültiges Theme '{theme}' in den Einstellungen gefunden. Fallback auf 'light'.")
            theme = 'light'
            self.settings_manager.set('theme', 'light') # Korrigiert die Einstellung für zukünftige Starts
        sv_ttk.set_theme(theme)

        self.root.geometry("300x300")
        self.root.title(f"Dartcounter {self.version}")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_game)
        self.root.bind("<Escape>", lambda e: self.quit_game())

    def _setup_menu(self):
        self.menu = AppMenu(self.root, self)

    def _setup_main_canvas(self):
        assets_base_dir = get_asset_path("assets")
        image_path = assets_base_dir / "darthead.png"
        try:
            image = Image.open(image_path)
        except FileNotFoundError:
            ui_utils.show_message('error', "Fehler", f"Image nicht gefunden: {image_path}", parent=self.root)
            self.root.quit()
            return
        except Exception as e:
            ui_utils.show_message('error', "Fehler", f"Fehler beim Laden des Images: {e}", parent=self.root)
            self.root.quit()
            return

        new_size = (275, 275)
        resized = image.resize(new_size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(resized)
        canvas = tk.Canvas(self.root, width=new_size[0], height=new_size[1])
        canvas.pack(fill="both", expand=True)
        x_pos = (300 - new_size[0]) // 2
        y_pos = (300 - new_size[1]) // 2
        canvas.create_image(x_pos, y_pos, image=photo, anchor=tk.NW)
        canvas.image = photo
        canvas.bind("<Button-1>", lambda e: self.new_game())

    def _close_any_active_session(self):
        """Finds and closes any active game or tournament session unconditionally."""
        if self.game_instance and not self.game_instance.end:
            self.game_instance.destroy()
            self.game_instance = None

        if self.tournament_manager and not self.tournament_manager.is_finished:
            if self.tournament_view and self.tournament_view.winfo_exists():
                self.tournament_view.destroy()
            self.tournament_manager = None
            self.tournament_view = None

    def _check_and_close_existing_game(self, title, message):
        """
        Prüft, ob ein Spiel oder Turnier läuft, fragt den Benutzer und beendet es ggf.
        Gibt True zurück, wenn fortgefahren werden kann, sonst False.
        """
        activity_type = None
        if self.game_instance and not self.game_instance.end:
            activity_type = "Spiel"
        elif self.tournament_manager and not self.tournament_manager.is_finished:
            activity_type = "Turnier"

        if activity_type:
            # Die übergebene 'message' wird für die Abfrage verwendet.
            if not ui_utils.ask_question('yesno', title, message, parent=self.root):
                return False  # User cancelled

            # Bestehende Aktivität beenden
            if activity_type == "Spiel":
                self.game_instance.destroy()
                self.game_instance = None
            elif activity_type == "Turnier":
                if self.tournament_view and self.tournament_view.winfo_exists():
                    self.tournament_view.destroy()
                self.tournament_manager = None
                self.tournament_view = None
        return True

    def _initialize_game_session(self, game_options, player_names):
        """Erstellt die Game-Instanz, die ihre eigene UI initialisiert."""
        return Game(self.root, game_options, player_names, self.sound_manager, self.highscore_manager, self.player_stats_manager, self.profile_manager)

    def _create_game_options(self, source):
        """Erstellt ein standardisiertes game_options-Dictionary aus verschiedenen Quellen."""
        # Wir verwenden Duck-Typing (hasattr), da isinstance in Tests mit
        # gemockten Klassen fehlschlägt. Dies ist robuster.
        if hasattr(source, 'configure_game'):
            return {
                "name": source.game,
                "opt_in": source.opt_in,
                "opt_out": source.opt_out,
                "opt_atc": source.opt_atc,
                "count_to": source.count_to,
                "lifes": source.lifes,
                "rounds": source.rounds
            }
        # Annahme: source ist ein Dictionary aus einer Speicherdatei
        return {
            "name": source['game_name'],
            "opt_in": source['opt_in'],
            "opt_out": source['opt_out'],
            "opt_atc": source['opt_atc'],
            "count_to": str(source['count_to']),
            "lifes": str(source['lifes']),
            "rounds": str(source['rounds'])
        }

    def new_game(self):
        """Startet den Workflow zum Erstellen eines neuen Spiels."""
        if not self._check_and_close_existing_game("Neues Spiel", "Ein Spiel läuft bereits. Möchtest du es beenden und ein neues starten?"):
            return

        self.root.withdraw()
        gm = GameManager(self.sound_manager, self.settings_manager, self.profile_manager)

        if gm.configure_game(self.root):
            game_options = self._create_game_options(gm)
            self.game_instance = self._initialize_game_session(game_options, gm.players)
            self.game_instance.announce_current_player_turn()
            # Warten, bis das Spielfenster geschlossen wird, um das Hauptfenster wieder anzuzeigen.
            self.root.wait_window(self.game_instance.ui.db.root)
            self.root.deiconify()
        else:
            self.root.deiconify()

    def new_tournament(self):
        """Startet den Workflow zum Erstellen eines neuen Turniers."""
        # Generische Nachricht, da die Aktivität ein Spiel oder ein Turnier sein kann.
        if not self._check_and_close_existing_game("Neues Turnier", "Eine andere Aktivität läuft bereits. Möchtest du sie beenden und ein Turnier starten?"):
            return

        dialog = TournamentSettingsDialog(self.root, self.profile_manager, self.settings_manager)
        if not dialog.cancelled:
            # Erstelle ein game_options-Dictionary aus den Dialog-Ergebnissen
            game_options = {
                "name": dialog.game_mode,
                "opt_in": "Single", "opt_out": "Double", "opt_atc": "Single", # Standardwerte für Turnier
                "count_to": dialog.game_mode,
                "lifes": "3", "rounds": "7"
            }
            # Erstelle die TournamentManager-Instanz
            self.tournament_manager = TournamentManager(
                player_names=dialog.player_names,
                game_mode=dialog.game_mode,
                game_options=game_options
            )
            # Statt der MessageBox, öffne die neue Turnieransicht
            self.tournament_view = TournamentView(self.root, self.tournament_manager, self.start_next_tournament_match)

    def save_tournament(self):
        """Speichert den Zustand des aktuell laufenden Turniers."""
        if self.tournament_manager and not self.tournament_manager.is_finished:
            SaveLoadManager.save_tournament_state(self.tournament_manager, self.root)
        else:
            ui_utils.show_message('info', "Turnier speichern", "Es läuft kein aktives Turnier, das gespeichert werden könnte.", parent=self.root)

    def load_tournament(self):
        """Startet den Workflow zum Laden eines gespeicherten Turniers."""
        if not self._check_and_close_existing_game("Turnier laden", "Eine andere Aktivität läuft bereits. Möchtest du sie beenden und ein Turnier laden?"):
            return

        data = SaveLoadManager.load_tournament_data(self.root)
        if not data:
            return

        self.tournament_manager = TournamentManager.from_dict(data)
        self.tournament_view = TournamentView(self.root, self.tournament_manager, self.start_next_tournament_match)

    def load_game(self):
        """Startet den Workflow zum Laden eines gespeicherten Spiels."""
        if not self._check_and_close_existing_game("Spiel laden", "Ein Spiel läuft bereits. Möchtest du es beenden und ein anderes laden?"):
            return

        data = SaveLoadManager.load_game_data(self.root)
        if not data:
            return

        self.root.withdraw()
        game_options = self._create_game_options(data)
        player_names = [p['name'] for p in data['players']]

        loaded_game = self._initialize_game_session(game_options, player_names)
        SaveLoadManager.restore_game_state(loaded_game, data)
        self.game_instance = loaded_game
        # Warten und Hauptfenster wiederherstellen
        self.root.wait_window(self.game_instance.ui.db.root)
        self.root.deiconify()
        self.game_instance.announce_current_player_turn()

    def start_next_tournament_match(self):
        """Wird von der TournamentView aufgerufen, um das nächste Match zu starten."""
        match = self.tournament_manager.get_next_match()
        if not match:
            # Sollte nicht passieren, wenn der Button geklickt wird, aber als Sicherheitsnetz.
            return

        # Verstecke das Turnierfenster, während ein Match läuft
        if self.tournament_view and self.tournament_view.winfo_exists():
            self.tournament_view.withdraw()

        game_options = self.tournament_manager.game_options
        player_names = [match['player1'], match['player2']]
        self.game_instance = self._initialize_game_session(game_options, player_names)

        # Dieser Aufruf startet den Spielfluss (und damit auch den Zug der KI)
        self.game_instance.announce_current_player_turn()

        # Warten, bis das Spielfenster geschlossen wird
        self.root.wait_window(self.game_instance.ui.db.root)

        # --- Nach Beendigung des Matches ---

        # Trage den Gewinner ein und gehe zur nächsten Runde über
        if self.game_instance and self.game_instance.winner:
            winner_name = self.game_instance.winner.name
            self.tournament_manager.record_match_winner(match, winner_name)
            self.tournament_manager.advance_to_next_round()

        # Bereinige die beendete Spielinstanz
        self.game_instance = None

        # Zeige das Turnierfenster wieder an und aktualisiere es
        if self.tournament_view and self.tournament_view.winfo_exists():
            self.tournament_view.deiconify()
            self.tournament_view.update_bracket_tree()
            
            # --- Siegerehrung, wenn das Turnier beendet ist ---
            if self.tournament_manager.is_finished:
                winner = self.tournament_manager.get_tournament_winner()
                ui_utils.show_message(
                    'info',
                    "Turnier beendet!",
                    f"Herzlichen Glückwunsch, {winner}!\n\nDu hast das Turnier gewonnen!",
                    parent=self.tournament_view
                )

    def open_settings_dialog(self):
        """Öffnet einen Dialog für globale Anwendungseinstellungen."""
        dialog = AppSettingsDialog(self.root, self.settings_manager, self.sound_manager)
        self.root.wait_window(dialog)

    def open_profile_manager(self):
        """Öffnet den Dialog zur Verwaltung von Spielerprofilen."""
        dialog = ProfileManagerDialog(self.root, self.profile_manager)
        self.root.wait_window(dialog)

    def save_game(self):
        """Speichert den Zustand des aktuell laufenden Spiels."""
        # Spiel kann nur gespeichert werden, wenn eine Instanz existiert, das Spiel nicht beendet ist UND das Dartboard-Fenster (db) noch existiert.
        if self.game_instance and not self.game_instance.end and self.game_instance.ui and self.game_instance.ui.db:
            SaveLoadManager.save_game_state(self.game_instance, self.root)
        else:
            ui_utils.show_message('info', "Spiel speichern", "Es läuft kein aktives Spiel, das gespeichert werden könnte.", parent=self.root)

    def show_highscores(self):
        """Öffnet das Fenster zur Anzeige der Highscores."""
        if self.highscore_manager:
            self.highscore_manager.show_highscores_window(self.root)

    def show_player_stats(self):
        """Öffnet das Fenster zur Anzeige der Spielerstatistiken."""
        self.player_stats_manager.show_stats_window(self.root)

    def quit_game(self):
        """Beendet die Anwendung nach einer Bestätigungsabfrage."""
        confirm = ui_utils.ask_question('yesno', "Programm beenden", "DartCounter wirklich beenden?", parent=self.root)
        if confirm:
            if self.settings_manager:
                self.settings_manager.save_settings()
            # --- Zentrales Schließen der Datenbankverbindung ---
            if self.db_manager and self.db_manager.is_connected:
                self.db_manager.close_connection()
            if self.game_instance:
                self.game_instance.destroy() # Explizit die Ressourcen des Spiels freigeben
            self.root.quit()

    def about(self):
        """Zeigt ein "Über"-Dialogfenster mit Informationen zur Anwendung an."""
        about_text = (
            "Idee, Konzept und Code\n"
            "von Martin Hehl (airnooweeda)\n\n"
            "Ein besonderer Dank geht an Gemini Code Assist\n"
            "für die unschätzbare Hilfe bei der Entwicklung.\n\n"
            f"© 2025 Martin Hehl"
        )
        ui_utils.show_message('info', f"Dartcounter {self.version}", about_text, parent=self.root)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
    
