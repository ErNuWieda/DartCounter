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
from .checkout_calculator import CheckoutCalculator, CHECKOUT_PATHS

class AIPlayer(Player):
    """
    Repräsentiert einen computergesteuerten KI-Gegner.
    Erbt von der Player-Klasse und wird in Zukunft die Logik für
    automatische Würfe enthalten.
    """
    # Definiert die Streuung für jeden Schwierigkeitsgrad.
    # Der Wert ist der maximale Radius (in Pixeln) vom Zielpunkt.
    DIFFICULTY_SETTINGS = {
        'Anfänger':       {'radius': 150, 'delay': 800}, # Easiest
        'Fortgeschritten':{'radius': 60,  'delay': 800},
        'Amateur':        {'radius': 40,  'delay': 800}, # Between Fortgeschritten and Profi
        'Profi':          {'radius': 25,  'delay': 800},
        'Champion':       {'radius': 10,  'delay': 800}  # Hardest
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
        self.game.ui.db.root.after(self.settings['delay'], self._execute_throw, 1)

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

    def _get_setup_throw(self, score: int, darts_left: int) -> tuple[str, int]:
        """
        Berechnet den besten Setup-Wurf, wenn kein direkter Checkout verfügbar ist.
        Die Logik priorisiert das Hinterlassen eines idealen Rests für die nächste Runde.
        Diese Methode wird typischerweise für Scores <= 100 aufgerufen.

        Args:
            score (int): Der aktuelle Punktestand.
            darts_left (int): Die Anzahl der verbleibenden Darts in dieser Runde.

        Returns:
            tuple[str, int]: Ein Tupel aus (Ring, Segment) für das beste Setup-Ziel.
        """
        # Ideale Restpunktzahlen, geordnet nach Präferenz (D20, D16, D18, etc.)
        IDEAL_LEAVES = [40, 32, 36, 50, 24, 16, 8, 4, 2]

        # --- Strategie 1: Versuche, einen idealen Rest durch einen SINGLE-Wurf zu erreichen ---
        # Dies ist die sicherste und häufigste Setup-Strategie.
        for leave in IDEAL_LEAVES:
            score_to_hit = score - leave
            # Können wir diesen Score mit einem einzelnen Dart treffen (1-20 oder 25)?
            if 1 <= score_to_hit <= 20:
                return "Single", score_to_hit
            if score_to_hit == 25:
                return "Bull", 25

        # --- Strategie 2: Wenn kein idealer Rest funktioniert, versuche, irgendeinen geraden Rest zu hinterlassen ---
        # Dies ist der Fallback für ungünstige Punktestände.
        # Wir versuchen, das höchstmögliche Single zu treffen, das ein Doppel übrig lässt.
        for s in range(20, 0, -1):
            # Der Rest muss mindestens 2 sein (für D1) und gerade.
            if score - s >= 2 and (score - s) % 2 == 0:
                return "Single", s

        # Absoluter Notfall-Fallback (sollte praktisch nie erreicht werden)
        return "Single", 1

    def _get_strategic_target(self, throw_number: int) -> tuple[str, int]:
        """
        Ermittelt das beste strategische Ziel basierend auf dem Spielmodus und -stand.
        """
        game_name = self.game.name

        if game_name in ("301", "501", "701"):
            score = self.score
            darts_left = 4 - throw_number

            # 1. Prüfen, ob ein direkter Checkout-Pfad existiert
            checkout_path_str = CheckoutCalculator.get_checkout_suggestion(score, self.game.opt_out, darts_left)
            if checkout_path_str and checkout_path_str != "-":
                targets = checkout_path_str.split(', ')
                current_target_str = targets[0]
                return self._parse_target_string(current_target_str)
            
            # 2. Kein direkter Checkout. Unterscheide zwischen Power-Scoring und Setup-Wurf.
            # Wenn der Score hoch ist (z.B. > 100), wird auf maximale Punkte gezielt.
            # Darunter wird ein intelligenter Setup-Wurf versucht.
            if score > 100:
                return "Triple", 20

            # 3. Score ist in einem Bereich, wo ein Setup-Wurf sinnvoll ist.
            return self._get_setup_throw(score, darts_left)

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
            self.game.ui.db.root.after(self.settings['delay'], self.game.next_player)
            return

        # --- Strategische Ziel-Logik ---
        ring, segment = self._get_strategic_target(throw_number)
        target_coords = self.game.ui.db.get_coords_for_target(ring, segment)

        if target_coords:
            target_x, target_y = target_coords
        else:
            # Fallback, wenn kein Ziel gefunden wurde (sollte nicht passieren)
            target_x, target_y = self.game.ui.db.center_x, self.game.ui.db.center_y

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
        self.game.ui.db.on_click_simulated(throw_x, throw_y)

        # WICHTIG: Erneut prüfen, ob der gerade simulierte Wurf zu einem Bust oder Spielende geführt hat.
        # Dies verhindert, dass die KI nach einem Bust weiterwirft.
        if self.game.end or self.turn_is_over:
            self.game.ui.db.root.after(self.settings['delay'], self.game.next_player)
            return

        # --- Nächsten Wurf planen oder Zug beenden ---
        if throw_number < 3:
            # Planen des nächsten Wurfs nach der Verzögerung
            self.game.ui.db.root.after(self.settings['delay'], self._execute_throw, throw_number + 1)
        else:
            # Nach dem dritten Wurf den Zug an den nächsten Spieler übergeben
            self.game.ui.db.root.after(self.settings['delay'], self.game.next_player)
