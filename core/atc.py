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
Dieses Modul definiert die Hauptlogik für verschiedene Dartspiele.
Es enthält die Game-Klasse, die den Spielablauf, die Spieler,
Punktestände und Regeln verwaltet.
"""
from .game_logic_base import GameLogicBase

ATC_TARGET_VALUES = {
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "11": 11,
    "12": 12,
    "13": 13,
    "14": 14,
    "15": 15,
    "16": 16,
    "17": 17,
    "18": 18,
    "19": 19,
    "20": 20,
    "Bull": 25,
}

ATC_SEGMENTS_AS_STR = [str(s) for s in range(1, 21)]  # "1" bis "20"


class AtC(GameLogicBase):
    def __init__(self, game):
        super().__init__(game)
        self.opt_atc = game.options.opt_atc
        self.targets = [k for k in ATC_TARGET_VALUES.keys()]

    def initialize_player_state(self, player):
        """
        Setzt den Anfangs-Score auf 0, initialisiert die Treffer-Map und das erste Ziel.
        """
        player.score = 0
        if self.targets:
            player.next_target = self.targets[0]
            for target in self.targets:
                player.hits[target] = 0

    def _handle_throw_undo(self, player, ring, segment, players):
        """Macht einen Wurf im ATC-Modus rückgängig."""
        # Da _handle_throw nur gültige Treffer durchlässt, können wir annehmen,
        # dass der rückgängig gemachte Wurf ein gültiger Treffer war.
        target_hit = None
        if ring in ("Bull", "Bullseye"):
            target_hit = "Bull"
        elif str(segment) in self.targets:
            target_hit = str(segment)

        if target_hit:
            # Treffer zurücksetzen
            player.hits[target_hit] = 0

            # Nächstes Ziel neu bestimmen, indem wir das erste unvollständige Ziel suchen
            for target in self.targets:
                if player.hits.get(target, 0) == 0:
                    player.next_target = target
                    break

        # Anzeige aktualisieren
        player.sb.update_display(player.hits, player.score)

    def _handle_throw(self, player, ring, segment, players):
        """
        Verarbeitet einen Wurf im "Around the Clock" (ATC) Modus.
        Prüft, ob das korrekte Ziel getroffen wurde, aktualisiert den Fortschritt
        und prüft auf Gewinnbedingungen.

        Args:
            player (Player): Der Spieler, der den Wurf ausgeführt hat.
            ring (str): Der getroffene Ring.
            segment (int/str): Das getroffene Segment.

        Returns:
            str or None: Eine Nachricht über den Spielausgang oder den Wurf, oder None.
        """
        # Determine if the throw is valid for the current target
        is_valid_hit = False
        current_target_is_bull_type = player.next_target == "Bull"

        if current_target_is_bull_type:
            if ring in ("Bull", "Bullseye"):
                is_valid_hit = True
        else:  # Target is a number segment
            if str(segment) == player.next_target:  # Correct number segment
                if self.opt_atc == "Single":  # Any hit on the correct number is valid
                    is_valid_hit = True
                elif self.opt_atc == "Double" and ring == "Double":
                    is_valid_hit = True
                elif self.opt_atc == "Triple" and ring == "Triple":
                    is_valid_hit = True

        if not is_valid_hit:
            player.sb.update_score(player.score)  # Update display for throw history

            opt_atc_display = ""
            if not current_target_is_bull_type and self.opt_atc != "Single":
                opt_atc_display = self.opt_atc + " "

            base_msg = f"{player.name} muss {opt_atc_display}{player.next_target} treffen!"

            remaining_darts = 3 - len(player.throws)
            if remaining_darts > 0:
                return (
                    "invalid_target",
                    base_msg + f"\nNoch {remaining_darts} verbleibende Darts.",
                )
            else:  # Last dart of the turn
                return (
                    "invalid_target", base_msg + "\nLetzter Dart dieser Aufnahme. Bitte 'Weiter' klicken."
                )

        # --- Treffer auf AtC-Ziel verarbeiten ---
        player.hits[player.next_target] = 1

        # Nächstes Ziel bestimmen oder Gewinnbedingung prüfen
        all_targets_closed = True
        for target in self.targets:
            hit = player.hits.get(target, 0)
            if hit == 0:
                all_targets_closed = False
                player.next_target = target
                break

        player.sb.update_display(player.hits, player.score)  # Update display after successful hit

        # --- Gewinnbedingung prüfen ---
        if all_targets_closed:
            self.game.end = True
            total_darts = player.get_total_darts_in_game()
            return (
                "win",
                f"🏆 {player.name} gewinnt {self.game.options.name} in Runde {self.game.round} mit {total_darts} Darts!",
            )

        # --- Weiter / Nächster Spieler ---
        if len(player.throws) == 3:
            # Turn ends
            return ("ok", None)

        return ("ok", None)  # Throw processed, turn continues
