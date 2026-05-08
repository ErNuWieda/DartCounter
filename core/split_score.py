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

from .game_logic_base import GameLogicBase
from .throw_result import ThrowResult


class SplitScore(GameLogicBase):
    """
    Implements the game logic for the "Split Score" training game.
    The goal is to have the highest score after 7 rounds.
    """

    def __init__(self, game_controller):
        super().__init__(game_controller)
        # KORREKTUR: Die Optionen sind über self.game.options verfügbar, nicht direkt über self.options.
        # Die Basisklasse GameLogicBase stellt nur self.game bereit.
        self.start_score = int(getattr(self.game.options, "opt_split_score_target", 60))
        # Feste Zielsequenz für das Spiel
        self.targets = [
            ("Single", 15),
            ("Single", 16),
            ("Double", 17),
            ("Double", 18),
            ("Triple", 19),
            ("Triple", 20),
            ("Bullseye", 50),
        ]

    def initialize_player_state(self, player):
        """Initialisiert den Spieler mit dem Start-Score."""
        player.score = self.start_score
        # State für robustes Undo initialisieren
        player.state['halved_in_round'] = None

    def get_targets(self) -> list[str]:
        """Gibt keine festen Ziele für das Scoreboard zurück, da es rundenbasiert ist."""
        return []

    def get_scoreboard_height(self) -> int:
        """Gibt die Standardhöhe für das Scoreboard zurück."""
        return 300

    def get_turn_start_message(self, player) -> tuple | None:
        """Zeigt das Ziel für die aktuelle Runde an."""
        round_index = self.game.round - 1
        if 0 <= round_index < len(self.targets):
            target_ring, target_segment = self.targets[round_index]
            return ("info", f"Runde {self.game.round}", f"Ziel: {target_ring} {target_segment}")
        return None

    def _handle_throw_undo(self, player, ring, segment, players):
        """Macht die Punkteaddition oder die Halbierung rückgängig."""
        # 1. War dieser Wurf der Auslöser für eine Halbierung? (Wird über den State geprüft)
        if player.state.get('halved_in_round') == self.game.round:
            # Da wir die Halbierung rückgängig machen, stellen wir den Score vor der Halbierung wieder her.
            if 'score_before_halving' in player.state:
                player.score = player.state['score_before_halving']
                player.state['halved_in_round'] = None

        # 2. War es ein Treffer? Dann ziehen wir die addierten Punkte wieder ab.
        round_index = self.game.round - 1
        target_ring, target_segment = self.targets[round_index]
        if ring == target_ring and segment == target_segment:
            player.score -= self.game.get_score(ring, segment)

        player.sb.update_score(player.score)

    def _handle_throw(self, player, ring, segment, players):
        """Verarbeitet einen Wurf. Bei Treffern werden Punkte sofort addiert."""
        round_index = self.game.round - 1
        target_ring, target_segment = self.targets[round_index]

        if ring == target_ring and segment == target_segment:
            player.score += self.game.get_score(ring, segment)

        player.sb.update_score(player.score)
        return ("ok", None)  # Der Haupt-Score wird erst am Ende der Runde aktualisiert

    def handle_end_of_turn(self, player):
        """Wird am Ende einer Runde aufgerufen, um den Score zu berechnen."""
        round_index = self.game.round - 1
        if not (0 <= round_index < len(self.targets)):
            return

        target_ring, target_segment = self.targets[round_index]

        # Prüfen, ob das Ziel in dieser Runde getroffen wurde
        hit_in_round = any(r == target_ring and s == target_segment for r, s, _ in player.throws)

        if not hit_in_round and player.throws:
            # Score speichern für Undo, dann halbieren und aufrunden
            player.state['score_before_halving'] = player.score
            player.score = (player.score + 1) // 2
            player.state['halved_in_round'] = self.game.round

        player.sb.update_score(player.score)
        
        # Prüfen, ob das Spiel nach der Runde des letzten Spielers beendet ist
        is_last_player_of_round = self.game.current == len(self.game.players) - 1
        if self.game.round >= 7 and is_last_player_of_round:
            self.game.end = True
            # Der Gewinner ist der Spieler mit den meisten verbleibenden Punkten
            self.game.winner = max(self.game.players, key=lambda p: p.score)
            message = (
                f"🏆 {self.game.winner.name} gewinnt Split Score mit {self.game.winner.score} Punkten!"
            )
            # KORREKTUR: Der Callback muss explizit aufgerufen werden, um die UI (z.B. Sound)
            # über den Spielgewinn zu informieren.
            self.on_throw_processed_callback(
                ThrowResult(status="win", message=message, sound="win"), self.game.winner
            )