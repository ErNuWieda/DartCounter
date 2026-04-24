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

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from . import ui_utils
from .dartboard import DartBoard
from .scoreboard import setup_scoreboards
from .save_load_manager import SaveLoadManager
from .throw_result import ThrowResult

if TYPE_CHECKING:
    from .game_controller import GameController
    from .player import Player
    from .game_options import GameOptions
    from .sound_manager import SoundManager
    from .settings_manager import SettingsManager
    from .announcer import Announcer


class GameViewManager:
    """
    Verwaltet die gesamte Benutzeroberfläche für eine aktive Spielsitzung.
    Diese Klasse ist für die Darstellung des Dartboards, der Scoreboards
    und die Anzeige von Nachrichten zuständig. Sie empfängt Anweisungen
    vom GameController und leitet Benutzereingaben (Klicks) an diesen weiter.
    """

    root: tk.Tk
    game_controller: "GameController"
    game_options: "GameOptions"
    players: list["Player"]
    sound_manager: "SoundManager"
    settings_manager: "SettingsManager"
    is_tournament_match: bool
    on_game_end_callback: callable
    dartboard: DartBoard | None
    scoreboards: list
    announcer: "Announcer" | None

    def __init__(
        self,
        root: tk.Tk,
        game_controller: "GameController",
        game_options: "GameOptions",
        players: list["Player"],
        sound_manager: "SoundManager",
        settings_manager: "SettingsManager",
        is_tournament_match: bool,
        on_game_end_callback: callable,
        announcer: "Announcer" | None = None,
    ):
        """
        Initialisiert den GameViewManager.

        Args:
            root (tk.Tk): Das Hauptfenster der Anwendung, das als Parent dient.
            game_controller (GameController): Die Instanz des GameControllers, mit dem interagiert wird.
            game_options (GameOptions): Die Spieloptionen für die aktuelle Sitzung.
            players (list[Player]): Eine Liste der Spieler, die am Spiel teilnehmen.
            sound_manager (SoundManager): Die Instanz des SoundManagers für Audio-Feedback.
            settings_manager (SettingsManager): Die Instanz des SettingsManagers für App-Einstellungen.
            is_tournament_match (bool): True, wenn das Spiel Teil eines Turniers ist.
            on_game_end_callback (callable): Ein Callback, der aufgerufen wird, wenn das Spiel-Fenster
                                             geschlossen wird.
        """
        self.root = root
        self.game_controller = game_controller
        self.game_options = game_options
        self.players = players
        self.sound_manager = sound_manager
        self.settings_manager = settings_manager
        self.is_tournament_match = is_tournament_match
        self.on_game_end_callback = on_game_end_callback
        self.announcer = announcer

        self.dartboard: DartBoard | None = None
        self.scoreboards = []

        self._setup_game_window()

    def _setup_game_window(self):
        """
        Erstellt das Hauptfenster für das Spiel (Dartboard und Scoreboards).
        """
        self.dartboard = DartBoard(self, self.root)
        self.scoreboards = setup_scoreboards(self)

    def destroy(self) -> None:
        """Zerstört alle UI-Elemente, die zu diesem Spiel gehören, sicher."""
        # Zerstört das Dartboard-Fenster, was automatisch alle untergeordneten
        # Scoreboard-Fenster schließt.
        if self.dartboard and self.dartboard.root and self.dartboard.root.winfo_exists():
            self.dartboard.root.destroy()
        self.dartboard = None
        self.scoreboards = []
        self.on_game_end_callback() # Informiere die App, dass das Spiel beendet ist

    def quit_game(self):
        """
        Zeigt einen Dialog mit den Optionen Speichern, Beenden oder Abbrechen.
        Nutzt die zentrale `ask_question'-Methode der ui_utils.
        """
        if self.game_controller.end:
            self.destroy()
            return

        if self.is_tournament_match:
            ui_utils.show_message(
                "warning",
                "Laufendes Turnierspiel",
                "Ein Turnierspiel muss beendet werden.\n\n" "Bitte spiele das Match zu Ende.",
                parent=self.root,
            )
            return

        response = ui_utils.ask_question(
            "yesnocancel",
            "Spiel beenden",
            "Möchtest du den aktuellen Spielstand speichern, bevor du beendest?",
            "no",
        )

        if response is None:
            return

        if response is True:
            was_saved = SaveLoadManager.save_state(self.game_controller, self.root)
            if not was_saved:
                return

        self.destroy()

    def update_ui_for_new_turn(self, player: "Player", game_round: int):
        """
        Aktualisiert alle UI-Komponenten, um den Beginn eines neuen Zugs widerzuspiegeln.

        Args:
            player (Player): Der Spieler, der aktuell am Zug ist.
            game_round (int): Die aktuelle Spielrunde.
        """

        if not player:
            return

        if self.dartboard:
            dart_color = player.profile.dart_color if player.profile else "#ff0000"
            self.dartboard.update_dart_image(dart_color)
            self.dartboard.clear_dart_images_from_canvas()
            self.dartboard.update_button_states(player, self.game_controller.end)

        # Sprachansage für den neuen Spieler
        if self.announcer:
            self.announcer.announce_player_turn(player.name)

        for p in self.players:
            if p.sb and hasattr(p.sb, "set_active"):
                is_active = p.id == player.id
                p.sb.set_active(is_active)
                if is_active and p.sb.score_window.winfo_exists():
                    # Speziell für Split Score: Aktualisiere das Rundenziel auf dem Scoreboard
                    if self.game_options.name == "Split Score" and hasattr(p.sb, "update_target_display"):
                        round_index = game_round - 1
                        if 0 <= round_index < len(self.game_controller.game.targets):
                            p.sb.update_target_display(self.game_controller.game.targets[round_index])
                    # Hebe das Scoreboard des aktiven Spielers hervor und bringe es in den Vordergrund.
                    p.sb.score_window.lift()
                    p.sb.score_window.focus_force()

    def display_turn_start_message(self, player: "Player", game_round: int, message_data: tuple | None):
        """
        Zeigt eine Nachricht am Zugbeginn an.

        Args:
            player (Player): Der Spieler, der aktuell am Zug ist.
            game_round (int): Die aktuelle Spielrunde.
            message_data (tuple | None): Ein Tupel (msg_type, title, message) für eine
                                         spielspezifische Nachricht, oder None.
        """
        if self.dartboard:
            if self.game_controller.current == 0 and game_round == 1 and not player.throws:
                ui_utils.show_message("info", "Spielstart", f"{player.name} beginnt!", parent=self.dartboard.root)
            if message_data:
                msg_type, title, message = message_data
                ui_utils.show_message(msg_type, title, message, parent=self.dartboard.root)

    def display_throw_feedback(self, result: ThrowResult, player: "Player", auto_close_ms: int) -> None:
        """
        Zeigt Feedback für einen Wurf an (Sound, Nachrichten).

        Args:
            result (ThrowResult): Das Ergebnisobjekt des Wurfs.
            player (Player): Der Spieler, der den Wurf ausgeführt hat.
            auto_close_ms (int): Zeit in Millisekunden, nach der sich eine Nachricht automatisch schließt (für KI).
        """
        if result.sound and self.sound_manager:
            sound_method = getattr(self.sound_manager, f"play_{result.sound}", None)
            if sound_method and callable(sound_method):
                sound_method()

        # Sprachansage für das Wurfergebnis
        if self.announcer:
            if result.status == "win":
                self.announcer.announce_game_shot(player.name)
            elif result.status == "bust":
                self.announcer.announce_bust()
            elif result.status == "ok":
                # Den Score des letzten Wurfs ansagen
                if player.throws:
                    ring, segment, _ = player.throws[-1]
                    score_val = self.game_controller.get_score(ring, segment)
                    self.announcer.announce_score(score_val)

        if result.message and self.dartboard:
            ui_utils.show_message_for_throw_result(result, self.dartboard.root, auto_close_for_ai_after_ms=auto_close_ms)

    def update_button_states(self, player: "Player", game_ended: bool):
        """
        Aktualisiert den Zustand der Buttons auf dem Dartboard.

        Args:
            player (Player): Der Spieler, der aktuell am Zug ist.
            game_ended (bool): True, wenn das Spiel beendet ist.
        """
        if self.dartboard:
            self.dartboard.update_button_states(player, game_ended)

    def clear_dart_images(self) -> None:
        """
        Entfernt alle Dart-Bilder vom Canvas.
        """
        if self.dartboard:
            self.dartboard.clear_dart_images_from_canvas()

    def clear_last_dart_image(self) -> None:
        """
        Entfernt das letzte Dart-Bild vom Canvas.
        Wird von der Undo-Funktion verwendet.
        """
        if self.dartboard:
            self.dartboard.clear_last_dart_image_from_canvas()

    def display_dart_on_canvas(self, x: int, y: int) -> None:
        """
        Zeigt ein Dart-Bild auf dem Canvas an den angegebenen Koordinaten an.

        Args:
            x (int): Die x-Koordinate des Dart-Bildes.
            y (int): Die y-Koordinate des Dart-Bildes.
        """
        if self.dartboard:
            self.dartboard.display_dart_on_canvas(x, y)

    def get_dartboard_coords_for_target(self, ring: str, segment: int) -> tuple[int, int] | None:
        """
        Fragt das Dartboard nach den Koordinaten eines Ziels.
        Wird von der KI-Logik verwendet, um Ziele anzuvisieren.

        Args:
            ring (str): Der Zielring (z.B. "Triple", "Double", "Bullseye").
            segment (int): Das Zielsegment (z.B. 20 für T20).

        Returns:
            tuple[int, int] or None: Ein (x, y)-Tupel der Zielkoordinaten oder None,
                                     wenn das Ziel ungültig ist.
        """
        if self.dartboard:
            return self.dartboard.get_coords_for_target(ring, segment)
        return None

    def get_dartboard_ring_segment(self, x: int, y: int) -> tuple[str, int]:
        """
        Fragt das Dartboard nach Ring und Segment für gegebene Koordinaten.

        Args:
            x (int): Die x-Koordinate des Klicks.
            y (int): Die y-Koordinate des Klicks.
        Returns:
            tuple[str, int]: Ein Tupel aus Ring-Name und Segment-Wert.
        """
        if self.dartboard:
            return self.dartboard.get_ring_segment(x, y)
        return "Miss", 0

    def get_dartboard_canvas_size(self) -> tuple[int, int]:
        """Gibt die Größe des Dartboard-Canvas zurück."""
        if self.dartboard and self.dartboard.canvas:
            return self.dartboard.canvas.winfo_width(), self.dartboard.canvas.winfo_height()
        return 1, 1  # Fallback, um Division durch Null zu vermeiden

    def get_dartboard_root(self) -> tk.Toplevel | None:
        """
        Gibt das Root-Fenster des Dartboards zurück.

        Returns:
            tk.Toplevel | None: Das Toplevel-Fenster des Dartboards oder None, wenn nicht vorhanden.
        """
        if self.dartboard:
            return self.dartboard.root
        return None

    def get_dartboard_throw_delay(self) -> int:
        """
        Gibt die Wurfverzögerung des Dartboards zurück.

        Returns:
            int: Die Wurfverzögerung in Millisekunden.
        """
        if self.dartboard:
            return self.dartboard.throw_delay
        return 1000 # Fallback