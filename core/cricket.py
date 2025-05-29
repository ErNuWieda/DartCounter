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


    def get_targets(self):
        return self.targets

        
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
        Verarbeitet einen Wurf im Cricket-, Cut Throat, oder Tactics-Modus.
        Aktualisiert die Treffer des Spielers, berechnet Punkte und prüft auf Gewinnbedingungen.

        Args:
            player (Player): Der Spieler, der den Wurf ausgeführt hat.
            ring (str): Der getroffene Ring.
            segment (int/str): Das getroffene Segment.

        Returns:
            str or None: Eine Nachricht über den Spielausgang oder den Wurf,
                         oder None, wenn das Spiel weitergeht.
        """
        target_hit, marks_scored = self._get_target_and_marks (ring, segment)
        player.throws.append((ring, segment))
        if not target_hit or marks_scored == 0:
            player.sb.update_score(player.score) # Scoreboard aktualisieren (für Wurfanzeige)
            messagebox.showinfo("Fehlwurf!", text=f"{player.name} verfehlt oder Feld ist kein Ziel.")
            if len(player.throws) == 3:
                player.reset_turn()
                self.game.next_player()
            return 

        # --- Treffer auf Cricket-Ziel verarbeiten ---
        current_marks_on_target = player.hits.get(target_hit, 0)
        points_for_this_throw = 0
        for _ in range(marks_scored):
            if player.hits[target_hit] < 3:
                player.hits[target_hit] += 1
            else: # Ziel ist bereits vom Spieler geschlossen
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
                player.update_score_value(points_for_this_throw, subtract=False)
            else:
                for opp in players:
                    if opp != player and opp.hits.get(target_hit, 0) < 3:
                        opp.update_score_value(points_for_this_throw, subtract=False)

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
                return f"🏆 {player.name} gewinnt {self.name} in Runde {self.game.round} mit {total_darts} Darts!"

        # --- Zug beenden / Nächster Spieler ---
        if len(player.throws) == 3:
            player.reset_turn()
            self.game.next_player()
            return  
