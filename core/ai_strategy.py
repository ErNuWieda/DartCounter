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
        if target_str in ("BULLSEYE", "BE", "BULL"):
            return "Bullseye", 50
        if target_str == "B":
            return "Bullseye", 50
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

    # Bogey-Nummern: Scores, die nicht mit 3 Darts gefinished werden können.
    # Die "2" wurde entfernt, da D1 ein valides, wenn auch schwieriges, Finish ist
    # und die KI in der Lage sein muss, es zu versuchen.
    BOGEY_NUMBERS = {169, 168, 166, 165, 163, 162, 159}

    def _get_high_skill_target(self, score: int, darts_left: int) -> tuple[str, int] | None:
        """
        Prüft und wendet priorisierte Regeln für starke KI-Spieler an.
        Gibt ein Ziel zurück, wenn eine Regel zutrifft, sonst None.
        """
        is_high_skill = self.ai_player.difficulty in ("Profi", "Champion")
        if not (is_high_skill and self.game.game.opt_out == "Double"):
            return None

        # Regel 1: Aggressives 1-Dart-Finish bei geradem Score <= 40
        if score <= 40 and score % 2 == 0 and score != 2:
            return "Double", score // 2

        # Regel 2: Strategischer Bust, um ein Finish auf D1 zu vermeiden
        if score == 3 and darts_left > 1:
            return "Single", 20  # Wurf auf S20 führt zum Bust
        if score == 2 and darts_left > 1:
            return "Single", 2  # Wurf auf S2 führt zum Bust

        return None

    def _get_power_scoring_target(self, score: int, darts_left: int) -> tuple[str, int] | None:
        """
        Wählt ein Power-Scoring-Ziel, wenn der Score zu hoch für ein Finish ist.
        Gibt ein Ziel zurück, wenn Power-Scoring sinnvoll ist, sonst None.
        """
        if darts_left == 3 and score > 170:
            if self.ai_player.difficulty in ("Anfänger", "Fortgeschritten"):
                return "Single", 20
            return "Triple", 20
        return None

    def _get_direct_checkout_target(
        self, score: int, darts_left: int, preferred_double: int | None
    ) -> tuple[str, int] | None:
        """
        Versucht, einen direkten Checkout-Pfad zu finden.
        Gibt das erste Ziel des Pfades zurück oder None, wenn kein Pfad existiert.
        """
        checkout_path_str = CheckoutCalculator.get_checkout_suggestion(
            score, self.game.game.opt_out, darts_left, preferred_double=preferred_double
        )
        if checkout_path_str and checkout_path_str != "-":
            first_target_str = checkout_path_str.split(", ")[0]
            return self._parse_target_string(first_target_str)
        return None

    def _get_setup_target(self, score: int, darts_left: int) -> tuple[str, int]:
        """
        Bestimmt ein intelligentes Setup-Ziel, wenn kein direkter Checkout möglich ist.
        """
        # Fall A: Setup für DIESE Runde (wenn noch mehr als 1 Dart übrig ist)
        if darts_left > 1:
            all_possible_throws = [("Triple", s) for s in range(20, 0, -1)] + [
                ("Single", s) for s in range(20, 0, -1)
            ]
            for ring, segment in all_possible_throws:
                throw_value = self.game.get_score(ring, segment)
                if score - throw_value < 2:
                    continue

                remainder = score - throw_value
                if (
                    CheckoutCalculator.get_checkout_suggestion(
                        remainder, self.game.game.opt_out, darts_left - 1
                    )
                    != "-"
                ):
                    # Vermeide es, D1 zu hinterlassen, wenn es nicht der letzte Dart ist
                    if (
                        (darts_left - 1) > 0
                        and remainder == 2
                        and self.game.game.opt_out == "Double"
                    ):
                        continue
                    return ring, segment

        # Fall B: Setup für die NÄCHSTE Runde (letzter Dart or kein Setup in dieser Runde gefunden)
        # Ziel: Eine "gute" gerade Zahl hinterlassen. Geworfen wird auf sichere Single-Felder.
        safe_targets = list(range(20, 0, -1))

        # Priorisiere Würfe, die einen geraden Rest hinterlassen.
        for segment_value in safe_targets:
            if score - segment_value >= 2 and (score - segment_value) % 2 == 0:
                return "Single", segment_value

        # Fallback: Wenn kein Wurf einen geraden Rest hinterlässt,
        # nimm den höchsten möglichen Single-Wurf.
        for segment_value in safe_targets:
            if score - segment_value >= 2:
                return "Single", segment_value

        # Absoluter Notfall-Fallback (sollte nie passieren, wenn score >= 2 ist)
        return "Single", 1

    def get_target(self, throw_number: int) -> tuple[str, int]:
        """
        Bestimmt das strategische Ziel für einen Wurf in einem X01-Spiel.
        Diese Methode durchläuft mehrere Phasen, um das optimale Ziel zu finden.
        """
        score = self.ai_player.score
        darts_left = 4 - throw_number
        preferred_double = (
            self.ai_player.profile.preferred_double if self.ai_player.profile else None
        )

        # Phase 0: Priorisierte Regeln für starke KI-Spieler
        if target := self._get_high_skill_target(score, darts_left):
            return target

        # Phase 1: Power-Scoring bei sehr hohem Punktestand
        if target := self._get_power_scoring_target(score, darts_left):
            return target

        # Phase 2: Versuch eines direkten Checkouts
        if target := self._get_direct_checkout_target(score, darts_left, preferred_double):
            return target

        # Phase 3: Intelligentes Setup, wenn kein direkter Checkout möglich ist
        return self._get_setup_target(score, darts_left)


class CricketAIStrategy(AIStrategy):
    """Strategie für Cricket-Spiele."""

    def _get_defensive_target(self, targets: list[str], opponents: list) -> tuple[str, int] | None:
        """
        Sucht ein defensives Ziel: Schließe ein Ziel, auf dem ein Gegner punktet.
        Gibt das Ziel zurück oder None, wenn keine defensive Aktion nötig ist.
        """
        dangerous_targets = [
            t
            for t in targets
            if self.ai_player.hits.get(t, 0) < 3
            and any(opp.hits.get(t, 0) >= 3 for opp in opponents)
        ]
        if not dangerous_targets:
            return None

        target_segment = dangerous_targets[0]
        if target_segment == "Bull":
            return "Bullseye", 50

        ring = "Triple" if self.ai_player.difficulty in ("Profi", "Champion") else "Single"
        return ring, int(target_segment)

    def _get_offensive_target(self, targets: list[str]) -> tuple[str, int] | None:
        """
        Sucht ein offensives Ziel: Schließe das nächste eigene offene Ziel.
        Gibt das Ziel zurück oder None, wenn alle eigenen Ziele geschlossen sind.
        """
        for target in targets:
            if self.ai_player.hits.get(target, 0) < 3:
                if target == "Bull":
                    return "Bullseye", 50
                ring = "Triple" if self.ai_player.difficulty in ("Profi", "Champion") else "Single"
                return ring, int(target)
        return None

    def _get_scoring_target(self, targets: list[str], opponents: list) -> tuple[str, int] | None:
        """
        Sucht ein Ziel zum Punkten: Wirf auf ein eigenes geschlossenes Ziel,
        das bei einem Gegner noch offen ist.
        """
        for target in targets:
            if any(opp.hits.get(target, 0) < 3 for opp in opponents):
                if target == "Bull":
                    return "Bullseye", 50
                ring = "Triple" if self.ai_player.difficulty in ("Profi", "Champion") else "Single"
                return ring, int(target)
        return None

    def get_target(self, throw_number: int) -> tuple[str, int]:
        """Bestimmt das strategische Ziel für Cricket basierend auf einer Phasenlogik."""
        targets = self.game.game.get_targets()
        opponents = [p for p in self.game.players if p != self.ai_player]

        # Phase 1: Defensive - Verhindere, dass Gegner punkten.
        if target := self._get_defensive_target(targets, opponents):
            return target

        # Phase 2: Offensive - Schließe eigene Ziele.
        if target := self._get_offensive_target(targets):
            return target

        # Phase 3: Scoring - Erziele Punkte auf offenen Zielen.
        if target := self._get_scoring_target(targets, opponents):
            return target

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
                    # Korrektur: Um die Chance zu maximieren, das Bull-Segment zu treffen,
                    # sollte auf das Bullseye gezielt werden.
                    return ("Bullseye", 50) if target == "Bull" else ("Single", int(target))
            return "Single", 1  # Fallback

        # Phase 2: Killer werden
        if not player_state.get("can_kill"):
            my_segment = player_state["life_segment"]
            # Korrektur: Wenn das Lebensfeld "Bull" ist, ziele auf das größere Bullseye,
            # da sowohl Bull als auch Bullseye als Treffer zählen. Ansonsten wird versucht,
            # int("Bull") zu konvertieren, was fehlschlägt.
            if my_segment == "Bull":
                return "Bullseye", 50
            return "Double", int(my_segment)

        # Phase 3: Als Killer agieren
        opponents = [p for p in self.game.players if p != self.ai_player and p.score > 0]
        if not opponents:
            return "Bullseye", 50  # Keine Gegner mehr

        # Wenn keine Gegner mehr übrig sind, hat die KI gewonnen.
        if not opponents:
            return "Bullseye", 50  # Kein Ziel mehr nötig, Spiel ist vorbei.

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

        # Korrektur: Wenn das Ziel "Bull" ist, ziele auf das größere Bullseye,
        # da sowohl Bull als auch Bullseye als Treffer zählen.
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


class AtcAIStrategy(AIStrategy):
    """Strategie für Around the Clock."""

    def get_target(self, throw_number: int) -> tuple[str, int]:
        """
        Zielt immer auf das nächste erforderliche Segment in der Sequenz.
        Der erforderliche Ring (Single, Double, Triple) wird aus den Spieloptionen
        übernommen.
        """
        target_segment_str = self.ai_player.next_target
        if not target_segment_str:
            # Fallback, falls kein Ziel gesetzt ist (sollte nicht passieren)
            return "Bullseye", 50

        if target_segment_str == "Bull":
            return "Bullseye", 50

        try:
            target_segment = int(target_segment_str)
            required_ring = self.game.options.opt_atc
            return required_ring, target_segment
        except (ValueError, AttributeError):
            # Fallback bei unerwarteten Daten
            return "Bullseye", 50


class SplitScoreAIStrategy(AIStrategy):
    """Strategie für das Trainingsspiel Split Score."""

    def get_target(self, throw_number: int) -> tuple[str, int]:
        """
        Ermittelt das korrekte Ziel für die aktuelle Runde basierend auf der
        festgelegten Sequenz des Spiels.
        """
        round_index = self.game.round - 1
        targets = self.game.game.targets

        if 0 <= round_index < len(targets):
            return targets[round_index]

        return "Bullseye", 50  # Fallback


class DefaultAIStrategy(AIStrategy):
    """Fallback-Strategie, die immer auf das Bullseye zielt."""

    def get_target(self, throw_number: int) -> tuple[str, int]:
        return "Bullseye", 50
