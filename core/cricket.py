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
Dieses Modul definiert die Hauptlogik für Cricket und Cut Throat.
Es enthält die Cricket-Klasse, die den Spielablauf und Regeln der Cricket-Varianten verwaltet.
"""
from .game_logic_base import GameLogicBase

# Cricket, Cut Throat
CRICKET_TARGET_VALUES = {
    "20": 20,
    "19": 19,
    "18": 18,
    "17": 17,
    "16": 16,
    "15": 15,
    "Bull": 25,
}

CRICKET_SEGMENTS_AS_STR = [str(s) for s in range(15, 21)]  # "15" bis "20"

# Tactics Ziele
TACTICS_TARGET_VALUES = {
    "20": 20,
    "19": 19,
    "18": 18,
    "17": 17,
    "16": 16,
    "15": 15,
    "14": 14,
    "13": 13,
    "12": 12,
    "11": 11,
    "10": 10,
    "Bull": 25,
}
TACTICS_TARGETS = list(TACTICS_TARGET_VALUES.keys())

TACTICS_SEGMENTS_AS_STR = [str(s) for s in range(10, 21)]  # "10" bis "20"


class Cricket(GameLogicBase):
    """
    Behandelt die spezifische Spiellogik für Cricket und seine Varianten.

    Diese Klasse ist verantwortlich für die Logik der Spiele "Cricket",
    "Cut Throat Cricket" und "Tactics". Sie verwaltet:
    - Die Definition der relevanten Ziele für den jeweiligen Modus.
    - Die Verarbeitung von Würfen, um "Marks" auf den Zielen zu zählen.
    - Die unterschiedliche Punktevergabe:
        - "Cricket" / "Tactics": Punkte werden dem eigenen Score gutgeschrieben.
        - "Cut Throat": Punkte werden den Gegnern als "Straf-"Punkte zugewiesen.
    - Die Überprüfung der Gewinnbedingungen, die sowohl das Schließen aller
      Ziele als auch den Punktestand berücksichtigen.
    - Die Berechnung der "Marks Per Round" (MPR) für die Highscore-Liste.
    """

    def __init__(self, game):
        super().__init__(game)
        self.name = game.options.name
        self.CRICKET_TARGET_VALUES = CRICKET_TARGET_VALUES
        self.CRICKET_SEGMENTS_AS_STR = CRICKET_SEGMENTS_AS_STR

        if self.name == "Tactics":
            # Um unnötige if self.name == ... zu vermeiden werden hier die Werte überschrieben
            self.CRICKET_TARGET_VALUES = TACTICS_TARGET_VALUES
            self.CRICKET_SEGMENTS_AS_STR = TACTICS_SEGMENTS_AS_STR
        self.targets = [k for k in self.CRICKET_TARGET_VALUES.keys()]

    def initialize_player_state(self, player):
        """
        Setzt den Anfangs-Score auf 0 und initialisiert die Treffer-Map für Cricket.
        """
        player.state["hits"] = {}
        player.score = 0
        for target in self.get_targets():
            player.state["hits"][target] = 0

    def get_targets(self):
        """Gibt die Liste der Ziele für den aktuellen Spielmodus zurück."""
        return self.targets

    def _handle_throw_undo(self, player, ring, segment, players):
        """
        Macht den letzten Wurf für einen Spieler rückgängig.

        Diese Methode stellt den Zustand vor dem letzten Wurf wieder her. Sie
        ermittelt, wie viele "Marks" der Wurf wert war, reduziert die Treffer
        des Spielers auf dem entsprechenden Ziel und macht eventuell erzielte
        Punkte rückgängig.

        Args:
            player (Player): Der Spieler, dessen Wurf rückgängig gemacht wird.
            ring (str): Der Ring des rückgängig zu machenden Wurfs.
            segment (int): Das Segment des rückgängig zu machenden Wurfs.
            players (list[Player]): Die Liste aller Spieler, benötigt für die
                                   komplexe Logik der Punktevergabe bei
                                   Cut Throat.
        """
        target_hit, marks_scored = self._get_target_and_marks(ring, segment)
        if not target_hit:
            return  # Wurf war kein relevantes Ziel

        # 1. Statistik korrigieren
        if player.stats["total_marks_scored"] >= marks_scored:
            player.stats["total_marks_scored"] -= marks_scored

        # 2. Zustand VOR dem Wurf ermitteln
        marks_before_throw = player.state["hits"].get(target_hit, 0)

        # 3. Treffer rückgängig machen
        player.state["hits"][target_hit] = max(0, marks_before_throw - marks_scored)
        marks_after_undo = player.state["hits"][target_hit]

        # 4. Punkte rückgängig machen, falls welche erzielt wurden
        # Punkte wurden nur erzielt, wenn das Ziel schon vorher geschlossen war (>=3 Treffer)
        # und bei mindestens einem Gegner noch offen war.
        points_to_undo = 0
        # Wie viele der rückgängig gemachten Marks haben Punkte erzielt?
        scoring_marks_to_undo = max(0, marks_before_throw - max(3, marks_after_undo))

        if scoring_marks_to_undo > 0:
            is_target_open_for_scoring = any(
                opp != player and opp.state["hits"].get(target_hit, 0) < 3 for opp in players
            )
            if is_target_open_for_scoring:
                points_to_undo = self.CRICKET_TARGET_VALUES[target_hit] * scoring_marks_to_undo

                if self.name in ("Cricket", "Tactics"):
                    player.update_score_value(points_to_undo, subtract=True)
                else:  # Cut Throat
                    for opp in players:
                        if opp != player and opp.state["hits"].get(target_hit, 0) < 3:
                            opp.update_score_value(points_to_undo, subtract=True)

        # 5. Anzeige aktualisieren
        player.sb.update_display(player.state["hits"], player.score)

    def _get_target_and_marks(self, ring, segment):
        """
        Ermittelt das Ziel und die Anzahl der erzielten Marks für einen Wurf.

        Args:
            ring (str): Der getroffene Ring.
            segment (int/str): Das getroffene Segment.

        Returns:
            tuple: (target_hit, marks_scored) - Das getroffene Cricket-Ziel (str)
                   oder None und die Anzahl der Marks (int).
        """
        if ring == "Miss":
            return None, 0

        # Bullseye und Bull als "Bull" Target behandeln
        if ring == "Bullseye":  # Zählt als 2 Marks auf Bull
            return "Bull", 2
        if ring == "Bull":  # Zählt als 1 Mark auf Bull
            return "Bull", 1

        segment_str = str(segment)
        if segment_str in self.CRICKET_SEGMENTS_AS_STR:
            marks = 0
            if ring == "Single":
                marks = 1
            elif ring == "Double":
                marks = 2
            elif ring == "Triple":
                marks = 3
            return segment_str, marks

        return None, 0  # Kein Cricket/Tactics relevantes Segment getroffen

    def _handle_throw(self, player, ring, segment, players):
        """
        Verarbeitet einen einzelnen Wurf für einen Spieler.

        Dies ist die Kernmethode für die Cricket-Logik. Sie führt folgende Schritte aus:
        1.  Ermittelt, ob der Wurf ein gültiges Ziel getroffen hat und wie viele
            "Marks" er wert ist.
        2.  Aktualisiert die Statistik für die "Marks Per Round" (MPR).
        3.  Wenn der Wurf gültig ist, werden die Treffer (`player.hits`) aktualisiert.
        4.  Prüft, ob der Spieler bereits 3 Treffer auf dem Ziel hat. Wenn ja,
            werden Punkte vergeben, falls das Ziel bei den Gegnern noch offen ist.
        5.  Die Punktevergabe unterscheidet sich:
            -   "Cricket"/"Tactics": Punkte werden dem Spieler gutgeschrieben.
            -   "Cut Throat": Punkte werden den Gegnern als "Straf-"Punkte addiert.
        6.  Aktualisiert die Anzeige auf dem Scoreboard.
        7.  Prüft, ob der Spieler alle seine Ziele geschlossen hat UND die
            Punktebedingung für einen Sieg erfüllt ist.
        8.  Bei einem Sieg wird die MPR berechnet und an den HighscoreManager übergeben.

        Args:
            player (Player): Der Spieler, der den Wurf ausgeführt hat.
            ring (str): Der getroffene Ring.
            segment (int/str): Das getroffene Segment.

        Returns:
            tuple: (str, str) -
            str or None: Eine Gewinnnachricht, wenn das Spiel gewonnen wurde, ansonsten None.
        """
        return_msg = ("ok", None)
        target_hit, marks_scored = self._get_target_and_marks(ring, segment)

        if not target_hit:
            player.sb.update_score(player.score)  # Scoreboard aktualisieren (für Wurf-Historie)
        else:
            # Statistik für Marks-per-Round (MPR) aktualisieren
            player.stats["total_marks_scored"] += marks_scored
            # --- Treffer auf Cricket-Ziel verarbeiten (optimierte Logik) ---
            marks_before_throw = player.state["hits"].get(target_hit, 0)
            player.state["hits"][target_hit] += marks_scored

            # Berechne, wie viele der geworfenen Marks punktend waren
            # (d.h. auf ein bereits vom Spieler geschlossenes Ziel fielen)
            scoring_marks = max(0, (marks_before_throw + marks_scored) - 3) - max(
                0, marks_before_throw - 3
            )

            points_for_this_throw = 0
            if scoring_marks > 0:
                # Prüfen, ob das Ziel bei mindestens einem Gegner noch offen ist
                is_target_open_for_scoring = any(
                    opp != player and opp.state["hits"].get(target_hit, 0) < 3 for opp in players
                )
                if is_target_open_for_scoring:
                    points_for_this_throw = self.CRICKET_TARGET_VALUES[target_hit] * scoring_marks

                    if self.name in ("Cricket", "Tactics"):
                        player.update_score_value(points_for_this_throw, subtract=False)
                    else:  # Cut Throat
                        for opp in players:
                            if opp != player and opp.state["hits"].get(target_hit, 0) < 3:
                                opp.score += points_for_this_throw
                                opp.sb.set_score_value(opp.score)

            # Marks und Score aktualisieren
            player.sb.update_display(player.state["hits"], player.score)

            # --- Gewinnbedingung prüfen ---
            all_targets_closed_by_player = all(
                player.state["hits"].get(target, 0) >= 3 for target in self.targets
            )

            if all_targets_closed_by_player:
                # Ein Spieler gewinnt, wenn er alle Ziele geschlossen hat und
                # einen mindestens so guten Punktestand wie alle Gegner hat.
                has_won = True
                opponents = [p for p in players if p != player]

                for opp in opponents:
                    if self.name in ("Cricket", "Tactics"):
                        if player.score < opp.score:
                            has_won = False
                            break
                    elif self.name == "Cut Throat":
                        if player.score > opp.score:
                            has_won = False
                            break

                if has_won:
                    # Der Spieler, der den Wurf gemacht hat, der die Gewinnbedingung erfüllt, ist der alleinige Sieger.
                    self.game.end = True  # noqa
                    self.game.winner = player
                    return_msg = ("win", f"🏆 {player.name} gewinnt!")

        return return_msg
