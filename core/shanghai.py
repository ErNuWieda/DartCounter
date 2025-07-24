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
from .game_logic_base import GameLogicBase

TARGET_VALUES = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "11": 11, "12": 12, "13": 13, "14": 14, "15": 15, "16": 16, "17": 17, "18": 18, "19": 19, "20": 20}

SEGMENTS_AS_STR = [str(s) for s in range(1, 20)] # "1" bis "20"

class Shanghai(GameLogicBase):
	def __init__(self, game):
		super().__init__(game)
		self.targets = []

	def initialize_player_state(self, player):
		"""
		Setzt den Anfangs-Score auf 0, initialisiert die Treffer-Map und das erste Ziel.
		"""
		player.score = 0
		if self.get_targets(): # Sicherstellen, dass self.targets initialisiert ist
			player.next_target = self.targets[0]
			for target in self.targets:
				player.hits[target] = 0

	def get_targets(self):
		for i in range(self.game.rounds):
			self.targets.append(str(i+1)) 
		return self.targets

	def _handle_throw_undo(self, player, ring, segment, players):
		"""Macht einen Wurf im Shanghai-Modus rückgängig, indem Punkte und Treffer korrigiert werden."""
		# Der rückgängig gemachte Wurf war nur dann relevant, wenn er auf das Ziel der Runde ging.
		if str(segment) == str(self.game.round):
			# 1. Punkte des Wurfs ermitteln und vom Score abziehen
			score_to_undo = self.game.get_score(ring, segment)
			player.update_score_value(score_to_undo, subtract=True)

			# 2. Trefferzähler reduzieren
			# Da jeder gültige Treffer die 'hits' um 1 erhöht, reduzieren wir sie auch um 1.
			if player.hits.get(str(self.game.round), 0) > 0:
				player.hits[str(self.game.round)] -= 1

		# Das nächste Ziel ist immer die aktuelle Runde (für die UI-Anzeige)
		player.next_target = str(self.game.round)

		# Anzeige aktualisieren, um alle Änderungen zu reflektieren.
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
		# --- Gewinnbedingung prüfen (Ende der Runden) ---
		# Diese Prüfung muss VOR der Wurfverarbeitung stattfinden.
		if self.game.round > self.game.rounds:
			self.game.end = True
			winner = max(players, key=lambda p: p.score)
			return f"🏆 Spiel beendet!\n{winner.name} gewinnt mit {winner.score} Punkten!"

		player.throws.append((ring, segment))

		# Prüfen, ob der Wurf auf das Ziel der aktuellen Runde ging
		if str(segment) == str(self.game.round):
			# Trefferzähler erhöhen
			player.hits[str(self.game.round)] = player.hits.get(str(self.game.round), 0) + 1

			# Punkte berechnen und Score aktualisieren
			points_for_this_throw = self.game.get_score(ring, segment)
			player.update_score_value(points_for_this_throw, subtract=False)
			# Anzeige aktualisieren, um Treffer-Checkboxen zu zeigen
			player.sb.update_display(player.hits, player.score)
		else:
			# Ungültiger Wurf, nur Wurfhistorie aktualisieren
			player.sb.update_score(player.score)
			return None

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
		# --- Weiter / Nächster Spieler ---
		if len(player.throws) == 3:
			player.next_target = str(self.game.round + 1)

		    # Turn ends
			return None
        
		return None # Throw processed, turn continues
