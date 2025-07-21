"""
Dieses Modul definiert die Hauptlogik für Cricket und Cut Throat.
Es enthält die Cricket-Klasse, die den Spielablauf und Regeln der Cricket-Varianten verwaltet.
"""
import tkinter as tk 
from tkinter import ttk, messagebox
from . import player 
from .player import Player
from . import scoreboard
from .scoreboard import ScoreBoard 

# Cricket, Cut Throat 
CRICKET_TARGET_VALUES = {"20": 20, "19": 19, "18": 18, "17": 17, "16": 16, "15": 15, "Bull": 25}

CRICKET_SEGMENTS_AS_STR = [str(s) for s in range(15, 21)] # "15" bis "20"

# Tactics Ziele
TACTICS_TARGET_VALUES = {"20": 20, "19": 19, "18": 18, "17": 17, "16": 16, "15": 15, "14": 14, "13": 13, "12": 12, "11": 11, "10": 10, "Bull": 25}

TACTICS_SEGMENTS_AS_STR = [str(s) for s in range(10, 21)] # "10" bis "20"

class Cricket:
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
        self.game = game
        self.name = game.name
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
        player.score = 0
        if self.targets:
            for target in self.targets:
                player.hits[target] = 0

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
        # --- Treffer auf Cricket-Ziel verarbeiten ---
        current_marks_on_target = player.hits.get(target_hit, 0)
        points_for_this_throw = 0
        for _ in range(marks_scored):
            if player.hits[target_hit] > 0:
                player.hits[target_hit] -= 1
            can_score_points = False
            if current_marks_on_target >= 3: # Ziel ist bereits vom Spieler geschlossen
                # Prüfen, ob das Ziel für Punktgewinn offen ist (nicht alle Gegner haben es geschlossen)
                can_score_points = False
                for opp in players:
                    if opp != player and opp.hits.get(target_hit, 0) < 3:
                        can_score_points = True
                        break
                if can_score_points:
                    points_for_this_throw += self.CRICKET_TARGET_VALUES[target_hit]

        if points_for_this_throw > 0:
            if self.name in ("Cricket", "Tactics"):
                if can_score_points: # and player.score >= points_for_this_throw:
                    if player.score < points_for_this_throw:
                        points_for_this_throw = player.score
                    player.update_score_value(points_for_this_throw, subtract=True)
            else:
                for opp in players:
                    if opp != player and opp.hits.get(target_hit, 0) < 3:
                        if opp.score > 0:
                            opp.score -= points_for_this_throw
                            opp.sb.set_score_value(opp.score)
                        break
 
        player.sb.update_display(player.hits, player.score) # Scoreboard aktualisieren (für Wurfanzeige)


    def _get_target_and_marks (self, ring, segment):
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
        if ring == "Bullseye": # Zählt als 2 Marks auf Bull
            return "Bull", 2
        if ring == "Bull": # Zählt als 1 Mark auf Bull
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
        
        return None, 0 # Kein Cricket/Tactics relevantes Segment getroffen


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
            str or None: Eine Gewinnnachricht, wenn das Spiel gewonnen wurde, ansonsten None.
        """
        target_hit, marks_scored = self._get_target_and_marks (ring, segment)
        player.throws.append((ring, segment))

        # Statistik für Marks-per-Round (MPR) aktualisieren
        if target_hit and marks_scored > 0:
            player.stats['total_marks_scored'] += marks_scored

        if not target_hit or marks_scored == 0:
            player.sb.update_score(player.score) # Scoreboard aktualisieren (für Wurfanzeige)
            if len(player.throws) == 3:
                # Turn ends
                return None
            return None # Throw processed, continue turn

        # --- Treffer auf Cricket-Ziel verarbeiten ---
        current_marks_on_target = player.hits.get(target_hit, 0)
        points_for_this_throw = 0
        for _ in range(marks_scored):
            player.hits[target_hit] += 1
            if current_marks_on_target >= 3:
                # Ziel ist bereits vom Spieler geschlossen
                # Prüfen, ob das Ziel für Punktgewinn offen ist (nicht alle Gegner haben es geschlossen)
                can_score_points = False
                for opp in players:
                    if opp != player and opp.hits.get(target_hit, 0) < 3:
                        can_score_points = True
                        break
                if can_score_points:
                    points_for_this_throw += self.CRICKET_TARGET_VALUES[target_hit]
            current_marks_on_target += 1

        if points_for_this_throw > 0:
            if self.name in ("Cricket", "Tactics"):
                player.update_score_value(points_for_this_throw, subtract=False)
            else:
                for opp in players:
                    if opp != player and opp.hits.get(target_hit, 0) < 3:
                        opp.score += points_for_this_throw
                        opp.sb.set_score_value(opp.score)
                        
        # Marks und Score aktualisieren
        player.sb.update_display(player.hits, player.score) 

        # --- Gewinnbedingung prüfen ---
        all_targets_closed_by_player = True
        for target in player.targets:
            if player.hits.get(target, 0) < 3:
                all_targets_closed_by_player = False
                break
        
        if all_targets_closed_by_player:
            player_has_best_score = True
            for opp in players:
                if opp != player:
                    if self.name in ("Cricket", "Tactics") and opp.score > player.score:
                        player_has_best_score = False
                        break
                    elif opp.score < player.score:
                        player_has_best_score = False
                        break                        

            if player_has_best_score:
                self.game.end = True
                total_darts = (self.game.round - 1) * 3 + len(player.throws)

                # Highscore für Cricket-Modi hinzufügen (MPR)
                if self.game.highscore_manager:
                    total_darts_for_mpr = (self.game.round - 1) * 3 + len(player.throws)
                    if total_darts_for_mpr > 0:
                        mpr = (player.stats['total_marks_scored'] / total_darts_for_mpr) * 3
                    else:
                        mpr = 0.0
                    self.game.highscore_manager.add_score(self.name, player.name, mpr)

                return f"🏆 {player.name} gewinnt {self.name} in Runde {self.game.round} mit {total_darts} Darts!"

        # --- Weiter / Nächster Spieler ---
        if len(player.throws) == 3:
            # Turn ends
            return None
        return None # Added to ensure a return path if not 3 throws and no win
