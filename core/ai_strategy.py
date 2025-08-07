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
        if target_str in ("BULL", "BULLSEYE", "BE"): return "Bullseye", 50
        ring_map = {'T': "Triple", 'D': "Double", 'S': "Single"}
        ring_char = target_str[0]
        if ring_char in ring_map:
            try: return ring_map[ring_char], int(target_str[1:])
            except (ValueError, IndexError): pass
        try: return "Single", int(target_str)
        except ValueError: pass
        return "Triple", 20 # Fallback

class X01AIStrategy(AIStrategy):
    """Strategie für X01-Spiele."""
    
    # Bogey-Nummern: Scores, die nicht mit 3 Darts gefinished werden können,
    # plus die "2", da D1 ein sehr ungünstiges Finish ist.
    BOGEY_NUMBERS = {169, 168, 166, 165, 163, 162, 159, 2}

    def get_target(self, throw_number: int) -> tuple[str, int]:
        score = self.ai_player.score
        darts_left = 4 - throw_number
        preferred_double = self.ai_player.profile.preferred_double if self.ai_player.profile else None
        
        # 1. Direkten Checkout-Pfad suchen und verfolgen
        checkout_path_str = CheckoutCalculator.get_checkout_suggestion(
            score, self.game.options.opt_out, darts_left, preferred_double=preferred_double
        )
        if checkout_path_str and checkout_path_str != "-":
            targets = checkout_path_str.split(', ')
            return self._parse_target_string(targets[0])
        
        # 2. Wenn kein Checkout möglich ist: Power-Scoring mit Köpfchen
        #    Vermeide es, eine "Bogey"-Nummer zu hinterlassen.
        
        # Liste der bevorzugten Scoring-Würfe, von hoch nach niedrig
        power_throws = [
            # Die Reihenfolge spiegelt eine menschliche Strategie wider:
            # T20/T19 für die höchsten Punkte, dann das sichere Bullseye,
            # dann andere "gute" Triple. Die riskante T17 kommt zum Schluss.
            ("Triple", 20), 
            ("Triple", 19), 
            ("Bullseye", 50),
            ("Triple", 18), 
            ("Triple", 16), 
            ("Triple", 15), 
            ("Triple", 17)
        ]

        for ring, segment in power_throws:
            throw_value = self.game.get_score(ring, segment)
            
            # Prüfe, ob der Wurf zu einem Bust führen würde (Score < 2)
            if score - throw_value < 2:
                continue

            # Prüfe, ob der Rest eine Bogey-Nummer ist
            remainder = score - throw_value
            if remainder not in self.BOGEY_NUMBERS:
                # Dies ist ein sicherer, hochpunktender Wurf
                return ring, segment

        # 3. Fallback: Wenn alle Triple-Würfe zu einem Bogey führen,
        #    wirf auf das größte Single-Feld, das keinen Bust UND keinen Bogey verursacht.
        for segment in range(20, 0, -1):
            # Check for bust
            if score - segment < 2:
                continue
            # Check for bogey
            if (score - segment) not in self.BOGEY_NUMBERS:
                return "Single", segment

        # Absoluter Notfall-Fallback (sollte nie erreicht werden)
        return "Single", 1

class CricketAIStrategy(AIStrategy):
    """Strategie für Cricket-Spiele."""
    def get_target(self, throw_number: int) -> tuple[str, int]:
        targets = self.game.game.get_targets()
        opponents = [p for p in self.game.players if p != self.ai_player]

        # 1. Defensive: Gegnerische Punkt-Ziele schließen
        dangerous_targets = [
            t for t in targets 
            if self.ai_player.hits.get(t, 0) < 3 and any(opp.hits.get(t, 0) >= 3 for opp in opponents)
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

        return "Bullseye", 50 # Fallback

class KillerAIStrategy(AIStrategy):
    """Strategie für Killer."""
    def get_target(self, throw_number: int) -> tuple[str, int]:
        player_state = self.ai_player.state

        # Phase 1: Lebensfeld bestimmen
        if not player_state.get('life_segment'):
            taken = {p.state.get('life_segment') for p in self.game.players if p != self.ai_player and p.state.get('life_segment')}
            preferred = [str(i) for i in range(20, 14, -1)] + ["Bull"]
            for target in preferred:
                if target not in taken:
                    return "Single", int(target) if target != "Bull" else 25
            return "Single", 1 # Fallback

        # Phase 2: Killer werden
        if not player_state.get('can_kill'):
            my_segment = player_state['life_segment']
            return ("Bullseye", 50) if my_segment == "Bull" else ("Double", int(my_segment))

        # Phase 3: Als Killer agieren
        opponents = [p for p in self.game.players if p != self.ai_player and p.score > 0]
        if not opponents:
            return "Bullseye", 50 # Keine Gegner mehr

        victim = max(opponents, key=lambda p: p.score)
        victim_segment = victim.state.get('life_segment')
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
