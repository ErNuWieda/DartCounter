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
Dieses Modul definiert die Hauptlogik für das Spiel "Micky Maus".
"""
from .game_logic_base import GameLogicBase

# Micky Mouse Targets, Spielreihenfolge
MICKY_TARGET_VALUES = {
    "20": 20,
    "19": 19,
    "18": 18,
    "17": 17,
    "16": 16,
    "15": 15,
    "14": 14,
    "13": 13,
    "12": 12,
    "Bull": 25,
}
MICKY_TARGETS = list(MICKY_TARGET_VALUES.keys())

SEGMENTS_AS_STR = [str(s) for s in range(12, 21)]  # "12" bis "20"


class Micky(GameLogicBase):
    """
    Behandelt die spezifische Spiellogik für "Micky Maus".

    In diesem Spielmodus müssen die Spieler eine vordefinierte Sequenz von Zielen
    (20 bis 12, dann Bull) jeweils dreimal treffen. Es werden keine Punkte gezählt.
    Der erste Spieler, der alle Ziele schließt, gewinnt.
    """

    def __init__(self, game):
        super().__init__(game)
        self.targets = MICKY_TARGETS

    def initialize_player_state(self, player):
        """
        Setzt den Anfangs-Score auf 0, initialisiert die Treffer-Map und das erste Ziel.
        """
        player.score = 0
        if self.targets:
            player.next_target = self.targets[0]
            for target in self.targets:
                player.hits[target] = 0

    def get_targets(self):
        """Gibt die Liste der Ziele für den aktuellen Spielmodus zurück."""
        return self.targets

    def _get_target_and_marks(self, ring, segment):
        """
        Ermittelt das Ziel und die Anzahl der erzielten Marks für einen Wurf.
        Ein Double zählt als 2 Treffer, ein Triple als 3. Ein Bullseye zählt
        als 2 Treffer auf das Bull-Ziel.
        """
        if ring == "Miss":
            return None, 0

        # Bullseye und Bull als "Bull" Target behandeln
        if ring == "Bullseye":
            return "Bull", 2
        if ring == "Bull":
            return "Bull", 1

        segment_str = str(segment)
        if segment_str in SEGMENTS_AS_STR:
            return segment_str, {"Single": 1, "Double": 2, "Triple": 3}.get(ring, 0)

        return None, 0  # Kein Micky-Maus-relevantes Segment getroffen

    def _handle_throw_undo(self, player, ring, segment, players):
        """
        Macht den letzten Wurf für einen Spieler im Micky Maus-Modus rückgängig.

        Reduziert die Anzahl der Treffer auf dem Ziel des rückgängig gemachten
        Wurfs und setzt das `next_target` des Spielers auf das erste noch nicht
        geschlossene Ziel in der Sequenz.
        """
        target_hit, marks_scored = self._get_target_and_marks(ring, segment)

        if target_hit:
            current_hits = player.hits.get(target_hit, 0)
            player.hits[target_hit] = max(0, current_hits - marks_scored)

        # Nach dem Undo das nächste Ziel neu bestimmen
        next_unclosed_target = None
        for target in self.targets:
            if player.hits.get(target, 0) < 3:
                next_unclosed_target = target
                break

        if next_unclosed_target:
            player.next_target = next_unclosed_target
        else:
            # Alle Ziele sind (immer noch) geschlossen
            player.next_target = None

        player.sb.update_display(player.hits, player.score)

    def _handle_throw(self, player, ring, segment, players):
        """
        Verarbeitet einen Wurf im Micky Mouse-Modus.
        Aktualisiert die Treffer des Spielers und prüft auf Gewinnbedingungen.
        Der Spieler muss die Ziele in der vorgegebenen Reihenfolge treffen.

        Args:
            player (Player): Der Spieler, der den Wurf ausgeführt hat.
            ring (str): Der getroffene Ring.
            segment (int/str): Das getroffene Segment.
        """
        target_hit, marks_scored = self._get_target_and_marks(ring, segment)

        current_target = player.next_target

        # Prüfen, ob das korrekte Ziel getroffen wurde
        if not target_hit or target_hit != current_target:
            player.sb.update_score(player.score)  # Scoreboard aktualisieren (für Wurf-Historie)
            needed_hits = 3 - player.hits.get(current_target, 0)
            msg_base = f"{player.name} muss {current_target} noch {needed_hits}x treffen!"
            remaining_darts = 3 - len(player.throws)
            if remaining_darts > 0:
                return (
                    "invalid_target",
                    msg_base + f"\n{remaining_darts} verbleibende Darts.",
                )
            else:  # pragma: no cover
                return ("invalid_target", msg_base + "\nLetzter Dart dieser Aufnahme.")

        # Gültiger Treffer: Trefferzahl aktualisieren (maximal 3)
        current_hits = player.hits.get(current_target, 0)
        player.hits[current_target] = min(3, current_hits + marks_scored)

        # Prüfen, ob das aktuelle Ziel geschlossen wurde und zum nächsten wechseln
        if player.hits[current_target] >= 3:
            # Finde das nächste ungeschlossene Ziel
            next_unclosed_target = None
            for target in self.targets:
                if player.hits.get(target, 0) < 3:
                    next_unclosed_target = target
                    break

            if next_unclosed_target:
                player.next_target = next_unclosed_target
            else:
                # Alle Ziele sind geschlossen -> GEWINN
                self.game.end = True
                total_darts = player.get_total_darts_in_game()
                player.sb.update_display(player.hits, player.score)
                return (
                    "win",
                    f"🏆 {player.name} gewinnt {self.game.options.name} in Runde {self.game.round} mit {total_darts} Darts!",
                )

        # UI nach jedem gültigen Wurf aktualisieren
        player.sb.update_display(player.hits, player.score)

        # --- Weiter / Nächster Spieler ---
        if len(player.throws) == 3:
            # Turn ends
            return ("ok", None)
        return ("ok", None)  # Throw processed, turn continues
