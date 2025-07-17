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

# Micky Mouse Targets, Spielreihenfolge
TARGET_VALUES = {"20": 20, "19": 19, "18": 18, "17": 17, "16": 16, "15": 15, "14": 14, "13": 13, "12": 12, "Bull": 25}

SEGMENTS_AS_STR = [str(s) for s in range(12, 21)] # "12" bis "20"

class Micky:
	def __init__(self, game):
		self.game = game
		self.name = game.name
		self.targets = [k for k in TARGET_VALUES.keys()]

	def get_targets(self):
		return self.targets

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

		if ring == "Bullseye": # Zählt als 2 Marks auf Bull
			return "Bull", 2
		if ring == "Bull": # Zählt als 1 Mark auf Bull
			return "Bull", 1

		segment_str = str(segment)
		if segment_str in SEGMENTS_AS_STR:
			marks = 0
			if ring == "Single":
				marks = 1
			elif ring == "Double":
				marks = 2
			elif ring == "Triple":
				marks = 3
			return segment_str, marks

		return None, 0 # Kein Spiel-relevantes Segment getroffen
    
	def _handle_throw_undo(self, player, ring, segment, players):
		target_hit, marks_scored = self._get_target_and_marks(ring, segment)
		# --- Treffer auf Cricket-Ziel verarbeiten ---
		for _ in range(marks_scored):
			if player.hits[target_hit] > 0:
				player.hits[target_hit] -= 1

		# Nächstes Ziel zurücksetzen
		all_targets_closed = True
		for target in player.targets:
		    hits = player.hits.get(target, 0)
		    if hits < 3:
		        all_targets_closed = False
		        player.next_target = target
		        break

		player.sb.update_display(player.hits, player.score) # Scoreboard aktualisieren (für Wurfanzeige)

	def _handle_throw(self, player, ring, segment, players):
		"""
		Verarbeitet einen Wurf im Micky Mouse-Modus.
		Aktualisiert die Treffer des Spielers, hier werden keine Punkte berechnet. Prüft auf Gewinnbedingungen.

		Args:
		    player (Player): Der Spieler, der den Wurf ausgeführt hat.
		    ring (str): Der getroffene Ring.
		    segment (int/str): Das getroffene Segment.

		Returns:
		    str or None: Eine Nachricht über den Spielausgang oder den Wurf,
		                 oder None, wenn das Spiel weitergeht.
		"""
		# hier kann die Methodik von Cricket verwendet werden...
		target_hit, marks_scored = self._get_target_and_marks (ring, segment)
		player.throws.append((ring, segment))

		if not target_hit or marks_scored == 0 or target_hit != player.next_target:
			player.sb.update_score(player.score) # Scoreboard aktualisieren (für Wurf-Historie)            
			msg_base = f"{player.name} muss {player.next_target} noch {3 - player.hits.get(player.next_target, 0)}x treffen!"
			remaining_darts = 3 - len(player.throws)
			if remaining_darts > 0:
				messagebox.showerror("Ungültiger Wurf", msg_base + f"\n{remaining_darts} verbleibende Darts.")
			else:            
				messagebox.showerror("Ungültiger Wurf", msg_base + "\nLetzter Dart dieser Aufnahme.\nBitte 'Rückgängig' oder 'Zug beenden' klicken.")
			return None # End processing for this throw

		# --- Treffer auf Mickey Mouse-Ziel verarbeiten ---
		current_marks_on_target = player.hits.get(target_hit, 0)
		points_for_this_throw = 0
		for _ in range(marks_scored):
		    player.hits[target_hit] += 1

		# --- Gewinnbedingung prüfen ---
		all_targets_closed_by_player = True
		for target in player.targets:
		    target_hits = player.hits.get(target, 0)
		    if target_hits < 3:
		        if target_hits == 0:
		            player.next_target = target
		        all_targets_closed_by_player = False
		        break

		player.sb.update_display(player.hits, player.score) # Micky Mouse-Marks aktualisieren
		
		if all_targets_closed_by_player:
		    self.game.end = True
		    total_darts = (self.game.round - 1) * 3 + len(player.throws)
		    return f"🏆 {player.name} gewinnt {self.game.name} in Runde {self.game.round} mit {total_darts} Darts!"

		# --- Zug beenden / Nächster Spieler ---
		if len(player.throws) == 3:
		    # Turn ends
		    return None
		return None # Added for consistency
