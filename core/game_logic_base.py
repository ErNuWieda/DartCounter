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

"""
Defines the base class for all game logic handlers.
"""

class GameLogicBase:
    """
    Eine abstrakte Basisklasse für alle Spiellogik-Handler.

    Diese Klasse definiert eine gemeinsame Schnittstelle, die von allen spezifischen
    Spiellogik-Klassen (wie X01, Cricket, etc.) implementiert werden muss.
    Sie stellt sicher, dass die Haupt-`Game`-Klasse konsistent mit jeder
    Art von Spiellogik interagieren kann.
    """
    def __init__(self, game):
        """
        Initialisiert die Basis-Spiellogik.

        Args:
            game (Game): Die Haupt-Spielinstanz.
        """
        self.game = game
        self.targets = None

    def get_targets(self):
        """
        Gibt die Liste der Ziele für das Spiel zurück.
        Unterklassen sollten `self.targets` in ihrem `__init__` setzen.
        """
        return self.targets

    def initialize_player_state(self, player):
        """
        Initialisiert den spielspezifischen Zustand für einen Spieler.
        Wird von der Game-Klasse nach der Erstellung des Spielers aufgerufen.
        """
        pass # Standard-Implementierung tut nichts.

    def get_scoreboard_height(self):
        """
        Gibt die empfohlene Höhe für das Scoreboard dieses Spielmodus zurück.
        Die Standardimplementierung berechnet die Höhe basierend auf der Anzahl der Ziele.
        Kann von Unterklassen für spezielle Fälle (z.B. X01) überschrieben werden.
        """
        if self.targets:
            base_height = 240
            num_rows = (len(self.targets) + 1) // 2
            targets_height = 25 + num_rows * 32
            return base_height + targets_height

        # Fallback-Höhe, falls keine Ziele definiert sind und nichts überschrieben wurde.
        return 380

    def get_turn_start_message(self, player):
        """
        Gibt eine spielspezifische Nachricht zurück, die zu Beginn eines Zugs angezeigt wird.
        Gibt standardmäßig None zurück. Kann von Unterklassen überschrieben werden.
        """
        return None

    def _handle_throw(self, player, ring, segment, players):
        """
        Verarbeitet einen einzelnen Wurf. Muss von Unterklassen implementiert werden.
        """
        raise NotImplementedError("Die Methode '_handle_throw' muss in der Unterklasse implementiert werden.")

    def _handle_throw_undo(self, player, ring, segment, players):
        """
        Macht einen Wurf rückgängig. Muss von Unterklassen implementiert werden.
        """
        raise NotImplementedError("Die Methode '_handle_throw_undo' muss in der Unterklasse implementiert werden.")