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
import webbrowser
from PIL import Image, ImageTk
import sys
import sv_ttk
from core.settings_manager import SettingsManager
from core.logger_setup import setup_logging
import pathlib
from core.game_options import GameOptions
from core.game_settings_dialog import GameSettingsDialog
from core.game_controller import GameController
from core.game_view_manager import GameViewManager
from core.sound_manager import SoundManager
from core.announcer import Announcer
from core.player_stats_manager import PlayerStatsManager
from core.highscore_manager import HighscoreManager
from core.database_manager import DatabaseManager
from core.save_load_manager import SaveLoadManager
from core.player_profile_manager import PlayerProfileManager
from core.profile_manager_dialog import ProfileManagerDialog
from core.settings_dialog import AppSettingsDialog
from core.tournament_dialog import TournamentSettingsDialog
from core.app_menu import AppMenu
from core.tournament_view import TournamentView
from core.tournament_manager import TournamentManager
from core import ui_utils
from core.throw_result import ThrowResult


def get_asset_path(relative_path):
    """
    Gibt den korrekten Pfad zu einer Asset-Datei zurück, egal ob das Skript
    als normale .py-Datei oder als gepackte Anwendung (PyInstaller) läuft.
    """
    if hasattr(sys, "_MEIPASS"):
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
        # Logging als Allererstes einrichten, um alle nachfolgenden Meldungen zu erfassen.
        setup_logging()

        self.root = root
        self.version = f"v{__version__}"

        # Manager-Instanzen als Instanzvariablen
        self.settings_manager = SettingsManager()
        self.sound_manager = SoundManager(self.settings_manager, self.root)
        self.announcer = Announcer(self.settings_manager)

        # --- Dependency Injection für DatabaseManager ---
        # Einmal erstellen und an die abhängigen Manager weitergeben, um doppelte
        # Verbindungen und Log-Ausgaben zu vermeiden.
        self.db_manager = DatabaseManager()

        self.highscore_manager = HighscoreManager(self.db_manager)
        self.player_stats_manager = PlayerStatsManager(self.db_manager)
        self.profile_manager = PlayerProfileManager(self.db_manager)
        self.save_load_manager = SaveLoadManager() # SaveLoadManager benötigt keine DB-Referenz mehr
        self.game_instance = None
        self.tournament_manager = None
        self.tournament_view = None

        # UI-Setup
        self._setup_window()
        self._setup_menu()
        self._setup_main_canvas()

    def _setup_window(self):
        # Theme anwenden (NACH dem Erstellen des root-Fensters, aber VOR dem Rest)
        theme = self.settings_manager.get("theme", "light")
        sv_ttk.set_theme(theme)

        self.root.geometry("300x300")
        self.root.title(f"Dartcounter {self.version}")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_game)
        self.root.bind("<Escape>", lambda e: self.quit_game())

    def _setup_menu(self):
        self.menu = AppMenu(self.root, self, self.db_manager.is_connected)

    def _setup_main_canvas(self):
        assets_base_dir = get_asset_path("assets")
        image_path = assets_base_dir / "darthead.png"
        try:
            image = Image.open(image_path)
        except FileNotFoundError:
            ui_utils.show_message(
                "error",
                "Fehler",
                f"Image nicht gefunden: {image_path}",
                parent=self.root,
            )
            self.root.quit()
            return
        except Exception as e:
            ui_utils.show_message(
                "error",
                "Fehler",
                f"Fehler beim Laden des Images: {e}",
                parent=self.root,
            )
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

    def _ensure_no_active_session(self, title: str, message: str) -> bool:
        """
        Prüft, ob ein Spiel oder Turnier läuft, fragt den Benutzer und beendet es ggf.
        Gibt True zurück, wenn fortgefahren werden kann, sonst False.
        """
        activity_running = (self.game_instance and not self.game_instance.end) or (
            self.tournament_manager and not self.tournament_manager.is_finished()
        )

        if activity_running:
            if not ui_utils.ask_question("yesno", title, message, parent=self.root):
                return False  # User cancelled

            # Close any active game session
            if self.game_instance and self.game_instance.game_view_manager:
                self.game_instance.game_view_manager.destroy()
                self.game_instance = None
            
            # Close any active tournament session
            if self.tournament_manager:
                if self.tournament_view and self.tournament_view.winfo_exists():
                    self.tournament_view.destroy()
                self.tournament_manager = None
                self.tournament_view = None
        return True

    def _on_game_end(self):
        """
        Callback, der vom GameViewManager aufgerufen wird, wenn das Spiel-Fenster
        geschlossen wird. Dies signalisiert der App, dass das Hauptfenster
        wieder sichtbar gemacht werden kann.
        """
        self.root.deiconify()

    def _on_throw_processed_by_controller(self, result: ThrowResult, player):
        """
        Callback-Funktion, die vom GameController aufgerufen wird, um die App
        über das Ergebnis eines Wurfs zu informieren (z.B. für globale Sounds).
        Die UI-spezifischen Feedbacks werden vom GameViewManager direkt behandelt.
        """
        # Hier könnten globale Sounds oder andere App-weite Logik ausgelöst werden.
        # Aktuell ist die Sound-Logik in GameViewManager verschoben.
        pass

    def _initialize_game_session(
        self, game_options, player_names, is_tournament_match=False
    ):
        """
        Erstellt die GameController- und GameViewManager-Instanzen
        und verbindet sie miteinander.
        """
        # Zuerst den GameController erstellen (ohne UI-Referenzen)
        game_controller = GameController(
            root=self.root,
            game_options=game_options,
            player_names=player_names,
            on_throw_processed_callback=self._on_throw_processed_by_controller,
            highscore_manager=self.highscore_manager,
            player_stats_manager=self.player_stats_manager,
            profile_manager=self.profile_manager,
            settings_manager=self.settings_manager,
            is_tournament_match=is_tournament_match,
        )

        # Dann den GameViewManager erstellen und den Controller übergeben
        game_view_manager = GameViewManager(
            root=self.root,
            game_controller=game_controller,
            game_options=game_options,
            players=game_controller.players,
            sound_manager=self.sound_manager,
            settings_manager=self.settings_manager,
            is_tournament_match=is_tournament_match,
            on_game_end_callback=self._on_game_end,
            announcer=self.announcer,
        )

        # Den ViewManager dem Controller bekannt machen
        game_controller.game_view_manager = game_view_manager

        # Die Scoreboards werden jetzt vom GameViewManager erstellt und dem Controller bekannt gemacht
        # damit die Spieler-Objekte ihre Scoreboard-Referenz erhalten.
        game_controller.scoreboards = game_view_manager.scoreboards
        for p_idx, player in enumerate(game_controller.players):
            player.sb = game_controller.scoreboards[p_idx]

        return game_controller

    def _start_game_workflow(self, game_data: dict, is_loaded_game: bool = False):
        """
        Zentraler Workflow zum Starten einer neuen oder geladenen Spielsitzung.
        Kapselt die UI-Flow-Logik (Fenster ausblenden/anzeigen) und die Spielinitialisierung.
        """
        self.root.withdraw()

        game_options = GameOptions.from_dict(game_data)
        # Bei einem geladenen Spiel sind die Spielerdaten verschachtelt, bei einem neuen Spiel nicht.
        player_names = (
            [p["name"] for p in game_data["players"]]
            if is_loaded_game
            else game_data.pop("players")
        )

        game_instance = self._initialize_game_session(game_options, player_names)

        if is_loaded_game:
            self.save_load_manager.restore_game_state(game_instance, game_data)

        self.game_instance = game_instance
        self.game_instance.announce_current_player_turn()

        # Warten, bis das Spielfenster geschlossen wird, bevor das Hauptfenster wieder erscheint.
        self.root.wait_window(self.game_instance.dartboard.root)
        self.root.deiconify()

    def new_game(self):
        """Startet den Workflow zum Erstellen eines neuen Spiels."""
        if not self._ensure_no_active_session(
            "Neues Spiel",
            "Eine andere Aktivität läuft bereits. Möchtest du sie beenden und ein "
            "neues Spiel starten?",
        ):
            return

        self.root.withdraw()
        dialog = GameSettingsDialog(self.root, self.settings_manager, self.profile_manager)
        self.root.wait_window(dialog)

        if dialog.was_started and dialog.result:
            game_settings = dialog.result
            # Der Game-Konstruktor erwartet den Schlüssel 'name' statt 'game'.
            game_settings["name"] = game_settings.pop("game")
            self._start_game_workflow(game_settings, is_loaded_game=False)
        else:
            self.root.deiconify()

    def load_game(self):
        """Startet den Workflow zum Laden eines gespeicherten Spiels."""
        if not self._ensure_no_active_session(
            "Spiel laden",
            "Eine andere Aktivität läuft bereits. Möchtest du sie beenden und ein " "Spiel laden?",
        ):
            return

        data = self.save_load_manager.load_game_data(self.root)
        if data:
            self._start_game_workflow(data, is_loaded_game=True)

    def _start_tournament_workflow(self, tournament_manager: TournamentManager):
        """
        Zentraler Workflow zum Starten eines neuen oder geladenen Turniers.
        Setzt den Manager und erstellt die zugehörige UI-Ansicht.
        """
        self.tournament_manager = tournament_manager
        self.tournament_view = TournamentView(
            self.root, self.tournament_manager, self.start_next_tournament_match
        )

    def new_tournament(self):
        """Startet den Workflow zum Erstellen eines neuen Turniers."""
        if not self._ensure_no_active_session(
            "Neues Turnier",
            "Eine andere Aktivität läuft bereits. Möchtest du sie beenden und ein "
            "Turnier starten?",
        ):
            return

        dialog = TournamentSettingsDialog(self.root, self.profile_manager, self.settings_manager)
        self.root.wait_window(dialog)
        if not dialog.cancelled:
            tournament_manager = TournamentManager(
                player_names=dialog.player_names,
                game_mode=dialog.game_mode,
                system=dialog.tournament_system,
            )
            self._start_tournament_workflow(tournament_manager)

    def load_tournament(self):
        """Startet den Workflow zum Laden eines gespeicherten Turniers.""" # type: ignore
        if not self._ensure_no_active_session(
            "Turnier laden",
            "Eine andere Aktivität läuft bereits. Möchtest du sie beenden und ein "
            "Turnier laden?",
        ):
            return

        data = self.save_load_manager.load_tournament_data(self.root)
        if data:
            # Erstelle eine neue, leere Turnierinstanz mit den Metadaten aus der Speicherdatei.
            tournament_manager = TournamentManager(
                player_names=data["player_names"],
                game_mode=data["game_mode"],
                system=data.get("system", "Doppel-K.o."),
                shuffle=False,  # Wichtig: Beim Laden nicht erneut mischen!
            )
            # Stelle den detaillierten Zustand (Turnierbaum, Gewinner) wieder her.
            tournament_manager.restore_state(data)
            self._start_tournament_workflow(tournament_manager)

    def save_tournament(self):
        """Speichert den Zustand des aktuell laufenden Turniers."""
        if self.tournament_manager and not self.tournament_manager.is_finished():
            self.save_load_manager.save_state(self.tournament_manager, self.root)
        else:
            title = "Turnier speichern"
            message = "Es läuft kein aktives Turnier, das gespeichert werden könnte."
            ui_utils.show_message("info", title, message, parent=self.root)

    def _finalize_tournament_match(self, match):
        """Verarbeitet das Ergebnis eines beendeten Turniermatches."""
        # Trage den Gewinner ein und gehe zur nächsten Runde über
        if self.game_instance and self.game_instance.winner:
            winner_name = self.game_instance.winner.name
            self.tournament_manager.record_match_winner(match, winner_name)

        # Bereinige die beendete Spielinstanz
        self.game_instance = None

        # Zeige das Turnierfenster wieder an und aktualisiere es
        if self.tournament_view and self.tournament_view.winfo_exists():
            self.tournament_view.deiconify()
            self.tournament_view.update_bracket_tree()

    def start_next_tournament_match(self):
        """Wird von der TournamentView aufgerufen, um das nächste Match zu starten."""
        match = self.tournament_manager.get_next_match()

        if not match:
            # Sollte nicht passieren, wenn der Button geklickt wird, aber als Sicherheitsnetz.
            return

        # Verstecke das Turnierfenster, während ein Match läuft
        if self.tournament_view and self.tournament_view.winfo_exists():
            self.tournament_view.withdraw()

        # Hole die Spieloptionen direkt vom TournamentManager.
        game_options = self.tournament_manager.get_match_game_options()
        player_names = [match["player1"], match["player2"]]
        self.game_instance = self._initialize_game_session(
            game_options, player_names, is_tournament_match=True
        )

        # Dieser Aufruf startet den Spielfluss (und damit auch den Zug der KI)
        self.game_instance.announce_current_player_turn()

        # Warten, bis das Spielfenster geschlossen wird
        self.root.wait_window(self.game_instance.game_view_manager.get_dartboard_root()) # type: ignore

        # Delegiere die gesamte Nachbearbeitung an die neue Methode
        self._finalize_tournament_match(match)

    def open_settings_dialog(self):
        """Öffnet einen Dialog für globale Anwendungseinstellungen."""
        dialog = AppSettingsDialog(self.root, self.settings_manager, self.sound_manager, self.announcer)
        self.root.wait_window(dialog)

    def open_profile_manager(self):
        """Öffnet den Dialog zur Verwaltung von Spielerprofilen."""
        dialog = ProfileManagerDialog(self.root, self.profile_manager, self.player_stats_manager)
        self.root.wait_window(dialog)

    def save_game(self):
        """Speichert den Zustand des aktuell laufenden Spiels."""
        # Spiel kann nur gespeichert werden, wenn eine Instanz existiert, das Spiel nicht beendet ist UND das Dartboard noch existiert.
        if self.game_instance and not self.game_instance.end and self.game_instance.game_view_manager:
            self.save_load_manager.save_state(self.game_instance, self.root)
        else:  # pragma: no cover
            ui_utils.show_message(
                "info",
                "Spiel speichern",
                "Es läuft kein aktives Spiel, das gespeichert werden könnte.",
                parent=self.root,
            )

    def show_highscores(self):
        """Öffnet das Fenster zur Anzeige der Highscores."""
        if self.highscore_manager:
            self.highscore_manager.show_highscores_window(self.root)

    def show_player_stats(self):
        """Öffnet das Fenster zur Anzeige der Spielerstatistiken."""
        self.player_stats_manager.show_stats_window(self.root)

    def quit_game(self):
        """Beendet die Anwendung nach einer Bestätigungsabfrage."""
        confirm = ui_utils.ask_question(
            "yesno",
            "Programm beenden",
            "DartCounter wirklich beenden?",
            parent=self.root,
        )
        if confirm:
            if self.settings_manager:
                self.settings_manager.save_settings()
            # --- Zentrales Schließen der Datenbankverbindung ---
            if self.db_manager and self.db_manager.is_connected:
                self.db_manager.close_connection()
            if self.game_instance and self.game_instance.game_view_manager:
                self.game_instance.game_view_manager.destroy()  # Explizit die Ressourcen des Spiels freigeben
            self.root.quit()

    def about(self):
        """Zeigt ein "Über"-Dialogfenster mit Informationen zur Anwendung an."""
        about_text = (
            "Idee, Konzept und Code\n"
            "von Martin Hehl (airnooweeda)\n\n"
            "Ein besonderer Dank geht an Gemini Code Assist\n"
            "für die unschätzbare Hilfe bei der Entwicklung.\n\n"
            "© 2026 Martin Hehl"
        )
        ui_utils.show_message("info", f"Dartcounter {self.version}", about_text, parent=self.root)

    def open_donate_link(self):
        """Öffnet den Spenden-Link im Standard-Webbrowser des Benutzers."""
        # --- WICHTIG: Bitte diese URL durch deinen persönlichen Spenden-Link ersetzen ---
        DONATE_URL = "https://paypal.me/ernuwieda"

        title = "Browser wird geöffnet"
        message = (
            "Vielen Dank für deine Unterstützung!\n\n"
            "Dein Standard-Browser wird jetzt geöffnet, um die Spendenseite zu laden."
        )
        ui_utils.show_message("info", title, message, parent=self.root)
        try:
            webbrowser.open_new_tab(DONATE_URL)
        except Exception as e:
            ui_utils.show_message(
                "error",
                "Fehler",
                f"Der Browser konnte nicht geöffnet werden: {e}",
                parent=self.root,
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
