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
from typing import TYPE_CHECKING
from .ai_strategy import (
    AIStrategy,
    X01AIStrategy,
    CricketAIStrategy,
    KillerAIStrategy,
    ShanghaiAIStrategy,
    SplitScoreAIStrategy,
    AtcAIStrategy,
    DefaultAIStrategy,
)

if TYPE_CHECKING:
    from .game_view_manager import GameViewManager


class AIPlayer(Player):
    """
    Repräsentiert einen computergesteuerten KI-Gegner.
    Erbt von der Player-Klasse und wird in Zukunft die Logik für
    automatische Würfe enthalten.
    """

    # Definiert die Streuung für jeden Schwierigkeitsgrad.
    # Der Wert ist der maximale Radius (in Pixeln) vom Zielpunkt.
    DIFFICULTY_SETTINGS = {
        "Anfänger": {"radius": 150},
        "Fortgeschritten": {"radius": 60},
        "Amateur": {"radius": 40},
        "Profi": {"radius": 25},
        "Champion": {"radius": 10},
        # 'Adaptive' wird hier nicht benötigt, da es seine Daten aus dem Profil lädt.
    }

    # Das Strategy-Pattern in Aktion: Eine Map, die Spielmodi auf Strategie-Klassen abbildet.
    _strategy_map = {
        "301": X01AIStrategy,
        "501": X01AIStrategy,
        "701": X01AIStrategy,
        "Cricket": CricketAIStrategy,
        "Cut Throat": CricketAIStrategy,
        "Tactics": CricketAIStrategy,
        "Killer": KillerAIStrategy,
        "Shanghai": ShanghaiAIStrategy,
        "Split Score": SplitScoreAIStrategy,
        "Around the Clock": AtcAIStrategy,
    }

    def __init__(self, name, game, profile=None): # type: ignore
        super().__init__(name, game, profile)
        self.difficulty = profile.difficulty if profile else "Anfänger"

        # Streuungsradius aus den Schwierigkeits-Einstellungen laden
        difficulty_params = self.DIFFICULTY_SETTINGS.get(
            self.difficulty, self.DIFFICULTY_SETTINGS["Anfänger"]
        ) # type: ignore
        self.throw_radius = difficulty_params["radius"]

        # Die Wurfverzögerung wird jetzt vom GameViewManager geholt, da dieser die Settings kennt
        # und das Dartboard-Fenster verwaltet.
        self.throw_delay = 1000 # Fallback
        # Wurf-Verzögerung aus den globalen Einstellungen laden
        self.throw_delay = 1000  # Fallback-Wert
        if game.settings_manager:
            self.throw_delay = game.settings_manager.get("ai_throw_delay", 1000)

        # Wählt die passende Strategie aus der Map aus oder nimmt die Default-Strategie.
        strategy_class = self._strategy_map.get(game.options.name, DefaultAIStrategy)
        self.strategy: AIStrategy = strategy_class(self)

    def _apply_strategic_offset(self, center_coords: tuple[int, int], ring: str) -> tuple[int, int]:
        """
        Applies a small, strategic offset to the target coordinates to aim for
        the "safer" part of a segment (e.g., the inner part of a triple).

        Args:
            center_coords (tuple[int, int]): The geometric center of the target segment.
            ring (str): The ring being targeted (e.g., "Triple").

        Returns:
            tuple[int, int]: The new, strategically adjusted target coordinates.
        """
        if not center_coords or ring not in ("Triple", "Double"):
            return center_coords

        board_center_x = self.game.game_view_manager.dartboard.center_x or 0 # type: ignore
        board_center_y = self.game.game_view_manager.dartboard.center_y or 0 # type: ignore
        target_x, target_y = center_coords

        # Vector from board center to target center
        vec_x = target_x - board_center_x
        vec_y = target_y - board_center_y
        length = math.sqrt(vec_x**2 + vec_y**2) # type: ignore
        if length == 0:
            return center_coords

        # The "safe" direction is opposite to the vector (towards the board center)
        # The offset is a fraction of the ring's height, depending on AI skill.
        skaliert = self.game.game_view_manager.dartboard.skaliert if self.game.game_view_manager else {}
        ring_height = (skaliert or {}).get(f"{ring.lower()}_outer", 0) - (
            skaliert or {}).get(f"{ring.lower()}_inner", 0)
        offset_percentage = {
            "Champion": 0.35,
            "Profi": 0.3,
            "Amateur": 0.25,
            "Fortgeschritten": 0.2,
            "Anfänger": 0.1,
        }.get(self.difficulty, 0.1)
        offset_distance = ring_height * offset_percentage # type: ignore

        # Um den Zielpunkt in Richtung Board-Mitte zu verschieben, subtrahieren wir # type: ignore
        # einen Teil des Vektors, der vom Zentrum zum Ziel zeigt.
        return int(target_x - (vec_x / length) * offset_distance), int(
            target_y - (vec_y / length) * offset_distance
        )

    def _get_adaptive_throw_coords(
        self, target_coords: tuple[int, int], target_name: str
    ) -> tuple[int, int]:
        """
        Berechnet die Wurfkoordinaten basierend auf einem gelernten statistischen Modell
        (Bias und Streuung) eines menschlichen Spielers.

        Args:
            target_coords (tuple[int, int]): Die idealen Zielkoordinaten.
            target_name (str): Der Name des Ziels (z.B. "T20"), um das korrekte Modell zu laden.

        Returns:
            tuple[int, int]: Die simulierten Wurfkoordinaten.
        """
        # Lade das vollständige Genauigkeitsmodell aus dem Profil.
        accuracy_model = (self.profile.accuracy_model or {}) if self.profile else {}
        target_stats = accuracy_model.get(target_name)

        if target_stats:
            # Verwende die gelernten Werte für dieses spezifische Ziel
            mean_offset_x = target_stats.get("mean_offset_x", 0)
            mean_offset_y = target_stats.get("mean_offset_y", 0)
            std_dev_x = target_stats.get("std_dev_x", 20)
            std_dev_y = target_stats.get("std_dev_y", 20)
        else:
            # Fallback: Wenn für dieses Ziel kein Modell existiert,
            # verwende eine Standard-Streuung ohne Bias.
            mean_offset_x = 0
            mean_offset_y = 0
            std_dev_x = 20  # Entspricht ungefähr der "Profi"-Streuung
            std_dev_y = 20

        # Wende den gelernten Bias (durchschnittliche Abweichung) an
        biased_target_x, biased_target_y = (
            target_coords[0] + mean_offset_x,
            target_coords[1] + mean_offset_y,
        )

        # Erzeuge eine normalverteilte (realistischere) Streuung um das neue Ziel
        return int(random.gauss(biased_target_x, std_dev_x)), int(
            random.gauss(biased_target_y, std_dev_y)
        )

    def is_ai(self) -> bool:
        """Gibt an, dass es sich um einen KI-Spieler handelt."""
        return True

    def take_turn(self, game_view_manager: "GameViewManager"):
        """Startet den automatischen Zug der KI."""
        self.game.game_view_manager = game_view_manager # Sicherstellen, dass die Referenz gesetzt ist
        self.throw_delay = game_view_manager.get_dartboard_throw_delay()
        if game_view_manager.get_dartboard_root() and game_view_manager.get_dartboard_root().winfo_exists():
            game_view_manager.get_dartboard_root().after(self.throw_delay, self._execute_throw, 1)

    def _execute_throw(self, throw_number: int):
        """
        Führt einen einzelnen simulierten Wurf aus.
        Diese Methode wird rekursiv über `root.after` aufgerufen.
        """
        # --- Vorab-Prüfung, ob der Zug überhaupt stattfinden darf ---
        if self.game.end:
            # also die KI-Aktion abbrechen.
            return

        if self.turn_is_over:
            # Der Zug wurde vorzeitig beendet (z.B. Bust im vorherigen Wurf),
            # also direkt zum nächsten Spieler wechseln.
            if self.game.game_view_manager and self.game.game_view_manager.get_dartboard_root():
                self.game.game_view_manager.get_dartboard_root().after(self.throw_delay, self.game.next_player) # type: ignore
            return

        # --- Strategische Ziel-Logik ---
        ring, segment = self.strategy.get_target(throw_number)
        center_coords = (
            self.game.game_view_manager.get_dartboard_coords_for_target(ring, segment) # type: ignore
            if self.game.game_view_manager
            else (0, 0)
        )
        # Wende einen strategischen Offset an, um auf den "sicheren" Teil zu zielen
        target_coords = self._apply_strategic_offset(center_coords, ring)

        # Konstruiere den Ziel-Namen für die adaptive KI (z.B. "T20", "D18", "BE")
        target_name_map = {
            "Triple": "T",
            "Double": "D",
            "Single": "S",
            "Bullseye": "BE",
            "Bull": "B",
        }
        ring_prefix = target_name_map.get(ring, "S")
        target_name = ring_prefix if ring in ("Bullseye", "Bull") else f"{ring_prefix}{segment}"

        if target_coords:
            target_x, target_y = target_coords
        else:
            target_name = "BE"  # Ziele auf die Mitte
            target_x, target_y = (self.game.game_view_manager.dartboard.center_x or 0), ( # type: ignore
                self.game.game_view_manager.dartboard.center_y or 0 # type: ignore
            ) # type: ignore

        # --- Wurf-Simulation basierend auf Schwierigkeit (Standard vs. Adaptiv) ---
        if self.difficulty == "Adaptiv" and self.profile and self.profile.accuracy_model is not None:
            throw_x, throw_y = self._get_adaptive_throw_coords((target_x, target_y), target_name)
        else:
            # Standard-Logik mit kreisförmiger Streuung
            radius = self.throw_radius
            # Sonderregel für Killer: Das Lebensfeld wird mit der "schwachen" Hand ermittelt.
            # Wir simulieren das, indem wir für diesen einen Wurf
            # immer die Anfänger-Genauigkeit verwenden.
            if self.game.options.name == "Killer" and not self.state.get("life_segment"):
                radius = self.DIFFICULTY_SETTINGS["Anfänger"]["radius"]

            # Erzeugt eine zufällige Abweichung innerhalb eines Kreises um das Ziel
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(0, radius)
            offset_x = dist * math.cos(angle)
            offset_y = dist * math.sin(angle)

            throw_x = int(target_x + offset_x)
            throw_y = int(target_y + offset_y)

        # --- Wurf an die Game-Logik übergeben, indem ein Klick simuliert wird ---
        if self.game.game_view_manager:
            # Nutze root.after mit Verzögerung 0, um die Klick-Simulation in die
            # Event-Queue einzureihen. Dies stellt sicher, dass die UI reagiert.
            self.game.game_view_manager.get_dartboard_root().after(
                0, self.game.game_view_manager.dartboard.simulate_click, throw_x, throw_y
            )

        # --- Prüfung nach dem Wurf ---
        if self.game.end:
            # Das Spiel wurde durch diesen Wurf beendet. Die `Game.throw`-Methode
            # zeigt die Siegesnachricht an. Die KI beendet hier ihre Aktionen. Der Benutzer
            # interagiert mit der Nachricht und schließt das Spiel manuell.
            return

        # --- Nächsten Wurf planen oder Zug beenden ---
        if throw_number < 3:
            # Planen des nächsten Wurfs nach der Verzögerung
            if self.game.game_view_manager.get_dartboard_root() and self.game.game_view_manager.get_dartboard_root().winfo_exists(): # type: ignore
                self.game.game_view_manager.get_dartboard_root().after( # type: ignore
                    self.throw_delay, self._execute_throw, throw_number + 1 # type: ignore
                )
        else:
            # Nach dem dritten Wurf den Zug an den nächsten Spieler übergeben
            if self.game.game_view_manager.get_dartboard_root() and self.game.game_view_manager.get_dartboard_root().winfo_exists(): # type: ignore
                self.game.game_view_manager.get_dartboard_root().after(self.throw_delay, self.game.next_player) # type: ignore
