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
Dieses Modul implementiert das Strategy-Pattern für die KI-Zielauswahl.
Jede Klasse repräsentiert eine spezifische Strategie für einen Spielmodus.
"""
import random
from .checkout_calculator import CheckoutCalculator


class AIStrategy:
    """Basisklasse für alle KI-Strategien."""

    def __init__(self, ai_player):
        self.ai_player = ai_player
        self.game = ai_player.game

    def get_target(self, throw_number: int) -> tuple[str, int]:
        """Gibt das Ziel als (Ring, Segment)-Tupel zurück."""
        raise NotImplementedError("Diese Methode muss in der Unterklasse implementiert werden.")

    def _parse_target_string(self, target_str: str) -> tuple[str, int]:
        """Hilfsmethode zum Parsen von Ziel-Strings (z.B. "T20")."""
        target_str = target_str.strip().upper()
        if target_str in ("BULLSEYE", "BE"):
            return "Bullseye", 50
        if target_str == "BULL":
            return "Bull", 25
        ring_map = {"T": "Triple", "D": "Double", "S": "Single"}
        ring_char = target_str[0]
        if ring_char in ring_map:
            try:
                return ring_map[ring_char], int(target_str[1:])
            except (ValueError, IndexError):
                pass
        try:
            return "Single", int(target_str)
        except ValueError:
            pass
        return "Triple", 20  # Fallback


class X01AIStrategy(AIStrategy):
    """Strategie für X01-Spiele."""

    # Bogey-Nummern: Scores, die nicht mit 3 Darts gefinished werden können,
    # plus die "2", da D1 ein sehr ungünstiges Finish ist.
    BOGEY_NUMBERS = {169, 168, 166, 165, 163, 162, 159, 2}

    def get_target(self, throw_number: int) -> tuple[str, int]:
        score = self.ai_player.score
        darts_left = 4 - throw_number
        preferred_double = (
            self.ai_player.profile.preferred_double if self.ai_player.profile else None
        )

        # --- Phase 1: Power-Scoring (wenn Score zu hoch für ein Finish ist) ---
        # Ein Profi versucht nicht, von 300 ein Finish aufzubauen, sondern punktet maximal, um in den Finish-Bereich zu kommen.
        if score > 170:
            return "Triple", 20

        # --- Phase 2: Direkter Checkout (wenn ein Finish mit den verbleibenden Darts möglich ist) ---
        checkout_path_str = CheckoutCalculator.get_checkout_suggestion(
            score,
            self.game.options.opt_out,
            darts_left,
            preferred_double=preferred_double,
        )
        if checkout_path_str and checkout_path_str != "-":
            targets = checkout_path_str.split(", ")
            target = self._parse_target_string(targets[0])
            return target

        # --- Phase 3: Intelligentes Setup (wenn kein direkter Checkout möglich ist) ---

        # Fall A: Setup für DIESE Runde (wenn noch mehr als 1 Dart übrig ist)
        if darts_left > 1:
            all_possible_throws = [
                ("Triple", 20),
                ("Triple", 19),
                ("Bullseye", 50),
                ("Triple", 18),
                ("Triple", 16),
                ("Triple", 15),
                ("Triple", 17),
            ] + [("Single", s) for s in range(20, 0, -1)]

            # Versuche, ein Finish für die verbleibenden Darts zu hinterlassen
            for ring, segment in all_possible_throws:
                throw_value = self.game.get_score(ring, segment)
                if score - throw_value < 2:
                    continue

                remainder = score - throw_value
                if (
                    CheckoutCalculator.get_checkout_suggestion(
                        remainder, self.game.options.opt_out, darts_left - 1
                    )
                    != "-"
                ):
                    # Vermeide es, D1 zu hinterlassen, wenn es nicht der letzte Dart ist
                    if (
                        (darts_left - 1) > 0
                        and remainder == 2
                        and self.game.options.opt_out == "Double"
                    ):
                        continue
                    return ring, segment

        # Fall B: Setup für die NÄCHSTE Runde (letzter Dart oder kein Setup für diese Runde gefunden)
        # Ziel: Eine "gute" gerade Zahl hinterlassen. Geworfen wird auf sichere Single-Felder.
        safe_targets = [
            20,
            19,
            18,
            17,
            16,
            15,
            14,
            13,
            12,
            11,
            10,
            9,
            8,
            7,
            6,
            5,
            4,
            3,
            2,
            1,
        ]

        for segment_value in safe_targets:
            if score - segment_value >= 2:
                if (score - segment_value) % 2 == 0:
                    return "Single", segment_value

        for segment_value in safe_targets:
            if score - segment_value >= 2:
                return "Single", segment_value

        # Absoluter Notfall-Fallback (sollte nie passieren, wenn score >= 2 ist)
        return "Single", 1


class CricketAIStrategy(AIStrategy):
    """Strategie für Cricket-Spiele."""

    def get_target(self, throw_number: int) -> tuple[str, int]:
        targets = self.game.game.get_targets()
        opponents = [p for p in self.game.players if p != self.ai_player]

        # 1. Defensive: Gegnerische Punkt-Ziele schließen
        dangerous_targets = [
            t
            for t in targets
            if self.ai_player.hits.get(t, 0) < 3
            and any(opp.hits.get(t, 0) >= 3 for opp in opponents)
        ]
        if dangerous_targets:
            target = dangerous_targets[0]
            return ("Bullseye", 50) if target == "Bull" else ("Triple", int(target))

        # 2. Offensive: Eigene Ziele schließen
        for target in targets:
            if self.ai_player.hits.get(target, 0) < 3:
                return ("Bullseye", 50) if target == "Bull" else ("Triple", int(target))

        # 3. Punkte-Phase: Auf offenen Zielen punkten
        for target in targets:
            if any(opp.hits.get(target, 0) < 3 for opp in opponents):
                return ("Bullseye", 50) if target == "Bull" else ("Triple", int(target))

        return "Bullseye", 50  # Fallback


class KillerAIStrategy(AIStrategy):
    """Strategie für Killer."""

    def get_target(self, throw_number: int) -> tuple[str, int]:
        player_state = self.ai_player.state

        # Phase 1: Lebensfeld bestimmen
        if not player_state.get("life_segment"):
            taken = {
                p.state.get("life_segment")
                for p in self.game.players
                if p != self.ai_player and p.state.get("life_segment")
            }
            preferred = [str(i) for i in range(20, 14, -1)] + ["Bull"]
            for target in preferred:
                if target not in taken:
                    # KORREKTUR: "Bull" muss als ("Bull", 25) zurückgegeben werden,
                    # nicht als ("Single", 25), da dies von der Spiellogik erwartet wird.
                    return ("Bull", 25) if target == "Bull" else ("Single", int(target))
            return "Single", 1  # Fallback

        # Phase 2: Killer werden
        if not player_state.get("can_kill"):
            my_segment = player_state["life_segment"]
            return ("Bullseye", 50) if my_segment == "Bull" else ("Double", int(my_segment))

        # Phase 3: Als Killer agieren
        opponents = [p for p in self.game.players if p != self.ai_player and p.score > 0]
        if not opponents:
            return "Bullseye", 50  # Keine Gegner mehr

        # Priorisiere Gegner, die ebenfalls Killer sind.
        killer_opponents = [p for p in opponents if p.state.get("can_kill")]

        if killer_opponents:
            # Unter den Killern, greife den mit den meisten Leben an.
            victim = max(killer_opponents, key=lambda p: p.score)
        else:
            # Wenn es keine anderen Killer gibt, greife den Spieler mit den meisten Leben an.
            victim = max(opponents, key=lambda p: p.score)

        victim_segment = victim.state.get("life_segment")
        if not victim_segment:
            # Fallback, falls ein Gegner aus irgendeinem Grund kein Lebensfeld hat
            return "Bullseye", 50

        return ("Bullseye", 50) if victim_segment == "Bull" else ("Double", int(victim_segment))


class ShanghaiAIStrategy(AIStrategy):
    """Strategie für Shanghai."""

    def get_target(self, throw_number: int) -> tuple[str, int]:
        """
        Zielt immer auf das Ziel der aktuellen Runde.
        Priorisiert das Triple, um den Score zu maximieren.
        """
        target_segment = self.game.round
        if 1 <= target_segment <= 20:
            return "Triple", target_segment

        # Fallback, falls die Runde außerhalb des normalen Bereichs liegt (sollte nicht passieren)
        return "Bullseye", 50


class DefaultAIStrategy(AIStrategy):
    """Fallback-Strategie, die immer auf das Bullseye zielt."""

    def get_target(self, throw_number: int) -> tuple[str, int]:
        return "Bullseye", 50
