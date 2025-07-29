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
Dieses Modul enthält die AIPlayer-Klasse, die einen computergesteuerten Gegner repräsentiert.
"""
import random
import math
from .player import Player
from .checkout_calculator import CheckoutCalculator

class AIPlayer(Player):
    """
    Repräsentiert einen computergesteuerten KI-Gegner.
    Erbt von der Player-Klasse und wird in Zukunft die Logik für
    automatische Würfe enthalten.
    """
    # Definiert die Streuung für jeden Schwierigkeitsgrad.
    # Der Wert ist der maximale Radius (in Pixeln) vom Zielpunkt.
    DIFFICULTY_SETTINGS = {
        'Anfänger': {'radius': 150, 'delay': 1000},
        'Fortgeschritten': {'radius': 60, 'delay': 600},
        'Profi': {'radius': 25, 'delay': 300}
    }

    def __init__(self, name, game, profile=None):
        super().__init__(name, game, profile)
        self.difficulty = profile.difficulty if profile else 'Anfänger'
        self.settings = self.DIFFICULTY_SETTINGS.get(self.difficulty, self.DIFFICULTY_SETTINGS['Anfänger'])

    def is_ai(self) -> bool:
        """
        Gibt an, dass es sich um einen KI-Spieler handelt.
        Überschreibt die Methode der Basisklasse.
        """
        return True

    def take_turn(self):
        """
        Startet den automatischen Zug der KI.
        Die Würfe werden nacheinander mit einer Verzögerung ausgeführt.
        """
        # Der erste Wurf wird nach einer kurzen initialen Verzögerung ausgeführt.
        self.game.db.root.after(self.settings['delay'], self._execute_throw, 1)

    def _parse_target_string(self, target_str: str) -> tuple[str, int]:
        """
        Parst einen Ziel-String (z.B. "T20", "D18", "S5", "BULL") in ein (Ring, Segment)-Tupel.
        """
        target_str = target_str.strip().upper()
        if target_str == "BULL" or target_str == "BULLSEYE":
            return "Bullseye", 50

        ring_map = {'T': "Triple", 'D': "Double", 'S': "Single"}
        
        ring_char = target_str[0]
        if ring_char in ring_map:
            try:
                segment = int(target_str[1:])
                return ring_map[ring_char], segment
            except (ValueError, IndexError):
                pass
        
        # Fallback für Strings, die nur eine Zahl sind (z.B. "20" -> S20)
        try:
            segment = int(target_str)
            return "Single", segment
        except ValueError:
            pass

        # Finaler Fallback, wenn nichts passt
        return "Triple", 20

    def _get_strategic_target(self, throw_number: int) -> tuple[str, int]:
        """
        Ermittelt das beste strategische Ziel basierend auf dem Spielmodus und -stand.
        Berücksichtigt jetzt den Wurf innerhalb der Runde für Checkout-Pfade.

        Args:
            throw_number (int): Die Nummer des Wurfs in der aktuellen Runde (1, 2 oder 3).

        Returns:
            tuple[str, int]: Ein Tupel aus (Ring, Segment), z.B. ("Triple", 20).
        """
        game_name = self.game.name

        if game_name in ("301", "501", "701"):
            score = self.score
            darts_left = 4 - throw_number # 1. Wurf -> 3 Darts, 2. Wurf -> 2, 3. Wurf -> 1

            # Checkout-Pfad nur im Finish-Bereich suchen (<= 170)
            if score <= 170:
                checkout_path_str = CheckoutCalculator.get_checkout_suggestion(score, self.game.opt_out, darts_left)

                if checkout_path_str and "Kein Finish" not in checkout_path_str:
                    # Wir haben einen gültigen Checkout-Pfad, z.B. "T20, T19, D12"
                    targets = checkout_path_str.split(', ')
                    # Das erste Element des Pfades ist immer das nächste Ziel für den aktuellen Zustand
                    current_target_str = targets[0]
                    return self._parse_target_string(current_target_str)

            # Kein Checkout-Pfad verfügbar oder Score zu hoch: Standardstrategie -> T20
            return "Triple", 20

        elif game_name in ("Cricket", "Cut Throat", "Tactics"):
            # Finde das wertvollste, noch nicht geschlossene Ziel.
            targets = self.game.game.get_targets() # z.B. ['20', '19', ..., 'Bull']
            for target in targets:
                if self.state['hits'].get(target, 0) < 3:
                    # Ziel ist noch nicht geschlossen, darauf zielen.
                    # Wir zielen auf das Triple, da es die meisten Punkte/Marks gibt.
                    if target == "Bull":
                        return "Bullseye", 50 # Bullseye zählt als 2 Marks
                    else:
                        return "Triple", int(target)

            # Alle eigenen Ziele sind zu. Jetzt auf die der Gegner punkten.
            # Finde ein Ziel, das wir zu haben, aber ein Gegner noch nicht.
            for target in targets:
                is_open_for_scoring = any(opp != self and opp.state['hits'].get(target, 0) < 3 for opp in self.game.players)
                if is_open_for_scoring:
                    if target == "Bull": return "Bullseye", 50
                    else: return "Triple", int(target)

        # Fallback für andere Spielmodi oder wenn keine Strategie zutrifft: Mitte anvisieren.
        return "Bullseye", 50

    def _execute_throw(self, throw_number):
        """
        Führt einen einzelnen simulierten Wurf aus.
        Diese Methode wird rekursiv über `root.after` aufgerufen.
        """
        if self.game.end or self.turn_is_over:
            # Wenn das Spiel während der KI-Würfe beendet wurde oder der Zug
            # durch einen Bust vorzeitig beendet wurde, wird der Zug beendet.
            self.game.db.root.after(self.settings['delay'], self.game.next_player)
            return

        # --- Strategische Ziel-Logik ---
        ring, segment = self._get_strategic_target(throw_number)
        target_coords = self.game.db.get_coords_for_target(ring, segment)

        if target_coords:
            target_x, target_y = target_coords
        else:
            # Fallback, wenn kein Ziel gefunden wurde (sollte nicht passieren)
            target_x, target_y = self.game.db.center_x, self.game.db.center_y

        # --- Wurf-Simulation basierend auf Schwierigkeit ---
        radius = self.settings['radius']
        # Erzeugt eine zufällige Abweichung innerhalb eines Kreises um das Ziel
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0, radius)
        offset_x = dist * math.cos(angle)
        offset_y = dist * math.sin(angle)

        throw_x = int(target_x + offset_x)
        throw_y = int(target_y + offset_y)

        # --- Wurf an die Game-Logik übergeben, indem ein Klick simuliert wird ---
        self.game.db.on_click_simulated(throw_x, throw_y)

        # --- Nächsten Wurf planen oder Zug beenden ---
        if throw_number < 3:
            # Planen des nächsten Wurfs nach der Verzögerung
            self.game.db.root.after(self.settings['delay'], self._execute_throw, throw_number + 1)
        else:
            # Nach dem dritten Wurf den Zug an den nächsten Spieler übergeben
            self.game.db.root.after(self.settings['delay'], self.game.next_player)
