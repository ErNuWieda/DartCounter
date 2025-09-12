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
Dieses Modul definiert die Hauptlogik für das Spiel "Elimination".
Es enthält die Elimination-Klasse, die den Spielablauf und die Regeln verwaltet.
"""
from .game_logic_base import GameLogicBase


class Elimination(GameLogicBase):

    def __init__(self, game):
        super().__init__(game)
        self.count_to = game.options.count_to
        self.opt_out = game.options.opt_out
        # Ein transientes Protokoll, um Eliminierungen für die Undo-Funktion zu speichern.
        self.elimination_log = []
        # self.targets bleibt None aus der Basisklasse

    def initialize_player_state(self, player):
        """
        Setzt den Anfangs-Score für Elimination auf 0.
        """
        player.score = 0

    def get_scoreboard_height(self):
        """
        Gibt die spezifische, kleinere Höhe für Elimination-Scoreboards zurück.
        """
        return 240

    def get_targets(self):
        """
        Gibt die Zielliste zurück. Für Elimination gibt es keine festen Ziele.
        Gibt eine leere Liste zurück, um Kompatibilität zu gewährleisten.
        """
        return []

    def _handle_throw_undo(self, player, ring, segment, players):
        """Macht einen Wurf im Elimination-Modus rückgängig, inklusive Eliminierungen."""
        # 1. Prüfen, ob dieser Wurf eine Eliminierung ausgelöst hat.
        # Dies muss VOR der Korrektur des Werfer-Scores geschehen, da wir den
        # Zustand zum Zeitpunkt der Eliminierung benötigen.
        score_after_throw = player.score
        if self.elimination_log:
            last_elimination = self.elimination_log[-1]
            # Prüfen, ob die letzte Eliminierung vom aktuellen Spieler verursacht wurde
            # und sein aktueller Punktestand dem des Opfers vor der Eliminierung entspricht.
            if (
                last_elimination["thrower_id"] == player.id
                and last_elimination["victim_score_before"] == score_after_throw
            ):
                elimination_event = self.elimination_log.pop()

                # Finde das Opfer und stelle seinen Score wieder her
                victim = next(
                    (p for p in players if p.id == elimination_event["victim_id"]),
                    None,
                )
                if victim:
                    victim.score = elimination_event["victim_score_before"]
                    victim.sb.set_score_value(victim.score)

        # 2. Punktzahl des Werfers korrigieren
        score_to_undo = self.game.get_score(ring, segment)
        player.update_score_value(score_to_undo, subtract=True)

    def _handle_throw(self, player, ring, segment, players):
        score = self.game.get_score(ring, segment)
        result_event = ("ok", None)  # Standard-Rückgabewert

        new_score = player.score + score
        bust = False
        if new_score > self.count_to:
            bust = True  # Direkt überworfen
        elif (
            self.opt_out == "Double"
            and new_score == self.count_to
            and ring not in ("Double", "Bullseye")
        ):
            bust = True  # Gewinnwurf muss ein Double sein

        if bust:
            player.turn_is_over = True
            # The score will be as it was BEFORE this busting throw.
            player.sb.update_score(player.score)  # Update display
            result_event = (
                "bust",
                f"{player.name} hat überworfen!\nBitte 'Weiter' klicken.",
            )
        elif ring == "Miss":
            # Wurf war ein "Miss", aber kein Bust. Nur die Wurfhistorie aktualisieren.
            player.sb.update_score(player.score)
        else:
            # Gültiger Wurf
            player.update_score_value(score, subtract=False)

            # Prüfen, ob ein Gegner eliminiert wurde
            for opp in players:
                # Ein Gegner wird eliminiert, wenn sein Score mit dem des Werfers übereinstimmt
                # und der Score nicht 0 ist (man kann niemanden bei 0 eliminieren).
                if opp != player and player.score == opp.score and opp.score != 0:
                    # Protokolliere den Zustand des Opfers VOR der Eliminierung
                    self.elimination_log.append(
                        {
                            "thrower_id": player.id,
                            "victim_id": opp.id,
                            "victim_score_before": opp.score,
                        }
                    )

                    # Eliminiere das Opfer
                    opp.score = 0
                    opp.sb.set_score_value(opp.score)
                    result_event = (
                        "info",
                        f"{player.name} schickt {opp.name} zurück an den Start!",
                    )
                    break  # Es kann nur ein Gegner pro Wurf eliminiert werden

        if player.score == self.count_to:
            result_event = (
                "win",
                f"🏆 {player.name} gewinnt in Runde {self.game.round}!",
            )
            self.game.end = True

        return result_event
