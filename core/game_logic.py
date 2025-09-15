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


class GameLogic:
    """
    Abstrakte Basisklasse für alle spezifischen Spiellogiken (z.B. X01, Cricket).
    Definiert die Schnittstelle, die jede Spiellogik implementieren muss.
    """

    def __init__(self, game_controller):
        self.game = game_controller
        self.on_throw_processed_callback = game_controller.on_throw_processed

    @property
    def players(self):
        """Greift dynamisch auf die Spielerliste des Game-Controllers zu."""
        return self.game.players

    @property
    def options(self):
        """Greift dynamisch auf die Spieloptionen des Game-Controllers zu."""
        return self.game.options

    def get_targets(self) -> list:
        """Gibt eine Liste der relevanten Ziele für das Spiel zurück."""
        return []

    def initialize_player_state(self, player):
        """Initialisiert den spielspezifischen Zustand für einen Spieler."""
        pass

    def _handle_throw(self, player, ring, segment, players):
        """Verarbeitet einen einzelnen Wurf."""
        raise NotImplementedError

    def _handle_throw_undo(self, player, ring, segment, players):
        """Macht die Logik eines Wurfs rückgängig."""
        pass

    def get_turn_start_message(self, player) -> tuple | None:
        """Gibt eine optionale Nachricht zurück, die zu Beginn eines Zugs angezeigt wird."""
        return None

    def get_scoreboard_height(self) -> int:
        """Gibt die Standardhöhe für ein Scoreboard zurück."""
        return 240
