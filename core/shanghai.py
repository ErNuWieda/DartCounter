"""
Dieses Modul definiert die Hauptlogik für verschiedene Dartspiele.
Es enthält die Game-Klasse, die den Spielablauf, die Spieler,
Punktestände und Regeln verwaltet.
"""
import tkinter as tk 
from tkinter import ttk, messagebox
from . import player 
from .player import Player
from . import scoreboard
from .scoreboard import ScoreBoard 

TARGET_VALUES = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "11": 11, "12": 12, "13": 13, "14": 14, "15": 15, "16": 16, "17": 17, "18": 18, "19": 19, "20": 20}

SEGMENTS_AS_STR = [str(s) for s in range(1, 20)] # "1" bis "20"

class Shanghai:
	def __init__(self, game):
		self.game = game
		self.rounds = self.game.rounds
		self.targets = []

	def get_targets(self):
		for i in range(self.rounds):
			self.targets.append(str(i+1)) 
		return self.targets

	def _handle_throw_undo(self, player, ring, segment, players):
		# 1. Punkte des Wurfs ermitteln.
		score = self.game.get_score(ring, segment)

		if str(segment) == str(self.game.round): # Hit the correct number segment
			valid_target = True
			player.hits[str(self.game.round)] -= 1
			if ring == "Single":
				points_for_this_throw = int(segment) # segment is str from dartboard sometimes
			elif ring == "Double":
				points_for_this_throw = int(segment) * 2
			elif ring == "Triple":
				points_for_this_throw = int(segment) * 3
		
        # Punkte und Anzeige aktualisieren
		if valid_target:
			player.update_score_value(points_for_this_throw, subtract=True)

		if len(player.throws) == 2:
			player.next_target = self.game.round

		# 3. Anzeige aktualisieren, um alle Änderungen zu reflektieren.
		player.sb.update_display(player.hits, player.score)
		
	def _handle_throw(self, player, ring, segment, players):
		"""
		Verarbeitet einen Wurf im "Shanghai" Modus.
		Prüft, ob das korrekte Ziel getroffen wurde, aktualisiert den Fortschritt
		und prüft auf Gewinnbedingungen.

		Args:
		    player (Player): Der Spieler, der den Wurf ausgeführt hat.
		    ring (str): Der getroffene Ring.
		    segment (int/str): Das getroffene Segment.

		Returns:
		    str or None: Eine Nachricht über den Spielausgang oder den Wurf, oder None.
		"""
		player.throws.append((ring, segment))       
		points_for_this_throw = 0
		valid_target = False # Distinguish from progress hit

		if str(segment) == str(self.game.round): # Hit the correct number segment
			valid_target = True
			player.hits[str(self.game.round)] += 1
			if ring == "Single":
				points_for_this_throw = int(segment) # segment is str from dartboard sometimes
			elif ring == "Double":
				points_for_this_throw = int(segment) * 2
			elif ring == "Triple":
				points_for_this_throw = int(segment) * 3
		
		if not valid_target:
			player.sb.update_score(player.score) # Update for throw history
			return None # End processing for this throw

        # Punkte und Anzeige aktualisieren
		player.update_score_value(points_for_this_throw, subtract=False)
		player.sb.update_display(player.hits, player.score) # Checkboxen im Scoreboard aktualisieren

		# --- Gewinnbedingung prüfen ---
        # 1. Shanghai Finish (S, D, T des Zielfelds der Runde)
		target_segment_for_shanghai = str(self.game.round)

		rings_hit_on_target = set()
		for r, s_val in player.throws: # Check current turn's throws
			if str(s_val) == target_segment_for_shanghai:
				if r in ("Single", "Double", "Triple"):
					rings_hit_on_target.add(r)
		
		# --- Gewinnbedingungen prüfen ---
		if rings_hit_on_target == {"Single", "Double", "Triple"}:
			self.game.end = True
			return f"🏆 SHANGHAI ON {target_segment_for_shanghai}!\n{player.name} gewinnt in Runde {self.game.round}!"

		if self.game.round > self.rounds:
			self.game.end = True
			winner = max(players, key=lambda p: p.score)
			return f"🏆 Spiel beendet!\n{winner.name} gewinnt mit {winner.score} Punkten.!"

		# --- Weiter / Nächster Spieler ---
		if len(player.throws) == 3:
			player.next_target = self.game.round + 1
			player.sb.update_display(player.hits, player.score) # Checkboxen im Scoreboard aktualisieren

		    # Turn ends
			return None
        
		return None # Throw processed, turn continues
